"""Tests for weather-based ride auto-cancel logic."""
import pytest
from datetime import date, time, timedelta
from unittest.mock import patch

from app.models import Club, Ride
from app.extensions import db


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_today_ride(db, club, **kwargs):
    """Create a ride scheduled for today."""
    ride = Ride(
        club_id=club.id,
        title=kwargs.get('title', 'Test Ride'),
        date=date.today(),
        time=time(17, 0),
        meeting_location='Test Location',
        distance_miles=20.0,
        pace_category='B',
    )
    db.session.add(ride)
    db.session.commit()
    return ride


CLEAR_WEATHER = {
    'description': 'Clear', 'emoji': '☀️', 'severity': 0,
    'temp_f': 65, 'wind_mph': 8, 'precip_prob': 5,
    'warning': False, 'warning_reasons': [],
}

RAINY_WEATHER = {
    'description': 'Rain', 'emoji': '🌧️', 'severity': 2,
    'temp_f': 60, 'wind_mph': 12, 'precip_prob': 85,
    'warning': True, 'warning_reasons': ['85% chance of rain'],
}

WINDY_WEATHER = {
    'description': 'Windy', 'emoji': '💨', 'severity': 1,
    'temp_f': 62, 'wind_mph': 40, 'precip_prob': 10,
    'warning': True, 'warning_reasons': ['40 mph winds'],
}

COLD_WEATHER = {
    'description': 'Cold', 'emoji': '❄️', 'severity': 2,
    'temp_f': 22, 'wind_mph': 10, 'precip_prob': 10,
    'warning': True, 'warning_reasons': ['22°F — dress in layers'],
}

HOT_WEATHER = {
    'description': 'Hot', 'emoji': '🌡️', 'severity': 2,
    'temp_f': 105, 'wind_mph': 5, 'precip_prob': 0,
    'warning': True, 'warning_reasons': ['105°F — extreme heat'],
}


# ── Model tests ───────────────────────────────────────────────────────────────

def test_club_auto_cancel_defaults(app, sample_club):
    """New clubs default to auto-cancel disabled with sensible thresholds."""
    assert sample_club.auto_cancel_enabled is False
    assert sample_club.cancel_rain_prob == 80
    assert sample_club.cancel_wind_mph == 35
    assert sample_club.cancel_temp_min_f == 28
    assert sample_club.cancel_temp_max_f == 100


def test_ride_cancel_reason_nullable(app, sample_club):
    """cancel_reason is nullable by default."""
    ride = _make_today_ride(db, sample_club)
    assert ride.cancel_reason is None


# ── Auto-cancel logic tests ───────────────────────────────────────────────────

def _run_job(app):
    from app.scheduler import check_auto_cancels
    check_auto_cancels(app)


def test_no_cancel_when_disabled(app, sample_club):
    """Auto-cancel does nothing when disabled for the club."""
    sample_club.auto_cancel_enabled = False
    db.session.commit()
    ride = _make_today_ride(db, sample_club)

    with patch('app.scheduler.get_weather_for_rides', return_value={ride.id: RAINY_WEATHER}):
        _run_job(app)

    db.session.refresh(ride)
    assert ride.is_cancelled is False


def test_cancel_on_rain(app, sample_club):
    """Ride is cancelled when rain probability exceeds threshold."""
    sample_club.auto_cancel_enabled = True
    sample_club.cancel_rain_prob = 80
    db.session.commit()
    ride = _make_today_ride(db, sample_club)

    with patch('app.scheduler.get_weather_for_rides', return_value={ride.id: RAINY_WEATHER}):
        _run_job(app)

    db.session.refresh(ride)
    assert ride.is_cancelled is True
    assert ride.cancel_reason is not None
    assert 'weather' in ride.cancel_reason.lower()


def test_no_cancel_below_rain_threshold(app, sample_club):
    """Ride is not cancelled when rain probability is below threshold."""
    sample_club.auto_cancel_enabled = True
    sample_club.cancel_rain_prob = 90
    db.session.commit()
    ride = _make_today_ride(db, sample_club)

    with patch('app.scheduler.get_weather_for_rides', return_value={ride.id: RAINY_WEATHER}):
        _run_job(app)

    db.session.refresh(ride)
    assert ride.is_cancelled is False


def test_cancel_on_wind(app, sample_club):
    """Ride is cancelled when wind speed exceeds threshold."""
    sample_club.auto_cancel_enabled = True
    sample_club.cancel_wind_mph = 35
    db.session.commit()
    ride = _make_today_ride(db, sample_club)

    with patch('app.scheduler.get_weather_for_rides', return_value={ride.id: WINDY_WEATHER}):
        _run_job(app)

    db.session.refresh(ride)
    assert ride.is_cancelled is True


def test_cancel_on_cold(app, sample_club):
    """Ride is cancelled when temperature is below minimum threshold."""
    sample_club.auto_cancel_enabled = True
    sample_club.cancel_temp_min_f = 28
    db.session.commit()
    ride = _make_today_ride(db, sample_club)

    with patch('app.scheduler.get_weather_for_rides', return_value={ride.id: COLD_WEATHER}):
        _run_job(app)

    db.session.refresh(ride)
    assert ride.is_cancelled is True


