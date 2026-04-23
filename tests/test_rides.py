"""
Retained for test_models.py coverage cross-check.
Ride detail and signup tests have moved to test_clubs.py.
This file is intentionally minimal — it tests the Ride model directly
without going through the HTTP layer.
"""
import pytest
from datetime import date, time, timedelta
from app.models import Ride, RideSignup
from app.extensions import db


@pytest.fixture
def one_ride(db, sample_club):
    ride = Ride(
        club_id=sample_club.id,
        title='Saturday Group Ride',
        date=date.today() + timedelta(days=5),
        time=time(8, 0),
        meeting_location='Lake Newport',
        distance_miles=30.0,
        pace_category='B',
    )
    db.session.add(ride)
    db.session.commit()
    return ride


class TestRideModel:
    def test_ride_created(self, app, db, one_ride):
        assert Ride.query.count() == 1

    def test_signup_count_zero_initial(self, app, db, one_ride):
        assert one_ride.signup_count == 0

    def test_signup_count_increments(self, app, db, one_ride, regular_user):
        db.session.add(RideSignup(ride_id=one_ride.id, user_id=regular_user.id))
        db.session.commit()
        assert one_ride.signup_count == 1

    def test_ride_belongs_to_club(self, app, db, one_ride, sample_club):
        assert one_ride.club_id == sample_club.id
        assert one_ride.club.name == 'Test Cycling Club'
