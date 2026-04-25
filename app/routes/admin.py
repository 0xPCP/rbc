from functools import wraps
from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Club, Ride, RideSignup, User, ClubMembership, ClubAdmin, ClubPost
from ..forms import RideForm, ClubForm, ClubSettingsForm, ClubPostForm
from ..recurrence import generate_instances, delete_future_instances
from ..geocoding import geocode_zip
from ..email import (send_cancellation_emails, send_new_ride_notification,
                     send_membership_approved, send_membership_rejected)

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


def club_ride_admin_required(f):
    """Decorator: user must be able to manage rides (full admin OR ride_manager)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        slug = kwargs.get('slug')
        if slug:
            club = _get_club_or_404(slug)
            if not current_user.can_manage_rides(club):
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
@club_ride_admin_required
def club_dashboard(slug):
    club = _get_club_or_404(slug)
    today = date.today()
    upcoming = (Ride.query.filter_by(club_id=club.id)
                .filter(Ride.date >= today)
                .order_by(Ride.date.asc()).limit(5).all())
    stats = {
        'members':        ClubMembership.query.filter_by(club_id=club.id, status='active').count(),
        'pending':        ClubMembership.query.filter_by(club_id=club.id, status='pending').count(),
        'upcoming_rides': Ride.query.filter_by(club_id=club.id).filter(Ride.date >= today).count(),
        'total_rides':    Ride.query.filter_by(club_id=club.id).count(),
        'total_signups':  (RideSignup.query
                           .join(Ride, RideSignup.ride_id == Ride.id)
                           .filter(Ride.club_id == club.id).count()),
    }
    is_full_admin = current_user.is_club_admin(club)
    return render_template('admin/club_dashboard.html', club=club,
                           upcoming=upcoming, stats=stats,
                           is_full_admin=is_full_admin)


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

        club.theme_primary = (form.theme_primary.data or '').strip().lower() or None
        club.theme_accent  = (form.theme_accent.data or '').strip().lower() or None
        club.banner_url    = form.banner_url.data or None

        raw_strava = (form.strava_club_id.data or '').strip()
        club.strava_club_id = int(raw_strava) if raw_strava.isdigit() else None

        club.auto_cancel_enabled = form.auto_cancel_enabled.data
        club.cancel_rain_prob    = form.cancel_rain_prob.data or 80
        club.cancel_wind_mph     = form.cancel_wind_mph.data or 35
        club.cancel_temp_min_f   = form.cancel_temp_min_f.data if form.cancel_temp_min_f.data is not None else 28
        club.cancel_temp_max_f   = form.cancel_temp_max_f.data if form.cancel_temp_max_f.data is not None else 100

        club.is_private         = form.is_private.data
        club.require_membership = form.require_membership.data
        club.join_approval      = form.join_approval.data if form.join_approval.data in ('auto', 'manual') else 'auto'

        db.session.commit()
        flash('Club settings updated.', 'success')
        return redirect(url_for('admin.club_settings', slug=slug))

    return render_template('admin/club_settings.html', form=form, club=club)


@admin_bp.route('/clubs/<slug>/members/export')
@club_admin_required
def club_members_export(slug):
    """Download active member list as CSV."""
    import csv
    import io
    from flask import Response
    club = _get_club_or_404(slug)
    memberships = (ClubMembership.query.filter_by(club_id=club.id)
                   .join(ClubMembership.user).order_by(User.username).all())
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Username', 'Email', 'Status', 'Joined',
                     'Emergency Contact', 'Emergency Phone'])
    for m in memberships:
        writer.writerow([
            m.user.username,
            m.user.email,
            m.status,
            m.joined_at.strftime('%Y-%m-%d') if m.joined_at else '',
            m.user.emergency_contact_name or '',
            m.user.emergency_contact_phone or '',
        ])
    output.seek(0)
    filename = f'{club.slug}_members.csv'
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@admin_bp.route('/clubs/<slug>/rides')
@club_ride_admin_required
def club_rides(slug):
    club = _get_club_or_404(slug)
    all_rides = (Ride.query.filter_by(club_id=club.id)
                 .order_by(Ride.date.desc()).all())
    return render_template('admin/club_rides.html', club=club, rides=all_rides)


@admin_bp.route('/clubs/<slug>/rides/<int:ride_id>/roster')
@club_ride_admin_required
def ride_roster(slug, ride_id):
    club = _get_club_or_404(slug)
    ride = Ride.query.filter_by(id=ride_id, club_id=club.id).first_or_404()
    active = [s for s in ride.signups if not s.is_waitlist]
    waitlist = [s for s in ride.signups if s.is_waitlist]
    return render_template('admin/ride_roster.html', club=club, ride=ride,
                           active=active, waitlist=waitlist)


def _resolve_leader(club):
    """Read leader_id from form; return (leader_id, ride_leader_text)."""
    lid = request.form.get('leader_id', type=int)
    if lid:
        member = ClubMembership.query.filter_by(user_id=lid, club_id=club.id, status='active').first()
        if member:
            return lid, member.user.username
    return None, request.form.get('ride_leader_text', '').strip() or None


@admin_bp.route('/clubs/<slug>/rides/new', methods=['GET', 'POST'])
@club_ride_admin_required
def ride_new(slug):
    club = _get_club_or_404(slug)
    form = RideForm()
    members = (ClubMembership.query.filter_by(club_id=club.id, status='active')
               .join(ClubMembership.user).order_by(User.username).all())
    if form.validate_on_submit():
        leader_id, ride_leader = _resolve_leader(club)
        ride = Ride(
            club_id=club.id,
            title=form.title.data,
            date=form.date.data,
            time=form.time.data,
            meeting_location=form.meeting_location.data,
            distance_miles=form.distance_miles.data,
            elevation_feet=form.elevation_feet.data,
            pace_category=form.pace_category.data,
            ride_type=form.ride_type.data or None,
            max_riders=form.max_riders.data or None,
            leader_id=leader_id,
            ride_leader=ride_leader,
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
            send_new_ride_notification(ride)
        return redirect(url_for('admin.club_rides', slug=slug))
    return render_template('admin/ride_form.html', form=form, club=club,
                           members=members, title='New Ride')


@admin_bp.route('/clubs/<slug>/rides/<int:ride_id>/edit', methods=['GET', 'POST'])
@club_ride_admin_required
def ride_edit(slug, ride_id):
    club = _get_club_or_404(slug)
    ride = Ride.query.filter_by(id=ride_id, club_id=club.id).first_or_404()
    form = RideForm(obj=ride)
    members = (ClubMembership.query.filter_by(club_id=club.id, status='active')
               .join(ClubMembership.user).order_by(User.username).all())
    if form.validate_on_submit():
        was_recurring  = ride.is_recurring
        was_cancelled  = ride.is_cancelled
        leader_id, ride_leader = _resolve_leader(club)
        ride.title          = form.title.data
        ride.date           = form.date.data
        ride.time           = form.time.data
        ride.meeting_location = form.meeting_location.data
        ride.distance_miles = form.distance_miles.data
        ride.elevation_feet = form.elevation_feet.data
        ride.pace_category  = form.pace_category.data
        ride.ride_type      = form.ride_type.data or None
        ride.max_riders     = form.max_riders.data or None
        ride.leader_id      = leader_id
        ride.ride_leader    = ride_leader
        ride.route_url      = form.route_url.data or None
        ride.video_url      = form.video_url.data or None
        ride.description    = form.description.data or None
        ride.is_cancelled   = form.is_cancelled.data
        ride.is_recurring   = form.is_recurring.data
        db.session.commit()
        if not was_cancelled and ride.is_cancelled:
            send_cancellation_emails(ride)
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
                           members=members, title='Edit Ride', ride=ride)


@admin_bp.route('/clubs/<slug>/rides/<int:ride_id>/delete', methods=['POST'])
@club_ride_admin_required
def ride_delete(slug, ride_id):
    club = _get_club_or_404(slug)
    ride = Ride.query.filter_by(id=ride_id, club_id=club.id).first_or_404()
    db.session.delete(ride)
    db.session.commit()
    flash('Ride deleted.', 'info')
    return redirect(url_for('admin.club_rides', slug=slug))


# ── Club team (admin role) management ─────────────────────────────────────────

@admin_bp.route('/clubs/<slug>/team')
@club_admin_required
def club_team(slug):
    club = _get_club_or_404(slug)
    admins = (ClubAdmin.query.filter_by(club_id=club.id)
              .join(User, ClubAdmin.user_id == User.id)
              .add_entity(User).all())
    members = (ClubMembership.query.filter_by(club_id=club.id, status='active')
               .join(User, ClubMembership.user_id == User.id)
               .add_entity(User).all())
    pending = (ClubMembership.query.filter_by(club_id=club.id, status='pending')
               .join(User, ClubMembership.user_id == User.id)
               .add_entity(User).all())
    return render_template('admin/club_team.html', club=club,
                           admins=admins, members=members, pending=pending)


@admin_bp.route('/clubs/<slug>/team/add', methods=['POST'])
@club_admin_required
def club_team_add(slug):
    club = _get_club_or_404(slug)
    identifier = request.form.get('identifier', '').strip()
    role = request.form.get('role', 'admin')
    if role not in ('admin', 'ride_manager'):
        role = 'admin'

    user = (User.query.filter(
        (User.email == identifier) | (User.username == identifier)
    ).first())
    if not user:
        flash(f'No user found with email or username "{identifier}".', 'danger')
        return redirect(url_for('admin.club_team', slug=slug))

    existing = ClubAdmin.query.filter_by(user_id=user.id, club_id=club.id).first()
    if existing:
        existing.role = role
        db.session.commit()
        flash(f'{user.username} role updated to {role}.', 'success')
    else:
        db.session.add(ClubAdmin(user_id=user.id, club_id=club.id, role=role))
        db.session.commit()
        flash(f'{user.username} added as {role}.', 'success')

    return redirect(url_for('admin.club_team', slug=slug))


@admin_bp.route('/clubs/<slug>/team/<int:admin_id>/remove', methods=['POST'])
@club_admin_required
def club_team_remove(slug, admin_id):
    club = _get_club_or_404(slug)
    row = ClubAdmin.query.filter_by(id=admin_id, club_id=club.id).first_or_404()

    # Prevent removing self if you're the only full admin
    full_admins = ClubAdmin.query.filter_by(club_id=club.id, role='admin').count()
    if row.user_id == current_user.id and full_admins <= 1:
        flash('Cannot remove yourself — you are the only club admin.', 'danger')
        return redirect(url_for('admin.club_team', slug=slug))

    username = row.user.username
    db.session.delete(row)
    db.session.commit()
    flash(f'{username} removed from club team.', 'info')
    return redirect(url_for('admin.club_team', slug=slug))


@admin_bp.route('/clubs/<slug>/members/add', methods=['POST'])
@club_admin_required
def club_member_add(slug):
    club = _get_club_or_404(slug)
    identifier = request.form.get('identifier', '').strip()
    user = User.query.filter(
        (User.email == identifier) | (User.username == identifier)
    ).first()
    if not user:
        flash(f'No user found with email or username "{identifier}".', 'danger')
        return redirect(url_for('admin.club_team', slug=slug))

    existing = ClubMembership.query.filter_by(user_id=user.id, club_id=club.id).first()
    if existing:
        if existing.status == 'active':
            flash(f'{user.username} is already a member.', 'info')
        else:
            existing.status = 'active'
            db.session.commit()
            flash(f'{user.username} approved and added as a member.', 'success')
    else:
        db.session.add(ClubMembership(user_id=user.id, club_id=club.id, status='active'))
        db.session.commit()
        flash(f'{user.username} added as a member.', 'success')

    return redirect(url_for('admin.club_team', slug=slug))


@admin_bp.route('/clubs/<slug>/members/<int:uid>/remove', methods=['POST'])
@club_admin_required
def club_member_remove(slug, uid):
    club = _get_club_or_404(slug)
    row = ClubMembership.query.filter_by(user_id=uid, club_id=club.id).first_or_404()
    username = row.user.username
    db.session.delete(row)
    db.session.commit()
    flash(f'{username} removed from club.', 'info')
    return redirect(url_for('admin.club_team', slug=slug))


@admin_bp.route('/clubs/<slug>/members/<int:uid>/approve', methods=['POST'])
@club_admin_required
def club_member_approve(slug, uid):
    club = _get_club_or_404(slug)
    row = ClubMembership.query.filter_by(user_id=uid, club_id=club.id, status='pending').first_or_404()
    row.status = 'active'
    db.session.commit()
    send_membership_approved(row.user, club)
    flash(f'{row.user.username} approved and is now an active member.', 'success')
    return redirect(url_for('admin.club_team', slug=slug))


@admin_bp.route('/clubs/<slug>/members/<int:uid>/reject', methods=['POST'])
@club_admin_required
def club_member_reject(slug, uid):
    club = _get_club_or_404(slug)
    row = ClubMembership.query.filter_by(user_id=uid, club_id=club.id, status='pending').first_or_404()
    username = row.user.username
    send_membership_rejected(row.user, club)
    db.session.delete(row)
    db.session.commit()
    flash(f'{username}\'s membership request was rejected.', 'info')
    return redirect(url_for('admin.club_team', slug=slug))


# ── Club news/announcements ───────────────────────────────────────────────────

@admin_bp.route('/clubs/<slug>/posts')
@club_admin_required
def club_posts(slug):
    club = _get_club_or_404(slug)
    posts = (ClubPost.query.filter_by(club_id=club.id)
             .order_by(ClubPost.published_at.desc()).all())
    return render_template('admin/club_posts.html', club=club, posts=posts)


@admin_bp.route('/clubs/<slug>/posts/new', methods=['GET', 'POST'])
@club_admin_required
def post_new(slug):
    club = _get_club_or_404(slug)
    form = ClubPostForm()
    if form.validate_on_submit():
        post = ClubPost(
            club_id=club.id,
            author_id=current_user.id,
            title=form.title.data,
            body=form.body.data,
        )
        db.session.add(post)
        db.session.commit()
        flash('Post published.', 'success')
        return redirect(url_for('admin.club_posts', slug=slug))
    return render_template('admin/post_form.html', form=form, club=club, title='New Post', post=None)


@admin_bp.route('/clubs/<slug>/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@club_admin_required
def post_edit(slug, post_id):
    club = _get_club_or_404(slug)
    post = ClubPost.query.filter_by(id=post_id, club_id=club.id).first_or_404()
    form = ClubPostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data
        post.body  = form.body.data
        db.session.commit()
        flash('Post updated.', 'success')
        return redirect(url_for('admin.club_posts', slug=slug))
    return render_template('admin/post_form.html', form=form, club=club, title='Edit Post', post=post)


@admin_bp.route('/clubs/<slug>/posts/<int:post_id>/delete', methods=['POST'])
@club_admin_required
def post_delete(slug, post_id):
    club = _get_club_or_404(slug)
    post = ClubPost.query.filter_by(id=post_id, club_id=club.id).first_or_404()
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'info')
    return redirect(url_for('admin.club_posts', slug=slug))