def test_cancel_on_heat(app, sample_club):
    """Ride is cancelled when temperature exceeds maximum threshold."""
    sample_club.auto_cancel_enabled = True
    sample_club.cancel_temp_max_f = 100
    db.session.commit()
    ride = _make_today_ride(db, sample_club)

    with patch('app.scheduler.get_weather_for_rides', return_value={ride.id: HOT_WEATHER}):
        _run_job(app)

    db.session.refresh(ride)
    assert ride.is_cancelled is True


def test_no_cancel_clear_weather(app, sample_club):
    """Ride is not cancelled under clear, mild conditions."""
    sample_club.auto_cancel_enabled = True
    db.session.commit()
    ride = _make_today_ride(db, sample_club)

    with patch('app.scheduler.get_weather_for_rides', return_value={ride.id: CLEAR_WEATHER}):
        _run_job(app)

    db.session.refresh(ride)
    assert ride.is_cancelled is False


def test_already_cancelled_ride_skipped(app, sample_club):
    """Rides that are already cancelled are not reprocessed."""
    sample_club.auto_cancel_enabled = True
    db.session.commit()
    ride = _make_today_ride(db, sample_club)
    ride.is_cancelled = True
    ride.cancel_reason = 'Manual cancel'
    db.session.commit()

    with patch('app.scheduler.get_weather_for_rides') as mock_w:
        _run_job(app)
    mock_w.assert_not_called()

    db.session.refresh(ride)
    assert ride.cancel_reason == 'Manual cancel'


def test_no_weather_data_no_cancel(app, sample_club):
    """If weather fetch returns no data for a ride, it is not cancelled."""
    sample_club.auto_cancel_enabled = True
    db.session.commit()
    ride = _make_today_ride(db, sample_club)

    with patch('app.scheduler.get_weather_for_rides', return_value={}):
        _run_job(app)

    db.session.refresh(ride)
    assert ride.is_cancelled is False


def test_cancel_reason_includes_details(app, sample_club):
    """cancel_reason string includes the specific threshold that was exceeded."""
    sample_club.auto_cancel_enabled = True
    sample_club.cancel_rain_prob = 80
    db.session.commit()
    ride = _make_today_ride(db, sample_club)

    with patch('app.scheduler.get_weather_for_rides', return_value={ride.id: RAINY_WEATHER}):
        _run_job(app)

    db.session.refresh(ride)
    assert '85%' in ride.cancel_reason
    assert 'precipitation' in ride.cancel_reason.lower()


def test_only_todays_rides_checked(app, sample_club):
    """The scheduler only checks rides scheduled for today, not future rides."""
    sample_club.auto_cancel_enabled = True
    db.session.commit()

    tomorrow_ride = Ride(
        club_id=sample_club.id,
        title='Tomorrow Ride',
        date=date.today() + timedelta(days=1),
        time=time(17, 0),
        meeting_location='Somewhere',
        distance_miles=20.0,
        pace_category='B',
    )
    db.session.add(tomorrow_ride)
    db.session.commit()

    with patch('app.scheduler.get_weather_for_rides', return_value={tomorrow_ride.id: RAINY_WEATHER}):
        _run_job(app)

    db.session.refresh(tomorrow_ride)
    assert tomorrow_ride.is_cancelled is False


# ── Admin settings tests ──────────────────────────────────────────────────────

def test_club_settings_saves_thresholds(client, app, sample_club, club_admin_user):
    """Club settings form saves auto-cancel threshold fields correctly."""
    from tests.conftest import login
    login(client, email='clubadmin@test.com')

    resp = client.post(
        f'/admin/clubs/{sample_club.slug}/settings',
        data={
            'name': sample_club.name,
            'auto_cancel_enabled': 'y',
            'cancel_rain_prob': '75',
            'cancel_wind_mph': '30',
            'cancel_temp_min_f': '32',
            'cancel_temp_max_f': '95',
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    db.session.refresh(sample_club)
    assert sample_club.auto_cancel_enabled is True
    assert sample_club.cancel_rain_prob == 75
    assert sample_club.cancel_wind_mph == 30
    assert sample_club.cancel_temp_min_f == 32
    assert sample_club.cancel_temp_max_f == 95


def test_club_settings_disable_auto_cancel(client, app, sample_club, club_admin_user):
    """Unchecking auto_cancel_enabled sets the flag to False."""
    sample_club.auto_cancel_enabled = True
    db.session.commit()

    from tests.conftest import login
    login(client, email='clubadmin@test.com')
    resp = client.post(
        f'/admin/clubs/{sample_club.slug}/settings',
        data={
            'name': sample_club.name,
            # auto_cancel_enabled omitted → unchecked
            'cancel_rain_prob': '80',
            'cancel_wind_mph': '35',
            'cancel_temp_min_f': '28',
            'cancel_temp_max_f': '100',
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.refresh(sample_club)
    assert sample_club.auto_cancel_enabled is False
