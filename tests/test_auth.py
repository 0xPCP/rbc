"""
Tests for authentication: registration, login, logout, first-user admin promotion.
"""
import pytest
from app.models import User
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
