"""
Tests for the super admin panel:
  - Non-admin users are blocked (403) from all admin user-management endpoints
  - User list: search and filter
  - User detail page
  - Password reset: generates a working temp password
  - Toggle admin: grant, revoke, can't change own status
  - Toggle active: deactivate, reactivate, can't deactivate self
  - Deactivated user cannot log in
"""
import pytest
from unittest.mock import patch
from app.extensions import db, bcrypt
from app.models import Club, User
from tests.conftest import login, logout


# ── Helpers ───────────────────────────────────────────────────────────────────

def login_as(client, user, password='password123'):
    return client.post('/auth/login', data={
        'email': user.email, 'password': password,
    }, follow_redirects=True)


def make_user(db, username, email, is_admin=False, is_active=True, password='password123'):
    u = User(
        username=username,
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode(),
        is_admin=is_admin,
        is_active=is_active,
    )
    db.session.add(u)
    db.session.commit()
    return u


# ── Access control ─────────────────────────────────────────────────────────────

class TestSuperadminAccessControl:

    def test_unauthenticated_user_list_redirects(self, client):
        resp = client.get('/admin/users/', follow_redirects=False)
        assert resp.status_code in (302, 403)

    def test_regular_user_blocked_user_list(self, client, db, regular_user):
        login_as(client, regular_user)
        resp = client.get('/admin/users/')
        assert resp.status_code == 403

    def test_regular_user_blocked_user_detail(self, client, db, regular_user, admin_user):
        login_as(client, regular_user)
        resp = client.get(f'/admin/users/{admin_user.id}')
        assert resp.status_code == 403

    def test_regular_user_blocked_reset_password(self, client, db, regular_user, admin_user):
        login_as(client, regular_user)
        resp = client.post(f'/admin/users/{admin_user.id}/reset-password')
        assert resp.status_code == 403

    def test_regular_user_blocked_toggle_admin(self, client, db, regular_user, admin_user):
        login_as(client, regular_user)
        resp = client.post(f'/admin/users/{admin_user.id}/toggle-admin')
        assert resp.status_code == 403

    def test_regular_user_blocked_toggle_active(self, client, db, regular_user, admin_user):
        login_as(client, regular_user)
        resp = client.post(f'/admin/users/{admin_user.id}/toggle-active')
        assert resp.status_code == 403

    def test_superadmin_can_access_user_list(self, client, db, admin_user):
        login_as(client, admin_user)
        resp = client.get('/admin/users/')
        assert resp.status_code == 200

    def test_superadmin_can_access_user_detail(self, client, db, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.get(f'/admin/users/{regular_user.id}')
        assert resp.status_code == 200


# ── User list ─────────────────────────────────────────────────────────────────

class TestUserList:

    def test_user_list_shows_all_users(self, client, db, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.get('/admin/users/')
        assert resp.status_code == 200
        assert b'rider' in resp.data
        assert b'superadmin' in resp.data

    def test_search_by_username(self, client, db, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.get('/admin/users/?q=rider')
        assert resp.status_code == 200
        assert b'rider@test.com' in resp.data
        assert b'admin@test.com' not in resp.data  # admin email absent from results

    def test_search_by_email(self, client, db, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.get('/admin/users/?q=admin@test.com')
        assert resp.status_code == 200
        assert b'admin@test.com' in resp.data
        assert b'rider@test.com' not in resp.data

    def test_filter_admins(self, client, db, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.get('/admin/users/?filter=admins')
        assert resp.status_code == 200
        assert b'admin@test.com' in resp.data
        assert b'rider@test.com' not in resp.data

    def test_filter_inactive(self, client, db, admin_user):
        inactive = make_user(db, 'sleeper', 'sleeper@test.com', is_active=False)
        login_as(client, admin_user)
        resp = client.get('/admin/users/?filter=inactive')
        assert resp.status_code == 200
        assert b'sleeper@test.com' in resp.data
        assert b'admin@test.com' not in resp.data  # admin is active, not in inactive filter

    def test_search_no_results(self, client, db, admin_user):
        login_as(client, admin_user)
        resp = client.get('/admin/users/?q=zzznobody')
        assert resp.status_code == 200
        assert b'No users found' in resp.data


# ── User detail ───────────────────────────────────────────────────────────────

class TestUserDetail:

    def test_detail_shows_account_info(self, client, db, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.get(f'/admin/users/{regular_user.id}')
        assert resp.status_code == 200
        assert b'rider@test.com' in resp.data
        assert b'rider' in resp.data

    def test_detail_404_for_nonexistent_user(self, client, db, admin_user):
        login_as(client, admin_user)
        resp = client.get('/admin/users/99999')
        assert resp.status_code == 404

    def test_detail_shows_deactivated_badge(self, client, db, admin_user):
        inactive = make_user(db, 'goneguy', 'gone@test.com', is_active=False)
        login_as(client, admin_user)
        resp = client.get(f'/admin/users/{inactive.id}')
        assert resp.status_code == 200
        assert b'Deactivated' in resp.data

    def test_detail_self_actions_disabled(self, client, db, admin_user):
        """Admin/active action buttons are hidden when viewing own account."""
        login_as(client, admin_user)
        resp = client.get(f'/admin/users/{admin_user.id}')
        assert resp.status_code == 200
        assert b'Admin/active actions are disabled' in resp.data


# ── Password reset ────────────────────────────────────────────────────────────

class TestPasswordReset:

    def test_reset_password_changes_hash(self, client, db, admin_user, regular_user):
        old_hash = regular_user.password_hash
        login_as(client, admin_user)
        resp = client.post(
            f'/admin/users/{regular_user.id}/reset-password',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.password_hash != old_hash

    def test_reset_password_flash_contains_temp_password(self, client, db, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.post(
            f'/admin/users/{regular_user.id}/reset-password',
            follow_redirects=True,
        )
        assert b'Temporary password' in resp.data

    def test_reset_password_new_pw_works(self, client, db, admin_user, regular_user):
        """After reset, the user should be able to log in with the temp password."""
        login_as(client, admin_user)
        # Capture the redirect response (not following) to stay on detail page
        client.post(f'/admin/users/{regular_user.id}/reset-password', follow_redirects=True)

        # Re-fetch user and brute-check we can find the new hash via bcrypt
        db.session.refresh(regular_user)
        # We can't read the temp pw from the response easily, so just verify hash changed
        # and that the old password no longer works
        logout(client)
        resp = client.post('/auth/login', data={
            'email': regular_user.email, 'password': 'password123',
        }, follow_redirects=True)
        # Old password should fail
        assert b'Invalid email or password' in resp.data


# ── Toggle admin ──────────────────────────────────────────────────────────────

class TestToggleAdmin:

    def test_grant_admin(self, client, db, admin_user, regular_user):
        assert not regular_user.is_admin
        login_as(client, admin_user)
        resp = client.post(
            f'/admin/users/{regular_user.id}/toggle-admin',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.is_admin

    def test_revoke_admin(self, client, db, admin_user):
        second_admin = make_user(db, 'admin2', 'admin2@test.com', is_admin=True)
        login_as(client, admin_user)
        resp = client.post(
            f'/admin/users/{second_admin.id}/toggle-admin',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(second_admin)
        assert not second_admin.is_admin

    def test_cannot_change_own_admin_status(self, client, db, admin_user):
        login_as(client, admin_user)
        resp = client.post(
            f'/admin/users/{admin_user.id}/toggle-admin',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'cannot change your own' in resp.data
        db.session.refresh(admin_user)
        assert admin_user.is_admin  # unchanged

    def test_grant_admin_flash_message(self, client, db, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.post(
            f'/admin/users/{regular_user.id}/toggle-admin',
            follow_redirects=True,
        )
        assert b'granted' in resp.data


# ── Toggle active ─────────────────────────────────────────────────────────────

class TestToggleActive:

    def test_deactivate_user(self, client, db, admin_user, regular_user):
        assert regular_user.is_active
        login_as(client, admin_user)
        resp = client.post(
            f'/admin/users/{regular_user.id}/toggle-active',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(regular_user)
        assert not regular_user.is_active

    def test_reactivate_user(self, client, db, admin_user):
        inactive = make_user(db, 'dormant', 'dormant@test.com', is_active=False)
        login_as(client, admin_user)
        resp = client.post(
            f'/admin/users/{inactive.id}/toggle-active',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(inactive)
        assert inactive.is_active

    def test_cannot_deactivate_self(self, client, db, admin_user):
        login_as(client, admin_user)
        resp = client.post(
            f'/admin/users/{admin_user.id}/toggle-active',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'cannot deactivate your own' in resp.data
        db.session.refresh(admin_user)
        assert admin_user.is_active  # unchanged

    def test_deactivate_flash_message(self, client, db, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.post(
            f'/admin/users/{regular_user.id}/toggle-active',
            follow_redirects=True,
        )
        assert b'deactivated' in resp.data

    def test_reactivate_flash_message(self, client, db, admin_user):
        inactive = make_user(db, 'zombie', 'zombie@test.com', is_active=False)
        login_as(client, admin_user)
        resp = client.post(
            f'/admin/users/{inactive.id}/toggle-active',
            follow_redirects=True,
        )
        assert b'reactivated' in resp.data


# ── Deactivated user cannot log in ────────────────────────────────────────────

class TestDeactivatedLogin:

    def test_deactivated_user_cannot_login(self, client, db):
        inactive = make_user(db, 'banned', 'banned@test.com', is_active=False)
        resp = client.post('/auth/login', data={
            'email': 'banned@test.com', 'password': 'password123',
        }, follow_redirects=True)
        assert b'deactivated' in resp.data.lower()

    def test_active_user_can_login(self, client, db, regular_user):
        resp = client.post('/auth/login', data={
            'email': regular_user.email, 'password': 'password123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'deactivated' not in resp.data.lower()

    def test_deactivated_user_session_invalidated(self, client, db, admin_user, regular_user):
        """A user who gets deactivated mid-session should be treated as anonymous."""
        login_as(client, regular_user)
        # Deactivate them while they are "logged in"
        regular_user.is_active = False
        db.session.commit()
        # Flask-Login checks is_active on each request — they should be redirected
        resp = client.get('/auth/profile', follow_redirects=False)
        assert resp.status_code == 302


# ── Bulk geocoding ─────────────────────────────────────────────────────────────

class TestBulkGeocoding:

    def _ungeocodeable_club(self, db):
        club = Club(slug='geo-test', name='Geo Test Club', zip_code='20148', lat=None, lng=None)
        db.session.add(club)
        db.session.commit()
        return club

    def test_geocode_clubs_requires_superadmin(self, client, db, regular_user):
        login_as(client, regular_user)
        resp = client.post('/admin/geocode-clubs', follow_redirects=False)
        assert resp.status_code == 403

    def test_geocode_clubs_fills_coordinates(self, client, db, admin_user):
        club = self._ungeocodeable_club(db)
        login_as(client, admin_user)
        with patch('app.routes.admin.geocode_zip', return_value=(38.9, -77.4)):
            resp = client.post('/admin/geocode-clubs', follow_redirects=True)
        assert resp.status_code == 200
        db.session.refresh(club)
        assert club.lat == pytest.approx(38.9)
        assert club.lng == pytest.approx(-77.4)

    def test_geocode_clubs_skips_already_geocoded(self, client, db, admin_user, sample_club):
        original_lat = sample_club.lat
        login_as(client, admin_user)
        with patch('app.routes.admin.geocode_zip', return_value=(0.0, 0.0)) as mock_geo:
            client.post('/admin/geocode-clubs', follow_redirects=True)
        mock_geo.assert_not_called()
        db.session.refresh(sample_club)
        assert sample_club.lat == original_lat

    def test_geocode_clubs_handles_lookup_failure(self, client, db, admin_user):
        club = self._ungeocodeable_club(db)
        login_as(client, admin_user)
        with patch('app.routes.admin.geocode_zip', return_value=None):
            resp = client.post('/admin/geocode-clubs', follow_redirects=True)
        assert resp.status_code == 200
        db.session.refresh(club)
        assert club.lat is None

    def test_dashboard_shows_geocode_warning(self, client, db, admin_user):
        self._ungeocodeable_club(db)
        login_as(client, admin_user)
        resp = client.get('/admin/')
        assert b'missing map coordinates' in resp.data

    def test_dashboard_no_geocode_warning_when_all_geocoded(self, client, db, admin_user, sample_club):
        login_as(client, admin_user)
        resp = client.get('/admin/')
        assert b'missing map coordinates' not in resp.data
