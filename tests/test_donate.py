def test_footer_shows_donate_link(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'href="/donate"' in resp.data
    assert b'Donate' in resp.data


def test_club_footer_shows_donate_link(client, sample_club):
    resp = client.get(f'/clubs/{sample_club.slug}/')
    assert resp.status_code == 200
    assert b'href="/donate"' in resp.data
    assert b'Donate' in resp.data


def test_donate_stub_page_without_config(client, app):
    app.config['DONATE_URL'] = ''
    resp = client.get('/donate')
    assert resp.status_code == 200
    assert b'Stripe donation link coming soon' in resp.data
    assert b'Donate with Stripe' in resp.data


def test_donate_redirects_to_configured_stripe_link(client, app):
    app.config['DONATE_URL'] = 'https://buy.stripe.com/test_donation'
    resp = client.get('/donate')
    assert resp.status_code == 302
    assert resp.headers['Location'] == 'https://buy.stripe.com/test_donation'


def test_donate_rejects_non_http_configured_url(client, app):
    app.config['DONATE_URL'] = 'javascript:alert(1)'
    resp = client.get('/donate')
    assert resp.status_code == 200
    assert b'Stripe donation link coming soon' in resp.data
