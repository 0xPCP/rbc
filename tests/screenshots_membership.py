"""
Membership workflow screenshots against a local Flask test server.
Run: python tests/screenshots_membership.py
"""
import os
import sys
import threading
import time as _time
from datetime import date, timedelta, time as dtime

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from playwright.sync_api import sync_playwright
from app import create_app
from app.extensions import db as _db, bcrypt as _bcrypt
from app.models import (User, Club, ClubMembership, ClubAdmin,
                        ClubWaiver, Ride, RideSignup)

OUT  = os.path.join(os.path.dirname(__file__), 'screenshots')
DB_PATH = os.path.join(os.path.dirname(__file__), '_membership_screenshots.db')
PORT = 5098
BASE = f'http://127.0.0.1:{PORT}'
os.makedirs(OUT, exist_ok=True)


class Cfg:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'screenshot-secret'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STRAVA_CLIENT_ID = None
    STRAVA_CLIENT_SECRET = None
    STRAVA_CLUB_ID = None
    STRAVA_CLUB_REFRESH_TOKEN = None


# ── Seed ──────────────────────────────────────────────────────────────────────
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

app = create_app(Cfg)

with app.app_context():
    _db.create_all()

    pw123 = _bcrypt.generate_password_hash('password123').decode()
    pw    = _bcrypt.generate_password_hash('password').decode()

    admin   = User(username='testadmin', email='test@pcp.dev',             password_hash=pw)
    jsmith  = User(username='jsmith',    email='john.smith@example.com',   password_hash=pw123)
    nvcc_a  = User(username='nvcc_admin', email='admin@nvcc.dev',          password_hash=pw123)
    _db.session.add_all([admin, jsmith, nvcc_a])
    _db.session.flush()

    today = date.today()
    nxt   = today + timedelta(days=7 - today.weekday())

    rbc = Club(
        slug='rbc', name='Reston Bike Club',
        city='Reston', state='VA', zip_code='20191',
        lat=38.9376, lng=-77.3476,
        require_membership=False,
    )
    nvcc = Club(
        slug='nvcc', name='Northern Virginia Cycling Club',
        city='McLean', state='VA', zip_code='22101',
        lat=38.9339, lng=-77.1773,
        is_private=True, require_membership=True, join_approval='manual',
        theme_primary='#1a5276', theme_accent='#f39c12',
    )
    _db.session.add_all([rbc, nvcc])
    _db.session.flush()

    _db.session.add(ClubAdmin(user_id=admin.id, club_id=rbc.id,  role='admin'))
    _db.session.add(ClubAdmin(user_id=nvcc_a.id, club_id=nvcc.id, role='admin'))
    _db.session.add(ClubMembership(user_id=admin.id,  club_id=rbc.id,  status='active'))
    _db.session.add(ClubMembership(user_id=nvcc_a.id, club_id=nvcc.id, status='active'))

    rides = [
        Ride(club_id=rbc.id, title='Tuesday A Ride',
             date=nxt + timedelta(1), time=dtime(17,0),
             meeting_location='Hunterwoods', distance_miles=38, pace_category='A',
             route_url='https://ridewithgps.com/routes/35103917'),
        Ride(club_id=nvcc.id, title='Thursday Night Worlds',
             date=nxt + timedelta(3), time=dtime(18,0),
             meeting_location='McLean CC', distance_miles=32, pace_category='A',
             route_url='https://ridewithgps.com/routes/35103917'),
    ]
    for r in rides:
        _db.session.add(r)
    _db.session.commit()

    rbc_ride_id  = rides[0].id
    nvcc_ride_id = rides[1].id
    rbc_slug     = rbc.slug
    nvcc_slug    = nvcc.slug

# ── Start server ──────────────────────────────────────────────────────────────
t = threading.Thread(
    target=lambda: app.run(host='127.0.0.1', port=PORT, use_reloader=False, threaded=True),
    daemon=True,
)
t.start()
_time.sleep(1.0)


def shot(page, name):
    path = os.path.join(OUT, f'membership_{name}.png')
    page.screenshot(path=path, full_page=False)
    print(f'  saved: {os.path.basename(path)}')


