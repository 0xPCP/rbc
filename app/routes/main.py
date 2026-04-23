from datetime import date
from flask import Blueprint, render_template
from flask_login import current_user
from ..models import Club, Ride, RideSignup, ClubMembership
from ..weather import get_weather_for_rides

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    today = date.today()

    if current_user.is_authenticated:
        return _user_dashboard(today)

    # Landing page for logged-out visitors: show club directory teaser
    clubs = Club.query.filter_by(is_active=True).order_by(Club.name.asc()).all()
    return render_template('index.html', clubs=clubs, today=today)


def _user_dashboard(today):
    """Home screen for logged-in users: upcoming rides across all subscribed clubs."""
    # Clubs the user has joined
    memberships = (ClubMembership.query
                   .filter_by(user_id=current_user.id)
                   .all())
    club_ids = [m.club_id for m in memberships]

    # Rides the user is signed up for (upcoming only), across any club
    signed_up_ride_ids = set(
        s.ride_id for s in RideSignup.query.filter_by(user_id=current_user.id).all()
    )
    my_rides = (Ride.query
                .filter(Ride.id.in_(signed_up_ride_ids),
                        Ride.date >= today,
                        Ride.is_cancelled == False)
                .order_by(Ride.date.asc(), Ride.time.asc())
                .all()) if signed_up_ride_ids else []

    # Upcoming rides from subscribed clubs (not already signed up), next 14 days
    upcoming_club_rides = []
    if club_ids:
        upcoming_club_rides = (Ride.query
                               .filter(Ride.club_id.in_(club_ids),
                                       Ride.date >= today,
                                       Ride.is_cancelled == False,
                                       ~Ride.id.in_(signed_up_ride_ids))
                               .order_by(Ride.date.asc(), Ride.time.asc())
                               .limit(10).all())

    all_display_rides = list({r.id: r for r in my_rides + upcoming_club_rides}.values())
    weather = get_weather_for_rides(all_display_rides)

    # Clubs user hasn't joined yet (for discovery)
    joined_ids = set(club_ids)
    suggested_clubs = (Club.query
                       .filter_by(is_active=True)
                       .filter(~Club.id.in_(joined_ids))
                       .order_by(Club.name.asc())
                       .limit(4).all()) if True else []

    return render_template('dashboard.html',
                           my_rides=my_rides,
                           upcoming_club_rides=upcoming_club_rides,
                           weather=weather,
                           today=today,
                           suggested_clubs=suggested_clubs,
                           signed_up_ride_ids=signed_up_ride_ids)


@main_bp.route('/about')
def about():
    return render_template('about.html')
