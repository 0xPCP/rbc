"""
Tests for authentication: registration, login, logout, first-user admin promotion.
"""
import pytest
from datetime import date, datetime, time, timedelta, timezone
from app.models import User, Ride, RideSignup
from tests.conftest import login, logout


# ── Registration ──────────────────────────────────────────────────────────────

class TestRegistration:
    def test_register_page_loads(self, client):
        resp = client.get('/auth/register')
        assert resp.status_code == 200

    def test_register_creates_user(self, client, db):
        resp = client.post('/auth/register', data={
            'username': 'newrider',
            'email': 'newrider@rbc.com',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
        }, follow_redirects=True)
        assert resp.status_code == 200
        user = User.query.filter_by(username='newrider').first()
        assert user is not None

    def test_first_user_becomes_admin(self, client, db):
        client.post('/auth/register', data={
            'username': 'firstuser',
            'email': 'first@rbc.com',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
        }, follow_redirects=True)
        user = User.query.filter_by(username='firstuser').first()
        assert user.is_admin is True

    def test_second_user_is_not_admin(self, client, admin_user, db):
        client.post('/auth/register', data={
            'username': 'seconduser',
            'email': 'second@rbc.com',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
        }, follow_redirects=True)
        user = User.query.filter_by(username='seconduser').first()
        assert user.is_admin is False

    def test_duplicate_username_rejected(self, client, regular_user, db):
        resp = client.post('/auth/register', data={
            'username': 'rider',          # same as regular_user
            'email': 'other@rbc.com',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
        }, follow_redirects=True)
        assert resp.status_code == 200
        count = User.query.filter_by(username='rider').count()
        assert count == 1

    def test_duplicate_email_rejected(self, client, regular_user, db):
        resp = client.post('/auth/register', data={
            'username': 'otherrider',
            'email': 'rider@test.com',   # same as regular_user
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
        }, follow_redirects=True)
        assert resp.status_code == 200
        count = User.query.filter_by(email='rider@test.com').count()
        assert count == 1

    def test_password_mismatch_rejected(self, client, db):
        resp = client.post('/auth/register', data={
            'username': 'mismatch',
            'email': 'mismatch@rbc.com',
            'password': 'StrongPass1!',
            'confirm_password': 'DifferentPass1!',
        }, follow_redirects=True)
        assert resp.status_code == 200
        user = User.query.filter_by(username='mismatch').first()
        assert user is None