def login(page, email, password='password123'):
    page.goto(f'{BASE}/auth/login')
    page.wait_for_selector('input[name=email]')
    page.fill('input[name=email]', email)
    page.fill('input[name=password]', password)
    page.click('input[type=submit]')
    page.wait_for_load_state('networkidle')


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # 1. Anonymous user visits NVCC (private club with manual approval)
    print('1. Anonymous user visits NVCC private club...')
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    page.goto(f'{BASE}/clubs/{nvcc_slug}/')
    page.wait_for_selector('h1')
    shot(page, '01_nvcc_anonymous')
    page.close()

    # 2. jsmith visits NVCC and sees Join Club button
    print('2. jsmith (non-member) visits NVCC — sees Join button...')
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    login(page, 'john.smith@example.com', 'password123')
    page.goto(f'{BASE}/clubs/{nvcc_slug}/')
    page.wait_for_selector('h1')
    shot(page, '02_nvcc_nonmember_sees_join_button')

    # 3. jsmith clicks Join Club (creates pending membership)
    print('3. jsmith requests to join NVCC — pending approval...')
    page.click('form[action*="/join"] button')
    page.wait_for_load_state('networkidle')
    shot(page, '03_nvcc_pending_after_join_request')

    # 4. jsmith views NVCC ride detail — route hidden (private + pending)
    print('4. jsmith views NVCC ride detail — route hidden...')
    page.goto(f'{BASE}/clubs/{nvcc_slug}/rides/{nvcc_ride_id}')
    page.wait_for_selector('h1')
    shot(page, '04_nvcc_ride_detail_route_hidden_nonmember')
    page.close()

    # 5. NVCC admin views team page — pending requests visible
    print('5. NVCC admin views team page with pending request...')
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    login(page, 'admin@nvcc.dev', 'password123')
    page.goto(f'{BASE}/admin/clubs/{nvcc_slug}/team')
    page.wait_for_selector('h1')
    shot(page, '05_nvcc_team_page_pending_requests')
    page.close()

    # 6. test@pcp.dev views RBC club settings — membership section
    print('6. RBC admin (test@pcp.dev) views club settings — membership section...')
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    login(page, 'test@pcp.dev', 'password')
    page.goto(f'{BASE}/admin/clubs/{rbc_slug}/settings')
    page.wait_for_selector('h1')
    page.evaluate("""
        const hs = document.querySelectorAll('h5');
        for (const h of hs) { if (h.textContent.includes('Membership')) { h.scrollIntoView(); break; } }
    """)
    _time.sleep(0.3)
    shot(page, '06_rbc_settings_membership_section')
    page.close()

    # 7. RBC admin dashboard
    print('7. RBC admin dashboard (test@pcp.dev)...')
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    login(page, 'test@pcp.dev', 'password')
    page.goto(f'{BASE}/admin/clubs/{rbc_slug}/')
    page.wait_for_selector('h1')
    shot(page, '07_rbc_admin_dashboard')
    page.close()

    # 8. NVCC admin approves jsmith
    print('8. NVCC admin approves jsmith...')
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    login(page, 'admin@nvcc.dev', 'password123')
    page.goto(f'{BASE}/admin/clubs/{nvcc_slug}/team')
    page.wait_for_selector('h1')
    # Click Approve button
    approve_btn = page.locator('button:has-text("Approve")')
    if approve_btn.count() > 0:
        approve_btn.first.click()
        page.wait_for_load_state('networkidle')
    shot(page, '08_nvcc_team_after_approval')
    page.close()

    # 9. jsmith now sees route after being approved
    print('9. jsmith revisits NVCC ride — now active member, route visible...')
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    login(page, 'john.smith@example.com', 'password123')
    page.goto(f'{BASE}/clubs/{nvcc_slug}/rides/{nvcc_ride_id}')
    page.wait_for_selector('h1')
    shot(page, '09_nvcc_ride_detail_route_visible_member')
    page.close()

    browser.close()

# Cleanup
try:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
except OSError:
    pass

print('\nDone! All screenshots saved to tests/screenshots/')
