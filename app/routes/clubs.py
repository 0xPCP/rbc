import calendar as cal_module
from datetime import date, datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, Response
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
import requests as http_requests
from ..extensions import db
from ..models import Club, ClubMembership, Ride
from ..weather import get_weather_for_rides
from ..geocoding import clubs_near_zip
from .strava import get_club_activities

clubs_bp = Blueprint('clubs', __name__)


def _get_club_or_404(slug):
    return Club.query.filter_by(slug=slug, is_active=True).first_or_404()


# ── Club directory ────────────────────────────────────────────────────────────

@clubs_bp.route('/')
def index():
    q        = request.args.get('q', '').strip()
    zip_q    = request.args.get('zip', '').strip()
    radius   = request.args.get('radius', '25')
    try:
        radius = int(radius)
        if radius not in (10, 25, 50, 100):
            radius = 25
    except ValueError:
        radius = 25

    all_clubs = Club.query.filter_by(is_active=True).order_by(Club.name.asc()).all()

    # Zip-based proximity search takes priority over text search
    zip_results = None
    geo_error   = None
    if zip_q:
        zip_results, geo_error = clubs_near_zip(zip_q, all_clubs, radius_miles=radius)
        clubs = [c for c, _ in zip_results]
        distances = {c.id: d for c, d in zip_results}
    else:
        distances = {}
        if q:
            clubs = [c for c in all_clubs if
                     q.lower() in c.name.lower() or
                     q.lower() in (c.city or '').lower() or
                     q.lower() in (c.state or '').lower() or
                     q.lower() in (c.zip_code or '').lower()]
        else:
            clubs = all_clubs

    return render_template('clubs/index.html', clubs=clubs, q=q,
                           zip_q=zip_q, radius=radius, distances=distances,
                           geo_error=geo_error)


@clubs_bp.route('/map/')
def club_map():
    return render_template('clubs/map.html')


# ── Club home ─────────────────────────────────────────────────────────────────

@clubs_bp.route('/<slug>/')
def home(slug):
    club = _get_club_or_404(slug)
    today = date.today()
    upcoming = (Ride.query
                .filter_by(club_id=club.id, is_cancelled=False)
                .filter(Ride.date >= today)
                .order_by(Ride.date.asc(), Ride.time.asc())
                .limit(5).all())
    weather = get_weather_for_rides(upcoming)
    is_member = (current_user.is_authenticated and
                 current_user.is_member_of(club))
    strava_activities = get_club_activities(club.strava_club_id)
    return render_template('clubs/home.html', club=club, upcoming=upcoming,
                           weather=weather, is_member=is_member, today=today,
                           strava_activities=strava_activities)


# ── Club calendar ─────────────────────────────────────────────────────────────

@clubs_bp.route('/<slug>/rides/')
def rides(slug):
    club = _get_club_or_404(slug)
    view = request.args.get('view', 'list')
    if view == 'month':
        return _month_view(club)
    if view == 'week':
        return _week_view(club)
    return _list_view(club)


def _list_view(club):
    today = date.today()
    pace = request.args.get('pace', '')
    query = (Ride.query
             .filter_by(club_id=club.id)
             .filter(Ride.date >= today)
             .order_by(Ride.date.asc(), Ride.time.asc()))
    if pace in ('A', 'B', 'C', 'D'):
        query = query.filter(Ride.pace_category == pace)
    rides = query.all()
    weather = get_weather_for_rides(rides)
    return render_template('clubs/calendar_list.html', club=club, rides=rides,
                           active_pace=pace, weather=weather, today=today, view='list')


def _month_view(club):
    today = date.today()
    try:
        year  = int(request.args.get('y', today.year))
        month = int(request.args.get('m', today.month))
        year  = max(2020, min(year, 2035))
        month = max(1, min(month, 12))
    except (ValueError, TypeError):
        year, month = today.year, today.month

    pm = month - 1 or 12
    py = year - (1 if month == 1 else 0)
    nm = month % 12 + 1
    ny = year + (1 if month == 12 else 0)

    c = cal_module.Calendar(firstweekday=0)
    month_dates = c.monthdatescalendar(year, month)
    range_start = month_dates[0][0]
    range_end   = month_dates[-1][-1]

    rides_in_range = (Ride.query
                      .filter_by(club_id=club.id)
                      .filter(Ride.date >= range_start, Ride.date <= range_end)
                      .order_by(Ride.time.asc()).all())
    rides_by_date = {}
    for r in rides_in_range:
        rides_by_date.setdefault(r.date, []).append(r)

    weeks = []
    for week in month_dates:
        days = []
        for d in week:
            days.append({'date': d, 'other_month': d.month != month,
                         'is_today': d == today, 'rides': rides_by_date.get(d, [])})
        weeks.append(days)

    weather = get_weather_for_rides(rides_in_range)
    return render_template('clubs/calendar_month.html', club=club,
                           year=year, month=month,
                           month_name=cal_module.month_name[month],
                           weeks=weeks, today=today,
                           prev={'y': py, 'm': pm}, next={'y': ny, 'm': nm},
                           weather=weather, view='month')


