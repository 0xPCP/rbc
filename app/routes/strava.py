import time
import requests
from flask import Blueprint, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from ..extensions import db

strava_bp = Blueprint('strava', __name__)

# In-memory cache for club token and activity feed
_token_cache = {}
_activity_cache = {}


def _get_club_token():
    """Return a valid Strava access token for the club feed, refreshing if needed."""
    now = time.time()
    if _token_cache.get('expires_at', 0) > now + 60:
        return _token_cache.get('access_token')

    client_id = current_app.config.get('STRAVA_CLIENT_ID')
    client_secret = current_app.config.get('STRAVA_CLIENT_SECRET')
    refresh_token = current_app.config.get('STRAVA_CLUB_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_token]):
        return None

    try:
        resp = requests.post(
            'https://www.strava.com/oauth/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        _token_cache['access_token'] = data['access_token']
        _token_cache['expires_at'] = data['expires_at']
        return data['access_token']
    except requests.RequestException:
        return None


def get_club_activities(limit=6):
    """Fetch recent club activities, cached for 5 minutes."""
    now = time.time()
    if now - _activity_cache.get('ts', 0) < 300:
        return _activity_cache.get('data', [])

    token = _get_club_token()
    club_id = current_app.config.get('STRAVA_CLUB_ID')
    if not token or not club_id:
        return []

    try:
        resp = requests.get(
            f'https://www.strava.com/api/v3/clubs/{club_id}/activities',
            headers={'Authorization': f'Bearer {token}'},
            params={'per_page': limit},
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        activities = resp.json()
        # Convert units: meters → miles, meters → feet
        for a in activities:
            a['distance_miles'] = round(a.get('distance', 0) / 1609.34, 1)
            a['elevation_feet'] = round(a.get('total_elevation_gain', 0) * 3.28084)
            secs = a.get('moving_time', 0)
            a['moving_time_fmt'] = f"{secs // 3600}h {(secs % 3600) // 60}m" if secs >= 3600 else f"{secs // 60}m"
        _activity_cache['data'] = activities
        _activity_cache['ts'] = now
        return activities
    except requests.RequestException:
        return []


# ── Member Strava OAuth ──────────────────────────────────────────────────────

@strava_bp.route('/connect')
@login_required
def connect():
    client_id = current_app.config.get('STRAVA_CLIENT_ID')
    if not client_id:
        flash('Strava integration is not configured.', 'warning')
        return redirect(url_for('auth.profile'))

    callback_url = url_for('strava.callback', _external=True)
    auth_url = (
        f'https://www.strava.com/oauth/authorize'
        f'?client_id={client_id}'
        f'&redirect_uri={callback_url}'
        f'&response_type=code'
        f'&scope=read,activity:read'
    )
    return redirect(auth_url)


@strava_bp.route('/callback')
@login_required
def callback():
    code = request.args.get('code')
    if not code:
        flash('Strava authorization failed.', 'danger')
        return redirect(url_for('auth.profile'))

    client_id = current_app.config.get('STRAVA_CLIENT_ID')
    client_secret = current_app.config.get('STRAVA_CLIENT_SECRET')

    try:
        resp = requests.post(
            'https://www.strava.com/oauth/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'grant_type': 'authorization_code',
            },
            timeout=10,
        )
        if resp.status_code != 200:
            flash('Failed to link Strava account.', 'danger')
            return redirect(url_for('auth.profile'))

        data = resp.json()
        current_user.strava_id = data['athlete']['id']
        current_user.strava_access_token = data['access_token']
        current_user.strava_refresh_token = data['refresh_token']
        current_user.strava_token_expires_at = data['expires_at']
        db.session.commit()
        flash('Strava account linked!', 'success')
    except requests.RequestException:
        flash('Could not reach Strava. Please try again.', 'danger')

    return redirect(url_for('auth.profile'))


@strava_bp.route('/disconnect', methods=['POST'])
@login_required
def disconnect():
    current_user.strava_id = None
    current_user.strava_access_token = None
    current_user.strava_refresh_token = None
    current_user.strava_token_expires_at = None
    db.session.commit()
    flash('Strava account disconnected.', 'info')
    return redirect(url_for('auth.profile'))
