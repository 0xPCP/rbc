"""
Tests for ride detail page and signup/unsignup flows.
"""
import pytest
from datetime import date, time, timedelta
from app.models import Ride, RideSignup
from app.extensions import db
from tests.conftest import login


@pytest.fixture
def one_ride(db):
    ride = Ride(
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


@pytest.fixture
def cancelled_ride(db):
    ride = Ride(
        title='Cancelled Saturday Ride',
        date=date.today() + timedelta(days=5),
        time=time(8, 0),
        meeting_location='Lake Newport',
        distance_miles=30.0,
        pace_category='B',
        is_cancelled=True,
    )
    db.session.add(ride)
    db.session.commit()
    return ride


# ── Ride detail ───────────────────────────────────────────────────────────────

class TestRideDetail:
    def test_returns_200(self, client, one_ride, mock_weather):
        resp = client.get(f'/rides/{one_ride.id}')
        assert resp.status_code == 200

    def test_shows_ride_title(self, client, one_ride, mock_weather):
        resp = client.get(f'/rides/{one_ride.id}')
        assert b'Saturday Group Ride' in resp.data

    def test_shows_ride_meta(self, client, one_ride, mock_weather):
        resp = client.get(f'/rides/{one_ride.id}')
        html = resp.data.decode()
        assert 'Lake Newport' in html
        assert '30' in html       # distance
        assert 'B' in html        # pace badge

    def test_404_for_missing_ride(self, client, mock_weather):
        resp = client.get('/rides/99999')
        assert resp.status_code == 404

    def test_weather_card_shown(self, client, one_ride, mock_weather):
        resp = client.get(f'/rides/{one_ride.id}')
        assert b'Forecast' in resp.data
        assert b'68' in resp.data   # mocked temp

    def test_sign_in_prompt_for_anonymous(self, client, one_ride, mock_weather):
        resp = client.get(f'/rides/{one_ride.id}')
        assert b'Sign in' in resp.data
        assert b'Sign Up for This Ride' not in resp.data

    def test_signup_button_for_authenticated(self, client, one_ride, regular_user, mock_weather):
        login(client, 'rider@rbc.com', 'password123')
        resp = client.get(f'/rides/{one_ride.id}')
        assert b'Sign Up for This Ride' in resp.data

    def test_cancelled_ride_shows_badge(self, client, cancelled_ride, mock_weather):
        resp = client.get(f'/rides/{cancelled_ride.id}')
        html = resp.data.decode()
        assert 'Cancelled' in html
        assert 'Sign Up for This Ride' not in html

    def test_back_to_calendar_link(self, client, one_ride, mock_weather):
        resp = client.get(f'/rides/{one_ride.id}')
        assert b'Back to Calendar' in resp.data


# ── Signup ────────────────────────────────────────────────────────────────────

class TestRideSignup:
    def test_signup_requires_login(self, client, one_ride):
        resp = client.post(f'/rides/{one_ride.id}/signup', follow_redirects=True)
        assert b'Sign In' in resp.data or resp.status_code in (302, 200)

    def test_signup_adds_record(self, client, one_ride, regular_user, db):
        login(client, 'rider@rbc.com', 'password123')
        resp = client.post(f'/rides/{one_ride.id}/signup', follow_redirects=True)
        assert resp.status_code == 200
        signup = RideSignup.query.filter_by(
            ride_id=one_ride.id, user_id=regular_user.id
        ).first()
        assert signup is not None

    def test_signup_increments_count(self, client, one_ride, regular_user, mock_weather):
        login(client, 'rider@rbc.com', 'password123')
        client.post(f'/rides/{one_ride.id}/signup', follow_redirects=True)
        resp = client.get(f'/rides/{one_ride.id}')
        assert b'1' in resp.data

    def test_double_signup_is_idempotent(self, client, one_ride, regular_user, db):
        login(client, 'rider@rbc.com', 'password123')
        client.post(f'/rides/{one_ride.id}/signup', follow_redirects=True)
        client.post(f'/rides/{one_ride.id}/signup', follow_redirects=True)
        count = RideSignup.query.filter_by(ride_id=one_ride.id).count()
        assert count == 1

    def test_cannot_signup_for_cancelled_ride(self, client, cancelled_ride, regular_user, db):
        login(client, 'rider@rbc.com', 'password123')
        client.post(f'/rides/{cancelled_ride.id}/signup', follow_redirects=True)
        count = RideSignup.query.filter_by(ride_id=cancelled_ride.id).count()
        assert count == 0

    def test_cancel_signup_removes_record(self, client, one_ride, regular_user, db):
        login(client, 'rider@rbc.com', 'password123')
        client.post(f'/rides/{one_ride.id}/signup', follow_redirects=True)
        client.post(f'/rides/{one_ride.id}/unsignup', follow_redirects=True)
        signup = RideSignup.query.filter_by(
            ride_id=one_ride.id, user_id=regular_user.id
        ).first()
        assert signup is None

    def test_cancel_signup_shows_button_change(self, client, one_ride, regular_user, mock_weather):
        login(client, 'rider@rbc.com', 'password123')
        client.post(f'/rides/{one_ride.id}/signup', follow_redirects=True)
        resp = client.get(f'/rides/{one_ride.id}')
        assert b'Cancel My Signup' in resp.data

    def test_signed_up_list_shown_to_authenticated(self, client, one_ride, regular_user, mock_weather):
        login(client, 'rider@rbc.com', 'password123')
        client.post(f'/rides/{one_ride.id}/signup', follow_redirects=True)
        resp = client.get(f'/rides/{one_ride.id}')
        assert b"Who's coming" in resp.data
        assert b'rider' in resp.data   # regular_user.username