def _week_view(club):
    today = date.today()
    default_start = today - timedelta(days=today.weekday())
    try:
        raw = request.args.get('start', default_start.isoformat())
        week_start = date.fromisoformat(raw)
        week_start = week_start - timedelta(days=week_start.weekday())
    except (ValueError, TypeError):
        week_start = default_start

    week_end   = week_start + timedelta(days=6)
    prev_start = week_start - timedelta(weeks=1)
    next_start = week_start + timedelta(weeks=1)

    rides_in_range = (Ride.query
                      .filter_by(club_id=club.id)
                      .filter(Ride.date >= week_start, Ride.date <= week_end)
                      .order_by(Ride.date.asc(), Ride.time.asc()).all())
    rides_by_date = {}
    for r in rides_in_range:
        rides_by_date.setdefault(r.date, []).append(r)

    days = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        days.append({'date': d, 'is_today': d == today, 'rides': rides_by_date.get(d, [])})

    weather = get_weather_for_rides(rides_in_range)
    return render_template('clubs/calendar_week.html', club=club,
                           week_start=week_start, week_end=week_end,
                           days=days, today=today,
                           prev_start=prev_start, next_start=next_start,
                           weather=weather, view='week')


# ── Ride detail & signups ─────────────────────────────────────────────────────

@clubs_bp.route('/<slug>/rides/<int:ride_id>')
def ride_detail(slug, ride_id):
    club = _get_club_or_404(slug)
    ride = Ride.query.filter_by(id=ride_id, club_id=club.id).first_or_404()

    user_signed_up = False
    waiver_required = False
    if current_user.is_authenticated:
        from ..models import RideSignup
        user_signed_up = RideSignup.query.filter_by(
            ride_id=ride_id, user_id=current_user.id
        ).first() is not None
        if club.current_waiver and not current_user.has_signed_waiver(club):
            waiver_required = True

    weather = get_weather_for_rides([ride])
    return render_template('clubs/ride_detail.html', club=club, ride=ride,
                           user_signed_up=user_signed_up,
                           waiver_required=waiver_required,
                           ride_weather=weather.get(ride.id))


