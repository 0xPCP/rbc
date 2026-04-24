"""Tests for the Leaflet club map page and /api/clubs/map-data endpoint."""
import pytest
from tests.conftest import login


def test_map_page_renders(client, sample_club):
    resp = client.get('/clubs/map/')
    assert resp.status_code == 200
    assert b'leaflet' in resp.data.lower()
    # Club data is now server-side embedded JSON, not a client-side fetch
    assert sample_club.slug.encode() in resp.data


def test_map_page_embeds_club_coords(client, sample_club):
    """Club lat/lng is embedded in the page as JSON when the club is geocoded."""
    resp = client.get('/clubs/map/')
    assert resp.status_code == 200
    assert str(sample_club.lat).encode() in resp.data
    assert str(sample_club.lng).encode() in resp.data


def test_map_page_excludes_ungeocoded_clubs(client, sample_club):
    """A club without lat/lng is not embedded in the page data."""
    sample_club.lat = None
    sample_club.lng = None
    from app.extensions import db
    db.session.commit()

    resp = client.get('/clubs/map/')
    assert resp.status_code == 200
    assert sample_club.slug.encode() not in resp.data


def test_map_data_no_coords(client, sample_club):
    """Club without lat/lng is excluded from map data."""
    sample_club.lat = None
    sample_club.lng = None
    from app.extensions import db
    db.session.commit()

    resp = client.get('/api/clubs/map-data')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert all(c['id'] != sample_club.id for c in data)


def test_map_data_with_coords(client, sample_club):
    """Club with lat/lng appears in map data with correct shape."""
    resp = client.get('/api/clubs/map-data')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    club_data = data[0]
    assert club_data['id'] == sample_club.id
    assert club_data['slug'] == sample_club.slug
    assert abs(club_data['lat'] - sample_club.lat) < 0.001
    assert abs(club_data['lng'] - sample_club.lng) < 0.001
    assert 'members' in club_data
    assert 'upcoming' in club_data
    assert 'url' in club_data
    assert club_data['is_member'] is False


def test_map_data_member_flag(client, app, sample_club, regular_user):
    """is_member flag is True for clubs the logged-in user has joined."""
    from app.models import ClubMembership
    from app.extensions import db
    db.session.add(ClubMembership(user_id=regular_user.id, club_id=sample_club.id))
    db.session.commit()

    login(client)
    resp = client.get('/api/clubs/map-data')
    data = resp.get_json()
    assert data[0]['is_member'] is True


def test_map_data_inactive_club_excluded(client, sample_club):
    """Inactive clubs are not included in map data."""
    sample_club.is_active = False
    from app.extensions import db
    db.session.commit()

    resp = client.get('/api/clubs/map-data')
    data = resp.get_json()
    assert all(c['id'] != sample_club.id for c in data)


def test_map_data_upcoming_count(client, sample_club, sample_rides):
    """upcoming count reflects non-cancelled future rides for the club."""
    resp = client.get('/api/clubs/map-data')
    data = resp.get_json()
    assert len(data) == 1
    # sample_rides has 2 non-cancelled future rides
    assert data[0]['upcoming'] == 2
