"""
Tests for post-ride media sharing.

Covers: photo upload (limits, wrong type, after-ride gate), video link posting,
delete permissions, serve route access control, and scheduler purge logic.
"""
import io
import os
from datetime import date, timedelta

import pytest

from app.models import RideMedia


# ── Helpers ────────────────────────────────────────────────────────────────────

def _login(client, user):
    client.post('/auth/login', data={'email': user.email, 'password': 'password123'},
                follow_redirects=True)


def _minimal_jpeg():
    """Return bytes of a valid JPEG (1×1 red pixel) using Pillow."""
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new('RGB', (1, 1), color=(255, 0, 0))
    img.save(buf, format='JPEG')
    return buf.getvalue()


def _make_past_ride(db, sample_club):
    """Create a ride dated yesterday so uploads are allowed."""
    from datetime import time as dtime
    from app.models import Ride
    ride = Ride(
        club_id=sample_club.id,
        title='Past Ride',
        date=date.today() - timedelta(days=1),
        time=dtime(7, 0),
        meeting_location='Trailhead',
        distance_miles=25.0,
        pace_category='B',
    )
    db.session.add(ride)
    db.session.commit()
    return ride


def _make_future_ride(db, sample_club):
    from datetime import time as dtime
    from app.models import Ride
    ride = Ride(
        club_id=sample_club.id,
        title='Future Ride',
        date=date.today() + timedelta(days=3),
        time=dtime(7, 0),
        meeting_location='Trailhead',
        distance_miles=30.0,
        pace_category='A',
    )
    db.session.add(ride)
    db.session.commit()
    return ride


# ── Photo upload ───────────────────────────────────────────────────────────────

class TestPhotoUpload:
    def test_upload_requires_login(self, client, db, sample_club):
        ride = _make_past_ride(db, sample_club)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/photo',
            data={'photo': (io.BytesIO(b'x'), 'test.jpg')},
            content_type='multipart/form-data',
            follow_redirects=False,
        )
        assert resp.status_code in (302, 403)

    def test_upload_blocked_before_ride_date(self, client, db, sample_club, regular_user):
        ride = _make_future_ride(db, sample_club)
        _login(client, regular_user)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/photo',
            data={'photo': (io.BytesIO(_minimal_jpeg()), 'photo.jpg')},
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'only be shared after' in resp.data
        with client.application.app_context():
            assert RideMedia.query.filter_by(ride_id=ride.id).count() == 0

    def test_upload_rejected_for_non_image(self, client, db, sample_club, regular_user, tmp_path):
        ride = _make_past_ride(db, sample_club)
        _login(client, regular_user)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/photo',
            data={'photo': (io.BytesIO(b'not an image'), 'video.mp4')},
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        assert b'Only JPEG' in resp.data or b'only' in resp.data.lower()
        with client.application.app_context():
            assert RideMedia.query.filter_by(ride_id=ride.id).count() == 0

    def test_upload_valid_jpeg_creates_record(self, client, db, sample_club, regular_user, app, tmp_path):
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        ride = _make_past_ride(db, sample_club)
        _login(client, regular_user)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/photo',
            data={
                'photo': (io.BytesIO(_minimal_jpeg()), 'photo.jpg'),
                'caption': 'Great day!',
            },
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        with app.app_context():
            item = RideMedia.query.filter_by(ride_id=ride.id, media_type='photo').first()
            assert item is not None
            assert item.caption == 'Great day!'
            assert item.file_path is not None
            assert item.user_id == regular_user.id
            # File should exist on disk
            full = os.path.join(str(tmp_path), item.file_path)
            assert os.path.exists(full)

    def test_per_user_photo_limit_enforced(self, client, db, sample_club, regular_user, app, tmp_path):
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        app.config['MEDIA_MAX_PHOTOS_PER_USER_RIDE'] = 2
        ride = _make_past_ride(db, sample_club)

        with app.app_context():
            for _ in range(2):
                db.session.add(RideMedia(
                    ride_id=ride.id, user_id=regular_user.id,
                    media_type='photo', file_path='fake/path.jpg',
                ))
            db.session.commit()

        _login(client, regular_user)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/photo',
            data={'photo': (io.BytesIO(_minimal_jpeg()), 'photo.jpg')},
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        assert b'at most 2' in resp.data

    def test_per_ride_photo_limit_enforced(self, client, db, sample_club, regular_user,
                                           second_user, app, tmp_path):
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        app.config['MEDIA_MAX_PHOTOS_PER_RIDE'] = 2
        ride = _make_past_ride(db, sample_club)

        with app.app_context():
            db.session.add(RideMedia(ride_id=ride.id, user_id=second_user.id,
                                     media_type='photo', file_path='fake/a.jpg'))
            db.session.add(RideMedia(ride_id=ride.id, user_id=second_user.id,
                                     media_type='photo', file_path='fake/b.jpg'))
            db.session.commit()

        _login(client, regular_user)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/photo',
            data={'photo': (io.BytesIO(_minimal_jpeg()), 'photo.jpg')},
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        assert b'2-photo limit' in resp.data or b'reached' in resp.data.lower()