# ── Login / Logout ────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_page_loads(self, client):
        resp = client.get('/auth/login')
        assert resp.status_code == 200

    def test_login_with_valid_credentials(self, client, regular_user):
        resp = login(client, 'rider@test.com', 'password123')
        assert resp.status_code == 200
        # Should be redirected away from login — check for username in nav
        assert b'rider' in resp.data

    def test_login_page_uses_trust_browser_label(self, client):
        resp = client.get('/auth/login')
        assert b'Trust this browser' in resp.data
        assert b'signed out after 6 hours' in resp.data

    def test_login_without_trust_does_not_issue_remember_cookie(self, client, regular_user):
        resp = client.post('/auth/login', data={
            'email': 'rider@test.com',
            'password': 'password123',
        })
        cookies = '\n'.join(resp.headers.getlist('Set-Cookie'))
        assert 'remember_token=' not in cookies

    def test_login_with_trust_issues_remember_cookie(self, client, regular_user):
        resp = client.post('/auth/login', data={
            'email': 'rider@test.com',
            'password': 'password123',
            'remember': 'y',
        })
        cookies = '\n'.join(resp.headers.getlist('Set-Cookie'))
        assert 'remember_token=' in cookies

    def test_login_with_bad_password(self, client, regular_user):
        resp = client.post('/auth/login', data={
            'email': 'rider@test.com',
            'password': 'wrongpassword',
        }, follow_redirects=True)
        assert resp.status_code == 200
        # Should stay on login page or show error
        assert b'rider' not in resp.data or b'Invalid' in resp.data

    def test_login_with_unknown_user(self, client):
        resp = client.post('/auth/login', data={
            'email': 'ghost@nowhere.com',
            'password': 'whatever',
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_logout_clears_session(self, client, regular_user):
        login(client, 'rider@test.com', 'password123')
        resp = logout(client)
        # After logout, Sign In link should appear
        assert b'Sign In' in resp.data

    def test_login_redirects_to_next(self, client, regular_user):
        resp = client.post('/auth/login?next=/clubs/', data={
            'email': 'rider@test.com',
            'password': 'password123',
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_non_trusted_session_expires_after_six_hours(self, client, regular_user):
        login(client, 'rider@test.com', 'password123')
        old = datetime.now(timezone.utc) - timedelta(hours=6, minutes=1)
        with client.session_transaction() as sess:
            sess['_paceline_auth_started_at'] = old.timestamp()
            sess['_paceline_trusted_browser'] = False

        resp = client.get('/auth/profile', follow_redirects=False)
        assert resp.status_code == 302
        assert '/auth/login?next=/auth/profile' in resp.headers['Location']

        resp = client.get('/auth/profile', follow_redirects=True)
        assert b'Your session expired' in resp.data
        assert b'Sign In' in resp.data

    def test_trusted_browser_skips_six_hour_reauth(self, client, regular_user):
        client.post('/auth/login', data={
            'email': 'rider@test.com',
            'password': 'password123',
            'remember': 'y',
        })
        old = datetime.now(timezone.utc) - timedelta(hours=12)
        with client.session_transaction() as sess:
            sess['_paceline_auth_started_at'] = old.timestamp()
            sess['_paceline_trusted_browser'] = True

        resp = client.get('/auth/profile')
        assert resp.status_code == 200
        assert b'rider' in resp.data


# ── Admin access ──────────────────────────────────────────────────────────────

class TestAdminAccess:
    def test_admin_link_visible_to_admin(self, client, admin_user):
        login(client, 'admin@test.com', 'password123')
        resp = client.get('/')
        assert b'Admin' in resp.data

    def test_admin_link_hidden_from_regular_user(self, client, regular_user):
        login(client, 'rider@test.com', 'password123')
        resp = client.get('/')
        assert b'Admin' not in resp.data

    def test_admin_dashboard_requires_admin(self, client, regular_user):
        login(client, 'rider@test.com', 'password123')
        resp = client.get('/admin/', follow_redirects=True)
        # Regular user should be redirected or get 403
        assert resp.status_code in (200, 403)
        assert b'Admin Dashboard' not in resp.data

    def test_admin_dashboard_accessible_to_admin(self, client, admin_user):
        login(client, 'admin@test.com', 'password123')
        resp = client.get('/admin/')
        assert resp.status_code == 200
        assert b'Admin' in resp.data


# ── Profile ───────────────────────────────────────────────────────────────────

class TestProfile:
    def test_profile_requires_login(self, client):
        resp = client.get('/auth/profile', follow_redirects=True)
        assert b'Sign In' in resp.data

    def test_profile_page_loads(self, client, regular_user):
        login(client)
        resp = client.get('/auth/profile')
        assert resp.status_code == 200
        assert b'rider' in resp.data

    def test_profile_shows_zip_field(self, client, regular_user):
        login(client)
        assert b'Zip Code' in client.get('/auth/profile').data

    def test_profile_update_username(self, client, regular_user, db):
        login(client)
        client.post('/auth/profile', data={
            'username': 'newrider', 'email': 'rider@test.com', 'zip_code': '',
        }, follow_redirects=True)
        from app.models import User
        assert User.query.filter_by(username='newrider').first() is not None

    def test_profile_update_zip_saves(self, client, regular_user, db):
        from unittest.mock import patch
        login(client)
        with patch('app.routes.auth.geocode_zip', return_value=(38.9, -77.3)):
            client.post('/auth/profile', data={
                'username': 'rider', 'email': 'rider@test.com', 'zip_code': '22101',
            }, follow_redirects=True)
        from app.models import User
        u = User.query.filter_by(username='rider').first()
        assert u.zip_code == '22101'
        assert u.lat == 38.9

    def test_duplicate_username_rejected(self, client, regular_user, second_user, db):
        login(client)
        resp = client.post('/auth/profile', data={
            'username': 'rider2', 'email': 'rider@test.com', 'zip_code': '',
        }, follow_redirects=True)
        assert b'already taken' in resp.data

    def test_profile_shows_ytd_stats(self, client, regular_user, sample_club, db):
        login(client)
        past_date = date.today() - timedelta(days=10)
        ride = Ride(
            club_id=sample_club.id, title='Past Ride', date=past_date,
            time=time(9, 0), meeting_location='HQ', distance_miles=30.0,
            elevation_feet=1500, pace_category='B',
        )
        db.session.add(ride)
        db.session.commit()
        db.session.add(RideSignup(ride_id=ride.id, user_id=regular_user.id, is_waitlist=False))
        db.session.commit()

        resp = client.get('/auth/profile')
        assert resp.status_code == 200
        assert b'Stats' in resp.data
        assert b'30.0' in resp.data

    def test_profile_shows_ride_history(self, client, regular_user, sample_club, db):
        login(client)
        past_date = date.today() - timedelta(days=5)
        ride = Ride(
            club_id=sample_club.id, title='History Test Ride', date=past_date,
            time=time(8, 0), meeting_location='Park', distance_miles=25.0,
            pace_category='C',
        )
        db.session.add(ride)
        db.session.commit()
        db.session.add(RideSignup(ride_id=ride.id, user_id=regular_user.id, is_waitlist=False))
        db.session.commit()

        resp = client.get('/auth/profile')
        assert b'History Test Ride' in resp.data

    def test_profile_history_excludes_waitlist(self, client, regular_user, sample_club, db):
        login(client)
        past_date = date.today() - timedelta(days=3)
        ride = Ride(
            club_id=sample_club.id, title='Waitlist Ride', date=past_date,
            time=time(8, 0), meeting_location='Park', distance_miles=20.0,
            pace_category='C',
        )
        db.session.add(ride)
        db.session.commit()
        db.session.add(RideSignup(ride_id=ride.id, user_id=regular_user.id, is_waitlist=True))
        db.session.commit()

        resp = client.get('/auth/profile')
        assert b'Waitlist Ride' not in resp.data
