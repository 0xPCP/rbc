from functools import wraps
from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Club, Ride, RideSignup, User, ClubMembership
from ..forms import RideForm, ClubForm, ClubSettingsForm
from ..recurrence import generate_instances, delete_future_instances
from ..geocoding import geocode_zip

admin_bp = Blueprint('admin', __name__)


def _get_club_or_404(slug):
    return Club.query.filter_by(slug=slug, is_active=True).first_or_404()


def club_admin_required(f):
    """Decorator: user must be club admin (or global superadmin) for the club in the URL."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        slug = kwargs.get('slug')
        if slug:
            club = _get_club_or_404(slug)
            if not current_user.is_club_admin(club):
                abort(403)
        elif not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return login_required(decorated)


def superadmin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return login_required(decorated)


# ── Global superadmin ─────────────────────────────────────────────────────────

@admin_bp.route('/')
@superadmin_required
def dashboard():
    today = date.today()
    stats = {
        'total_clubs':   Club.query.count(),
        'total_members': User.query.count(),
        'upcoming_rides': Ride.query.filter(Ride.date >= today).count(),
        'total_signups':  RideSignup.query.count(),
    }
    clubs = Club.query.order_by(Club.name.asc()).all()
    return render_template('admin/dashboard.html', stats=stats, clubs=clubs)


@admin_bp.route('/clubs/new', methods=['GET', 'POST'])
@superadmin_required
def club_new():
    form = ClubForm()
    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        if Club.query.filter_by(slug=slug).first():
            flash('That slug is already taken.', 'danger')
            return render_template('admin/club_form.html', form=form, title='New Club', club=None)

        club = Club(
            slug=slug,
            name=form.name.data,
            description=form.description.data or None,
            city=form.city.data or None,
            state=form.state.data or None,
            zip_code=form.zip_code.data or None,
            address=form.address.data or None,
            website=form.website.data or None,
            contact_email=form.contact_email.data or None,
            logo_url=form.logo_url.data or None,
            is_active=form.is_active.data,
        )
        if club.zip_code:
            coords = geocode_zip(club.zip_code)
            if coords:
                club.lat, club.lng = coords
        db.session.add(club)
        db.session.commit()
        flash(f'Club "{club.name}" created.', 'success')
        return redirect(url_for('admin.club_dashboard', slug=club.slug))

    return render_template('admin/club_form.html', form=form, title='New Club', club=None)


# ── Club admin ────────────────────────────────────────────────────────────────

@admin_bp.route('/clubs/<slug>/')
@club_admin_required
def club_dashboard(slug):
    club = _get_club_or_404(slug)
    today = date.today()
    upcoming = (Ride.query.filter_by(club_id=club.id)
                .filter(Ride.date >= today)
                .order_by(Ride.date.asc()).limit(5).all())
    stats = {
        'members':        ClubMembership.query.filter_by(club_id=club.id).count(),
        'upcoming_rides': Ride.query.filter_by(club_id=club.id).filter(Ride.date >= today).count(),
        'total_rides':    Ride.query.filter_by(club_id=club.id).count(),
        'total_signups':  (RideSignup.query
                           .join(Ride, RideSignup.ride_id == Ride.id)
                           .filter(Ride.club_id == club.id).count()),
    }
    return render_template('admin/club_dashboard.html', club=club,
                           upcoming=upcoming, stats=stats)


@admin_bp.route('/clubs/<slug>/settings', methods=['GET', 'POST'])
@club_admin_required
def club_settings(slug):
    club = _get_club_or_404(slug)
    form = ClubSettingsForm(obj=club)
    if form.validate_on_submit():
        club.name         = form.name.data
        club.description  = form.description.data or None
        club.city         = form.city.data or None
        club.state        = form.state.data or None
        club.address      = form.address.data or None
        club.website      = form.website.data or None
        club.contact_email = form.contact_email.data or None
        club.logo_url     = form.logo_url.data or None

        new_zip = (form.zip_code.data or '').strip()
        if new_zip != (club.zip_code or ''):
            club.zip_code = new_zip or None
            club.lat = None
            club.lng = None
            if new_zip:
                coords = geocode_zip(new_zip)
                if coords:
                    club.lat, club.lng = coords
                else:
                    flash('Zip code saved but could not be geocoded.', 'warning')

        db.session.commit()
        flash('Club settings updated.', 'success')
        return redirect(url_for('admin.club_settings', slug=slug))

    return render_template('admin/club_settings.html', form=form, club=club)


@admin_bp.route('/clubs/<slug>/rides')
@club_admin_required
def club_rides(slug):
    club = _get_club_or_404(slug)
    all_rides = (Ride.query.filter_by(club_id=club.id)
                 .order_by(Ride.date.desc()).all())
    return render_template('admin/club_rides.html', club=club, rides=all_rides)


@admin_bp.route('/clubs/<slug>/rides/new', methods=['GET', 'POST'])
@club_admin_required
def ride_new(slug):
    club = _get_club_or_404(slug)
    form = RideForm()
    if form.validate_on_submit():
        ride = Ride(
            club_id=club.id,
            title=form.title.data,
            date=form.date.data,
            time=form.time.data,
            meeting_location=form.meeting_location.data,
            distance_miles=form.distance_miles.data,
            elevation_feet=form.elevation_feet.data,
            pace_category=form.pace_category.data,
            ride_leader=form.ride_leader.data or None,
            route_url=form.route_url.data or None,
            video_url=form.video_url.data or None,
            description=form.description.data or None,
            is_cancelled=form.is_cancelled.data,
            is_recurring=form.is_recurring.data,
            created_by=current_user.id,
        )
        db.session.add(ride)
        db.session.commit()
        if ride.is_recurring:
            count = len(generate_instances(ride))
            flash(f'Ride created with {count} recurring instances.', 'success')
        else:
            flash('Ride created.', 'success')
        return redirect(url_for('admin.club_rides', slug=slug))
    return render_template('admin/ride_form.html', form=form, club=club, title='New Ride')


@admin_bp.route('/clubs/<slug>/rides/<int:ride_id>/edit', methods=['GET', 'POST'])
@club_admin_required
def ride_edit(slug, ride_id):
    club = _get_club_or_404(slug)
    ride = Ride.query.filter_by(id=ride_id, club_id=club.id).first_or_404()
    form = RideForm(obj=ride)
    if form.validate_on_submit():
        was_recurring = ride.is_recurring
        ride.title          = form.title.data
        ride.date           = form.date.data
        ride.time           = form.time.data
        ride.meeting_location = form.meeting_location.data
        ride.distance_miles = form.distance_miles.data
        ride.elevation_feet = form.elevation_feet.data
        ride.pace_category  = form.pace_category.data
        ride.ride_leader    = form.ride_leader.data or None
        ride.route_url      = form.route_url.data or None
        ride.video_url      = form.video_url.data or None
        ride.description    = form.description.data or None
        ride.is_cancelled   = form.is_cancelled.data
        ride.is_recurring   = form.is_recurring.data
        db.session.commit()
        # Regenerate instances if this is (or was) a recurring template
        if ride.is_recurring or was_recurring:
            delete_future_instances(ride)
            if ride.is_recurring:
                count = len(generate_instances(ride))
                flash(f'Ride updated — {count} upcoming instances regenerated.', 'success')
            else:
                flash('Ride updated — recurrence removed, future instances deleted.', 'success')
        else:
            flash('Ride updated.', 'success')
        return redirect(url_for('admin.club_rides', slug=slug))
    return render_template('admin/ride_form.html', form=form, club=club,
                           title='Edit Ride', ride=ride)


@admin_bp.route('/clubs/<slug>/rides/<int:ride_id>/delete', methods=['POST'])
@club_admin_required
def ride_delete(slug, ride_id):
    club = _get_club_or_404(slug)
    ride = Ride.query.filter_by(id=ride_id, club_id=club.id).first_or_404()
    db.session.delete(ride)
    db.session.commit()
    flash('Ride deleted.', 'info')
    return redirect(url_for('admin.club_rides', slug=slug))
