import calendar as cal_module
from datetime import date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Club, ClubMembership, Ride
from ..weather import get_weather_for_rides

clubs_bp = Blueprint('clubs', __name__)


def _get_club_or_404(slug):
    return Club.query.filter_by(slug=slug, is_active=True).first_or_404()


# ── Club directory ────────────────────────────────────────────────────────────

@clubs_bp.route('/')
def index():
    q = request.args.get('q', '').strip()
    query = Club.query.filter_by(is_active=True)
    if q:
        query = query.filter(
            db.or_(Club.name.ilike(f'%{q}%'), Club.city.ilike(f'%{q}%'),
                   Club.state.ilike(f'%{q}%'), Club.zip_code.ilike(f'%{q}%'))
        )
    clubs = query.order_by(Club.name.asc()).all()
    return render_template('clubs/index.html', clubs=clubs, q=q)


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
    return render_template('clubs/home.html', club=club, upcoming=upcoming,
                           weather=weather, is_member=is_member, today=today)


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