# ── Video link ─────────────────────────────────────────────────────────────────

class TestVideoLink:
    def test_add_video_link(self, client, db, sample_club, regular_user, app):
        ride = _make_past_ride(db, sample_club)
        _login(client, regular_user)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/video',
            data={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'caption': 'Epic'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        with app.app_context():
            item = RideMedia.query.filter_by(ride_id=ride.id, media_type='video_link').first()
            assert item is not None
            assert 'youtube' in item.url
            assert item.caption == 'Epic'

    def test_video_blocked_before_ride_date(self, client, db, sample_club, regular_user):
        ride = _make_future_ride(db, sample_club)
        _login(client, regular_user)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/video',
            data={'url': 'https://www.youtube.com/watch?v=abc'},
            follow_redirects=True,
        )
        assert b'only be shared after' in resp.data

    def test_video_link_embed_url_youtube(self, app, db, sample_club, regular_user):
        ride = _make_past_ride(db, sample_club)
        with app.app_context():
            item = RideMedia(
                ride_id=ride.id, user_id=regular_user.id,
                media_type='video_link',
                url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            )
            db.session.add(item)
            db.session.commit()
            assert 'youtube.com/embed/dQw4w9WgXcQ' in item.embed_url

    def test_video_link_embed_url_vimeo(self, app, db, sample_club, regular_user):
        ride = _make_past_ride(db, sample_club)
        with app.app_context():
            item = RideMedia(
                ride_id=ride.id, user_id=regular_user.id,
                media_type='video_link',
                url='https://vimeo.com/123456789',
            )
            db.session.add(item)
            db.session.commit()
            assert 'player.vimeo.com/video/123456789' in item.embed_url

    def test_non_embeddable_url_returns_none(self, app, db, sample_club, regular_user):
        ride = _make_past_ride(db, sample_club)
        with app.app_context():
            item = RideMedia(
                ride_id=ride.id, user_id=regular_user.id,
                media_type='video_link',
                url='https://strava.com/activities/12345',
            )
            db.session.add(item)
            db.session.commit()
            assert item.embed_url is None

    def test_video_link_rejects_host_prefix_trick(self, client, db, sample_club, regular_user):
        ride = _make_past_ride(db, sample_club)
        _login(client, regular_user)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/video',
            data={'url': 'https://www.youtube.com.evil.example/watch?v=dQw4w9WgXcQ'},
            follow_redirects=True,
        )
        assert b'Only YouTube, Vimeo, and Strava activity links are accepted.' in resp.data
        assert RideMedia.query.filter_by(ride_id=ride.id, media_type='video_link').first() is None

    def test_video_link_rejects_quoted_injection(self, client, db, sample_club, regular_user):
        ride = _make_past_ride(db, sample_club)
        _login(client, regular_user)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/video',
            data={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ" onload="alert(1)'},
            follow_redirects=True,
        )
        assert b'Only YouTube, Vimeo, and Strava activity links are accepted.' in resp.data
        assert RideMedia.query.filter_by(ride_id=ride.id, media_type='video_link').first() is None


# ── Delete ─────────────────────────────────────────────────────────────────────

