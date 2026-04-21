from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Ride, RideSignup

rides_bp = Blueprint('rides', __name__)


@rides_bp.route('/')
def calendar():
    today = date.today()
    pace = request.args.get('pace', '')
    query = Ride.query.filter(Ride.date >= today).order_by(Ride.date.asc(), Ride.time.asc())
    if pace in ('A', 'B', 'C', 'D'):
        query = query.filter(Ride.pace_category == pace)
    rides = query.all()
    return render_template('calendar.html', rides=rides, active_pace=pace)


@rides_bp.route('/<int:ride_id>')
def detail(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    user_signed_up = False
    if current_user.is_authenticated:
        user_signed_up = RideSignup.query.filter_by(
            ride_id=ride_id, user_id=current_user.id
        ).first() is not None
    return render_template('ride_detail.html', ride=ride, user_signed_up=user_signed_up)


@rides_bp.route('/<int:ride_id>/signup', methods=['POST'])
@login_required
def signup(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.is_cancelled:
        flash('This ride has been cancelled.', 'warning')
        return redirect(url_for('rides.detail', ride_id=ride_id))

    signup = RideSignup(ride_id=ride_id, user_id=current_user.id)
    db.session.add(signup)
    try:
        db.session.commit()
        flash("You're signed up! See you on the road.", 'success')
    except IntegrityError:
        db.session.rollback()
        flash('You are already signed up for this ride.', 'info')

    return redirect(url_for('rides.detail', ride_id=ride_id))


@rides_bp.route('/<int:ride_id>/unsignup', methods=['POST'])
@login_required
def unsignup(ride_id):
    signup = RideSignup.query.filter_by(ride_id=ride_id, user_id=current_user.id).first()
    if signup:
        db.session.delete(signup)
        db.session.commit()
        flash("You've been removed from this ride.", 'info')
    return redirect(url_for('rides.detail', ride_id=ride_id))
