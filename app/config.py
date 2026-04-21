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
