from functools import wraps
from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Ride, RideSignup, User
from ..forms import RideForm

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return login_required(decorated)


@admin_bp.route('/')
@admin_required
def dashboard():
    today = date.today()
    upcoming = (
        Ride.query
        .filter(Ride.date >= today)
        .order_by(Ride.date.asc())
        .limit(5)
        .all()
    )
    stats = {
        'total_members': User.query.count(),
        'upcoming_rides': Ride.query.filter(Ride.date >= today).count(),
        'total_rides': Ride.query.count(),
        'total_signups': RideSignup.query.count(),
    }
    return render_template('admin/dashboard.html', upcoming=upcoming, stats=stats)


@admin_bp.route('/rides')
@admin_required
def rides():
    all_rides = Ride.query.order_by(Ride.date.desc()).all()
    return render_template('admin/rides.html', rides=all_rides)


@admin_bp.route('/rides/new', methods=['GET', 'POST'])
@admin_required
def ride_new():
    form = RideForm()
    if form.validate_on_submit():
        ride = Ride(
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
            created_by=current_user.id,
        )
        db.session.add(ride)
        db.session.commit()
        flash('Ride created.', 'success')
        return redirect(url_for('admin.rides'))
    return render_template('admin/ride_form.html', form=form, title='New Ride')


@admin_bp.route('/rides/<int:ride_id>/edit', methods=['GET', 'POST'])
@admin_required
def ride_edit(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    form = RideForm(obj=ride)
    if form.validate_on_submit():
        ride.title = form.title.data
        ride.date = form.date.data
        ride.time = form.time.data
        ride.meeting_location = form.meeting_location.data
        ride.distance_miles = form.distance_miles.data
        ride.elevation_feet = form.elevation_feet.data
        ride.pace_category = form.pace_category.data
        ride.ride_leader = form.ride_leader.data or None
        ride.route_url = form.route_url.data or None
        ride.video_url = form.video_url.data or None
        ride.description = form.description.data or None
        ride.is_cancelled = form.is_cancelled.data
        db.session.commit()
        flash('Ride updated.', 'success')
        return redirect(url_for('admin.rides'))
    return render_template('admin/ride_form.html', form=form, title='Edit Ride', ride=ride)


@admin_bp.route('/rides/<int:ride_id>/delete', methods=['POST'])
@admin_required
def ride_delete(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    db.session.delete(ride)
    db.session.commit()
    flash('Ride deleted.', 'info')
    return redirect(url_for('admin.rides'))
