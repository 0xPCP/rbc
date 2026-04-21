import re
from datetime import datetime, timezone
from flask_login import UserMixin
from .extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Strava linking
    strava_id = db.Column(db.BigInteger, unique=True, nullable=True)
    strava_access_token = db.Column(db.Text, nullable=True)
    strava_refresh_token = db.Column(db.Text, nullable=True)
    strava_token_expires_at = db.Column(db.Integer, nullable=True)  # Unix timestamp

    signups = db.relationship('RideSignup', backref='user', lazy=True, cascade='all, delete-orphan')


class Ride(db.Model):
    __tablename__ = 'rides'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    meeting_location = db.Column(db.String(500), nullable=False)
    distance_miles = db.Column(db.Float, nullable=False)
    elevation_feet = db.Column(db.Integer, nullable=True)
    pace_category = db.Column(db.String(2), nullable=False)  # A, B, C, D
    ride_leader = db.Column(db.String(100), nullable=True)
    route_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    video_url = db.Column(db.String(500), nullable=True)
    is_cancelled = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    signups = db.relationship('RideSignup', backref='ride', lazy=True, cascade='all, delete-orphan')

    @property
    def signup_count(self):
        return len(self.signups)

    @property
    def embed_url(self):
        """Convert YouTube/Vimeo watch URL to embed URL."""
        if not self.video_url:
            return None
        yt = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)', self.video_url)
        if yt:
            return f'https://www.youtube.com/embed/{yt.group(1)}'
        vm = re.search(r'vimeo\.com/(\d+)', self.video_url)
        if vm:
            return f'https://player.vimeo.com/video/{vm.group(1)}'
        return self.video_url

    @property
    def pace_label(self):
        labels = {
            'A': 'A — Fast (22+ mph)',
            'B': 'B — Moderate (18–22 mph)',
            'C': 'C — Casual (14–18 mph)',
            'D': 'D — Beginner (<14 mph)',
        }
        return labels.get(self.pace_category, self.pace_category)


class RideSignup(db.Model):
    __tablename__ = 'ride_signups'

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint('ride_id', 'user_id', name='uq_ride_user'),)
