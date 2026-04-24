import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://rbc:rbc@db:5432/rbc'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

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
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@cyclingclubs.app')
    MAIL_SUPPRESS_SEND = not bool(os.environ.get('MAIL_SERVER', ''))