class TestMediaDelete:
    def test_author_can_delete_own_photo(self, client, db, sample_club, regular_user, app, tmp_path):
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        ride = _make_past_ride(db, sample_club)
        # Create a real file to delete
        ride_dir = os.path.join(str(tmp_path), 'ride_media', str(ride.id))
        os.makedirs(ride_dir, exist_ok=True)
        fpath = os.path.join(ride_dir, 'test.jpg')
        with open(fpath, 'wb') as f:
            f.write(b'fake')
        rel_path = os.path.join('ride_media', str(ride.id), 'test.jpg')

        with app.app_context():
            item = RideMedia(ride_id=ride.id, user_id=regular_user.id,
                             media_type='photo', file_path=rel_path)
            db.session.add(item)
            db.session.commit()
            mid = item.id

        _login(client, regular_user)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/{mid}/delete',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert not os.path.exists(fpath)
        with app.app_context():
            assert RideMedia.query.get(mid) is None

    def test_other_user_cannot_delete(self, client, db, sample_club, regular_user,
                                      second_user, app, tmp_path):
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        ride = _make_past_ride(db, sample_club)
        with app.app_context():
            item = RideMedia(ride_id=ride.id, user_id=regular_user.id,
                             media_type='video_link', url='https://youtube.com/watch?v=x')
            db.session.add(item)
            db.session.commit()
            mid = item.id

        _login(client, second_user)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/{mid}/delete',
            follow_redirects=True,
        )
        assert resp.status_code == 403

    def test_club_admin_can_delete_any_media(self, client, db, sample_club, regular_user,
                                              club_admin_user, app, tmp_path):
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        ride = _make_past_ride(db, sample_club)
        with app.app_context():
            item = RideMedia(ride_id=ride.id, user_id=regular_user.id,
                             media_type='video_link', url='https://youtube.com/watch?v=y')
            db.session.add(item)
            db.session.commit()
            mid = item.id

        _login(client, club_admin_user)
        resp = client.post(
            f'/clubs/{sample_club.slug}/rides/{ride.id}/media/{mid}/delete',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        with app.app_context():
            assert RideMedia.query.get(mid) is None


# ── Serve route ────────────────────────────────────────────────────────────────

class TestServePhoto:
    def test_serve_public_club_photo(self, client, db, sample_club, regular_user, app, tmp_path):
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        ride = _make_past_ride(db, sample_club)
        ride_dir = os.path.join(str(tmp_path), 'ride_media', str(ride.id))
        os.makedirs(ride_dir, exist_ok=True)
        with open(os.path.join(ride_dir, 'pic.jpg'), 'wb') as f:
            f.write(_minimal_jpeg())

        resp = client.get(f'/media/ride/{ride.id}/pic.jpg')
        assert resp.status_code == 200

    def test_serve_private_club_photo_requires_membership(self, client, db, sample_club,
                                                           regular_user, app, tmp_path):
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        sample_club.is_private = True
        db.session.commit()

        ride = _make_past_ride(db, sample_club)
        ride_dir = os.path.join(str(tmp_path), 'ride_media', str(ride.id))
        os.makedirs(ride_dir, exist_ok=True)
        with open(os.path.join(ride_dir, 'secret.jpg'), 'wb') as f:
            f.write(_minimal_jpeg())

        # Unauthenticated → 403
        resp = client.get(f'/media/ride/{ride.id}/secret.jpg')
        assert resp.status_code == 403

        # Non-member authenticated → 403
        _login(client, regular_user)
        resp = client.get(f'/media/ride/{ride.id}/secret.jpg')
        assert resp.status_code == 403


# ── Scheduler purge ────────────────────────────────────────────────────────────

class TestMediaPurge:
    def test_purge_deletes_old_records_and_files(self, app, db, sample_club, regular_user, tmp_path):
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        app.config['MEDIA_EXPIRY_DAYS'] = 30

        from datetime import time as dtime
        from app.models import Ride
        old_ride = Ride(
            club_id=sample_club.id,
            title='Old Ride',
            date=date.today() - timedelta(days=60),
            time=dtime(7, 0),
            meeting_location='Trailhead',
            distance_miles=20.0,
            pace_category='C',
        )
        db.session.add(old_ride)
        db.session.commit()

        ride_dir = os.path.join(str(tmp_path), 'ride_media', str(old_ride.id))
        os.makedirs(ride_dir, exist_ok=True)
        fpath = os.path.join(ride_dir, 'old.jpg')
        with open(fpath, 'wb') as f:
            f.write(b'fake')

        item = RideMedia(
            ride_id=old_ride.id, user_id=regular_user.id,
            media_type='photo',
            file_path=os.path.join('ride_media', str(old_ride.id), 'old.jpg'),
        )
        db.session.add(item)
        db.session.commit()
        mid = item.id

        from app.scheduler import purge_expired_media
        purge_expired_media(app)

        with app.app_context():
            assert RideMedia.query.get(mid) is None
        assert not os.path.exists(fpath)

    def test_purge_keeps_recent_media(self, app, db, sample_club, regular_user, tmp_path):
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        app.config['MEDIA_EXPIRY_DAYS'] = 90

        ride = _make_past_ride(db, sample_club)  # yesterday — well within 90 days
        item = RideMedia(
            ride_id=ride.id, user_id=regular_user.id,
            media_type='video_link', url='https://youtube.com/watch?v=z',
        )
        db.session.add(item)
        db.session.commit()
        mid = item.id

        from app.scheduler import purge_expired_media
        purge_expired_media(app)

        with app.app_context():
            assert RideMedia.query.get(mid) is not None


# ── Ride detail page shows media section ──────────────────────────────────────

class TestRideDetailMediaSection:
    def test_media_section_hidden_for_future_ride(self, client, db, sample_club):
        ride = _make_future_ride(db, sample_club)
        resp = client.get(f'/clubs/{sample_club.slug}/rides/{ride.id}')
        assert b'Ride Photos' not in resp.data

    def test_media_section_shown_for_past_ride(self, client, db, sample_club):
        ride = _make_past_ride(db, sample_club)
        resp = client.get(f'/clubs/{sample_club.slug}/rides/{ride.id}')
        assert b'Ride Photos' in resp.data

    def test_upload_form_hidden_when_unauthenticated(self, client, db, sample_club):
        ride = _make_past_ride(db, sample_club)
        resp = client.get(f'/clubs/{sample_club.slug}/rides/{ride.id}')
        assert b'Upload Photo' not in resp.data
        assert b'Sign in' in resp.data

    def test_upload_form_shown_when_authenticated(self, client, db, sample_club, regular_user):
        ride = _make_past_ride(db, sample_club)
        _login(client, regular_user)
        resp = client.get(f'/clubs/{sample_club.slug}/rides/{ride.id}')
        assert b'Upload Photo' in resp.data
        assert b'Share Video' in resp.data
