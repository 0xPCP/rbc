from datetime import date
from flask import Blueprint, render_template
from ..models import Ride
from ..routes.strava import get_club_activities

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    today = date.today()
    next_ride = (
        Ride.query
        .filter(Ride.date >= today, Ride.is_cancelled == False)
        .order_by(Ride.date.asc(), Ride.time.asc())
        .first()
    )
    strava_activities = get_club_activities(limit=6)
    return render_template('index.html', next_ride=next_ride, strava_activities=strava_activities)


@main_bp.route('/about')
def about():
    return render_template('about.html')
