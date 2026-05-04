import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://paceline:paceline@db:5432/paceline'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    AUTH_REAUTH_SECONDS = int(os.environ.get('AUTH_REAUTH_HOURS', 6)) * 60 * 60
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=AUTH_REAUTH_SECONDS)
    REMEMBER_COOKIE_DURATION = timedelta(days=int(os.environ.get('TRUSTED_BROWSER_DAYS', 30)))
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Strava
    STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
    STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
    STRAVA_CLUB_ID = os.environ.get('STRAVA_CLUB_ID')
    STRAVA_CLUB_REFRESH_TOKEN = os.environ.get('STRAVA_CLUB_REFRESH_TOKEN')

    # Email (Flask-Mail / SMTP)
    MAIL_SERVER   = os.environ.get('MAIL_SERVER', '')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS  = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@paceline.app')
    MAIL_SUPPRESS_SEND = not bool(os.environ.get('MAIL_SERVER', ''))

    # Internationalisation
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'

    # Hosted donation page. Leave blank to show the local coming-soon stub.
    DONATE_URL = os.environ.get('DONATE_URL', '').strip()

    # Media uploads — see docs/media_strategy.md for rationale and update guidance
    UPLOAD_FOLDER = os.environ.get(
        'UPLOAD_FOLDER',
        os.path.join(os.path.dirname(__file__), '..', 'uploads'),
    )
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024          # 5 MB hard Flask limit (pre-Pillow)
    MEDIA_EXPIRY_DAYS = int(os.environ.get('MEDIA_EXPIRY_DAYS', 90))
    MEDIA_MAX_PHOTOS_PER_USER_RIDE = int(os.environ.get('MEDIA_MAX_PHOTOS_PER_USER_RIDE', 5))
    MEDIA_MAX_PHOTOS_PER_RIDE = int(os.environ.get('MEDIA_MAX_PHOTOS_PER_RIDE', 30))
    MEDIA_MAX_WIDTH_PX = int(os.environ.get('MEDIA_MAX_WIDTH_PX', 1200))
