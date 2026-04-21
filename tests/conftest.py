"""
Shared pytest fixtures for the RBC test suite.

Uses an in-memory SQLite database so no running PostgreSQL is needed.
Weather API calls are patched by default — tests that need real weather
data can opt-out by not using the mock_weather fixture.
"""
import pytest
from datetime import date, time, timedelta
from unittest.mock import patch

from app import create_app
from app.extensions import db as _db
from app.models import User, Ride, RideSignup


# ── Test configuration ────────────────────────────────────────────────────────

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Strava not needed for most tests
    STRAVA_CLIENT_ID = None
    STRAVA_CLIENT_SECRET = None
    STRAVA_CLUB_ID = None
    STRAVA_CLUB_REFRESH_TOKEN = None


# ── Core fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope='function')
def app():
    """Fresh Flask app + SQLite schema for each test."""
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    """Database session (app context already active via app fixture)."""
    return _db


# ── Sample data fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    """Admin user."""
    from app.extensions import bcrypt
    user = User(
        username='admin',
        email='admin@rbc.com',
        password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'),
        is_admin=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def regular_user(db):
    """Non-admin user."""
    from app.extensions import bcrypt
    user = User(
        username='rider',
        email='rider@rbc.com',
        password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'),
        is_admin=False,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_rides(db):
    """
    Three rides spread across this week so they appear in week and month views.
    All dates are relative to today so tests stay green over time.
    """
    today = date.today()
    # Snap to this Monday so rides land within the current week view
    monday = today - timedelta(days=today.weekday())

    rides = [
        Ride(
            title='Tuesday A Ride',
            date=monday + timedelta(days=1),   # Tuesday
            time=time(17, 0),
            meeting_location='Hunterwoods Shopping Center',
            distance_miles=38.0,
            elevation_feet=2100,
            pace_category='A',
            ride_leader='Dave K.',
        ),
        Ride(
            title='Wednesday B Ride',
            date=monday + timedelta(days=2),   # Wednesday
            time=time(18, 0),
            meeting_location='The Bike Lane',
            distance_miles=25.0,
            pace_category='B',
        ),
        Ride(
            title='Thursday C Ride',
            date=monday + timedelta(days=3),   # Thursday
            time=time(18, 30),
            meeting_location='Lake Newport',
            distance_miles=20.0,
            pace_category='C',
            is_cancelled=True,
        ),
    ]
    for r in rides:
        db.session.add(r)
    db.session.commit()
    return rides


# ── Weather mock ──────────────────────────────────────────────────────────────

@pytest.fixture
def mock_weather():
    """
    Patches get_weather_for_rides to return a predictable response so tests
    don't depend on the Open-Meteo API or network availability.
    """
    def _fake_weather(rides):
        return {
            r.id: {
                'description': 'Partly cloudy',
                'emoji': '⛅',
                'severity': 0,
                'temp_f': 68,
                'wind_mph': 10,
                'precip_prob': 10,
                'warning': False,
                'warning_reasons': [],
            }
            for r in rides
        }

    with patch('app.routes.rides.get_weather_for_rides', side_effect=_fake_weather) as m:
        yield m


# ── Auth helpers ──────────────────────────────────────────────────────────────

def login(client, email='rider@rbc.com', password='password123'):
    return client.post('/auth/login', data={
        'email': email,
        'password': password,
    }, follow_redirects=True)


def logout(client):
    return client.get('/auth/logout', follow_redirects=True)
