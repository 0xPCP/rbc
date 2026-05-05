from werkzeug.datastructures import MultiDict

from app.forms import ClubSettingsForm
from app.models import Club


def test_csp_uses_script_nonce_without_unsafe_inline(client):
    resp = client.get('/')
    csp = resp.headers['Content-Security-Policy']
    script_src = next(part for part in csp.split(';') if part.strip().startswith('script-src'))
    assert "'nonce-" in script_src
    assert "'unsafe-inline'" not in script_src


def test_css_injection_url_rejected_by_safe_url(app):
    payload = "https://example.com/a');background-image:url(javascript:alert(1));/*"
    with app.test_request_context('/'):
        form = ClubSettingsForm(
            formdata=MultiDict({'name': 'Club', 'banner_url': payload, 'join_approval': 'auto'}),
            meta={'csrf': False},
        )
        assert not form.validate()
        assert form.banner_url.errors


def test_banner_url_renders_as_img_src_not_inline_css(client, db, sample_club, mock_weather):
    sample_club.banner_url = 'https://example.com/banner.jpg'
    db.session.commit()

    resp = client.get(f'/clubs/{sample_club.slug}/')
    assert resp.status_code == 200
    assert b'background-image:url' not in resp.data
    assert b'<img src="https://example.com/banner.jpg"' in resp.data
