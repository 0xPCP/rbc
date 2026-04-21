"""
Tests for model properties: RideWithGPS URL parsing, embed URL generation,
pace labels, signup counts.
"""
import pytest
from datetime import date, time, timedelta
from app.models import Ride, RideSignup, User
from app.extensions import bcrypt


def make_ride(db, **kwargs):
    defaults = dict(
        title='Test Ride',
        date=date.today() + timedelta(days=1),
        time=time(17, 0),
        meeting_location='Somewhere',
        distance_miles=20.0,
        pace_category='B',
    )
    defaults.update(kwargs)
    ride = Ride(**defaults)
    db.session.add(ride)
    db.session.commit()
    return ride


# ── RideWithGPS ───────────────────────────────────────────────────────────────

class TestRideWithGPS:
    def test_route_id_extracted(self, app, db):
        ride = make_ride(db, route_url='https://ridewithgps.com/routes/12345')
        assert ride.ridewithgps_route_id == '12345'

    def test_route_id_none_when_no_url(self, app, db):
        ride = make_ride(db, route_url=None)
        assert ride.ridewithgps_route_id is None

    def test_route_id_none_for_non_rwgps_url(self, app, db):
        ride = make_ride(db, route_url='https://strava.com/routes/99')
        assert ride.ridewithgps_route_id is None

    def test_embed_url_built_correctly(self, app, db):
        ride = make_ride(db, route_url='https://ridewithgps.com/routes/12345')
        assert ride.ridewithgps_embed_url == (
            'https://ridewithgps.com/embeds?type=route&id=12345'
            '&sampleGraph=true&distanceMarkers=true'
        )

    def test_embed_url_none_without_route(self, app, db):
        ride = make_ride(db, route_url=None)
        assert ride.ridewithgps_embed_url is None

    def test_map_image_url_built_correctly(self, app, db):
        ride = make_ride(db, route_url='https://ridewithgps.com/routes/12345')
        assert ride.ridewithgps_map_image_url == (
            'https://ridewithgps.com/routes/12345/hover_preview.png'
        )


# ── Video embed ───────────────────────────────────────────────────────────────

class TestEmbedUrl:
    def test_youtube_watch_url(self, app, db):
        ride = make_ride(db, video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        assert ride.embed_url == 'https://www.youtube.com/embed/dQw4w9WgXcQ'

    def test_youtu_be_shortlink(self, app, db):
        ride = make_ride(db, video_url='https://youtu.be/dQw4w9WgXcQ')
        assert ride.embed_url == 'https://www.youtube.com/embed/dQw4w9WgXcQ'

    def test_vimeo_url(self, app, db):
        ride = make_ride(db, video_url='https://vimeo.com/123456789')
        assert ride.embed_url == 'https://player.vimeo.com/video/123456789'

    def test_none_when_no_video(self, app, db):
        ride = make_ride(db, video_url=None)
        assert ride.embed_url is None

    def test_non_video_url_returned_as_is(self, app, db):
        ride = make_ride(db, video_url='https://example.com/video.mp4')
        assert ride.embed_url == 'https://example.com/video.mp4'


# ── Pace label ────────────────────────────────────────────────────────────────

class TestPaceLabel:
    @pytest.mark.parametrize('pace,expected', [
        ('A', 'A — Fast (22+ mph)'),
        ('B', 'B — Moderate (18–22 mph)'),
        ('C', 'C — Casual (14–18 mph)'),
        ('D', 'D — Beginner (<14 mph)'),
    ])
    def test_pace_labels(self, app, db, pace, expected):
        ride = make_ride(db, pace_category=pace)
        assert ride.pace_label == expected


# ── Signup count ──────────────────────────────────────────────────────────────

class TestSignupCount:
    def test_zero_when_no_signups(self, app, db):
        ride = make_ride(db)
        assert ride.signup_count == 0

    def test_increments_with_signups(self, app, db):
        ride = make_ride(db)
        user = User(
            username='u1',
            email='u1@test.com',
            password_hash=bcrypt.generate_password_hash('pass').decode(),
        )
        db.session.add(user)
        db.session.commit()
        signup = RideSignup(ride_id=ride.id, user_id=user.id)
        db.session.add(signup)
        db.session.commit()
        assert ride.signup_count == 1