@clubs_bp.route('/<slug>/rides/<int:ride_id>/ics')
def ride_ics(slug, ride_id):
    club = _get_club_or_404(slug)
    ride = Ride.query.filter_by(id=ride_id, club_id=club.id).first_or_404()

    dt_start = datetime.combine(ride.date, ride.time)
    dt_end   = dt_start + timedelta(hours=2)
    dt_stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    desc_parts = [f'Pace: {ride.pace_label}', f'Distance: {ride.distance_miles} mi']
    if ride.elevation_feet:
        desc_parts.append(f'Elevation: {ride.elevation_feet} ft')
    if ride.ride_leader:
        desc_parts.append(f'Leader: {ride.ride_leader}')
    if ride.description:
        desc_parts.append(ride.description)
    description = '\\n'.join(desc_parts)

    ics = (
        'BEGIN:VCALENDAR\r\n'
        'VERSION:2.0\r\n'
        'PRODID:-//Cycling Clubs//cyclingclub.pcp.dev//EN\r\n'
        'CALSCALE:GREGORIAN\r\n'
        'METHOD:PUBLISH\r\n'
        'BEGIN:VEVENT\r\n'
        f'UID:ride-{ride.id}@cyclingclub.pcp.dev\r\n'
        f'DTSTAMP:{dt_stamp}\r\n'
        f'DTSTART:{dt_start.strftime("%Y%m%dT%H%M%S")}\r\n'
        f'DTEND:{dt_end.strftime("%Y%m%dT%H%M%S")}\r\n'
        f'SUMMARY:{ride.title} — {club.name}\r\n'
        f'DESCRIPTION:{description}\r\n'
        f'LOCATION:{ride.meeting_location}\r\n'
        'END:VEVENT\r\n'
        'END:VCALENDAR\r\n'
    )

    filename = f'ride-{ride.id}.ics'
    return Response(
        ics,
        mimetype='text/calendar',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@clubs_bp.route('/<slug>/rides/<int:ride_id>/gpx')
def ride_gpx(slug, ride_id):
    club = _get_club_or_404(slug)
    ride = Ride.query.filter_by(id=ride_id, club_id=club.id).first_or_404()

    if not ride.ridewithgps_route_id:
        abort(404)

    gpx_url = f'https://ridewithgps.com/routes/{ride.ridewithgps_route_id}.gpx'
    try:
        upstream = http_requests.get(gpx_url, timeout=15,
                                     headers={'User-Agent': 'CyclingClubsApp/1.0'})
        if upstream.status_code != 200:
            abort(404)
    except http_requests.RequestException:
        abort(503)

    safe_title = ''.join(c if c.isalnum() or c in '-_ ' else '' for c in ride.title)
    filename = safe_title.strip().lower().replace(' ', '-') + '.gpx'
    return Response(
        upstream.content,
        mimetype='application/gpx+xml',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@clubs_bp.route('/<slug>/rides/<int:ride_id>/signup', methods=['POST'])
@login_required
def ride_signup(slug, ride_id):
    club = _get_club_or_404(slug)
    ride = Ride.query.filter_by(id=ride_id, club_id=club.id).first_or_404()

    if ride.is_cancelled:
        flash('This ride has been cancelled.', 'warning')
        return redirect(url_for('clubs.ride_detail', slug=slug, ride_id=ride_id))

    if club.current_waiver and not current_user.has_signed_waiver(club):
        flash('Please accept the club waiver before signing up for rides.', 'warning')
        return redirect(url_for('clubs.waiver', slug=slug, next=request.url))

    from ..models import RideSignup
    from sqlalchemy.exc import IntegrityError
    db.session.add(RideSignup(ride_id=ride_id, user_id=current_user.id))
    try:
        db.session.commit()
        flash("You're signed up! See you on the road.", 'success')
    except IntegrityError:
        db.session.rollback()
        flash('You are already signed up for this ride.', 'info')
    return redirect(url_for('clubs.ride_detail', slug=slug, ride_id=ride_id))


@clubs_bp.route('/<slug>/rides/<int:ride_id>/unsignup', methods=['POST'])
@login_required
def ride_unsignup(slug, ride_id):
    club = _get_club_or_404(slug)
    ride = Ride.query.filter_by(id=ride_id, club_id=club.id).first_or_404()
    from ..models import RideSignup
    s = RideSignup.query.filter_by(ride_id=ride_id, user_id=current_user.id).first()
    if s:
        db.session.delete(s)
        db.session.commit()
        flash("You've been removed from this ride.", 'info')
    return redirect(url_for('clubs.ride_detail', slug=slug, ride_id=ride_id))


# ── Club membership ───────────────────────────────────────────────────────────

@clubs_bp.route('/<slug>/join', methods=['POST'])
@login_required
def join(slug):
    club = _get_club_or_404(slug)
    db.session.add(ClubMembership(user_id=current_user.id, club_id=club.id))
    try:
        db.session.commit()
        flash(f"You've joined {club.name}!", 'success')
    except IntegrityError:
        db.session.rollback()
    return redirect(url_for('clubs.home', slug=slug))


@clubs_bp.route('/<slug>/leave', methods=['POST'])
@login_required
def leave(slug):
    club = _get_club_or_404(slug)
    m = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club.id).first()
    if m:
        db.session.delete(m)
        db.session.commit()
        flash(f"You've left {club.name}.", 'info')
    return redirect(url_for('clubs.home', slug=slug))


# ── Waiver ────────────────────────────────────────────────────────────────────

@clubs_bp.route('/<slug>/waiver', methods=['GET', 'POST'])
@login_required
def waiver(slug):
    club = _get_club_or_404(slug)
    waiver_obj = club.current_waiver
    if not waiver_obj:
        flash('This club has no waiver on file.', 'info')
        return redirect(url_for('clubs.home', slug=slug))

    next_url = request.args.get('next') or url_for('clubs.rides', slug=slug)

    if request.method == 'POST':
        if request.form.get('agree') == '1':
            from ..models import WaiverSignature
            from datetime import datetime, timezone
            year = datetime.now(timezone.utc).year
            if not current_user.has_signed_waiver(club, year):
                db.session.add(WaiverSignature(
                    user_id=current_user.id, club_id=club.id,
                    waiver_id=waiver_obj.id, year=year
                ))
                db.session.commit()
            flash('Waiver accepted. Welcome!', 'success')
            return redirect(next_url)
        flash('You must check the box to accept the waiver.', 'danger')

    already_signed = current_user.has_signed_waiver(club)
    return render_template('clubs/waiver.html', club=club, waiver=waiver_obj,
                           already_signed=already_signed, next_url=next_url)
