from datetime import date, datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import (
    login_user, logout_user, login_required, current_user,
    login_fresh, fresh_login_required,
)
from flask_babel import gettext as _
from ..extensions import db, bcrypt
from ..models import User, Ride, RideSignup, ClubInvite
from ..forms import RegisterForm, LoginForm, ProfileForm, SetPasswordForm
from ..geocoding import geocode_zip
from ..gear import GEAR_CATALOG
from ..utils import is_safe_url

auth_bp = Blueprint('auth', __name__)


def _mark_interactive_login(trusted_browser=False):
    session.permanent = True
    session['_paceline_auth_started_at'] = datetime.now(timezone.utc).timestamp()
    session['_paceline_trusted_browser'] = bool(trusted_browser)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        # Check for existing email or username
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash(_('An account with that email already exists.'), 'danger')
            return render_template('auth/register.html', form=form)
        if User.query.filter_by(username=form.username.data).first():
            flash(_('That username is already taken.'), 'danger')
            return render_template('auth/register.html', form=form)

        hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        # First registered user becomes admin
        is_first_user = User.query.count() == 0
        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            password_hash=hashed,
            is_admin=is_first_user,
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        _mark_interactive_login()
        if is_first_user:
            flash(_('Account created — you have been granted admin access as the first user.'), 'success')
        else:
            flash(_('Welcome! Your account has been created.'), 'success')
        next_page = request.args.get('next')
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
        return redirect(url_for('main.index'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and login_fresh():
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash(_('This account has been deactivated. Please contact support.'), 'danger')
                return render_template('auth/login.html', form=form)
            trusted_browser = bool(form.remember.data)
            login_user(user, remember=trusted_browser)
            _mark_interactive_login(trusted_browser=trusted_browser)
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('main.index'))
        flash(_('Invalid email or password.'), 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/setup-account/<token>', methods=['GET', 'POST'])
def setup_account(token):
    """Password-setup landing page for users created via bulk import."""
    invite = ClubInvite.query.filter_by(token=token, is_new_user=True).first_or_404()

    if invite.used_at:
        flash('This setup link has already been used. Please sign in.', 'warning')
        return redirect(url_for('auth.login'))
    if invite.expires_at.replace(tzinfo=None) < datetime.now(timezone.utc).replace(tzinfo=None):
        flash('This setup link has expired. Ask your club admin to re-import your email.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=invite.email).first_or_404()

    # Already logged in as the right user — just mark done and send to club
    if current_user.is_authenticated:
        if current_user.id != user.id:
            flash('This setup link belongs to a different account.', 'warning')
            return redirect(url_for('main.index'))
        invite.used_at = datetime.now(timezone.utc)
        invite.used_by_user_id = user.id
        db.session.commit()
        return redirect(url_for('clubs.home', slug=invite.club.slug))

    form = SetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = bcrypt.generate_password_hash(
            form.password.data
        ).decode('utf-8')
        user.revoke_sessions()
        invite.used_at = datetime.now(timezone.utc)
        invite.used_by_user_id = user.id
        db.session.commit()
        login_user(user)
        _mark_interactive_login()
        flash(f"Welcome to {invite.club.name}! Your Paceline account is ready.", 'success')
        return redirect(url_for('clubs.home', slug=invite.club.slug))

    return render_template('auth/setup_account.html', form=form, invite=invite)


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    session.pop('_paceline_auth_started_at', None)
    session.pop('_paceline_trusted_browser', None)
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@fresh_login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # Check uniqueness for changed fields
        if form.username.data != current_user.username:
            if User.query.filter_by(username=form.username.data).first():
                flash(_('That username is already taken.'), 'danger')
                return redirect(url_for('auth.profile'))
        if form.email.data.lower() != current_user.email:
            if User.query.filter_by(email=form.email.data.lower()).first():
                flash(_('An account with that email already exists.'), 'danger')
                return redirect(url_for('auth.profile'))

        current_user.username  = form.username.data
        current_user.email     = form.email.data.lower()
        current_user.gender    = form.gender.data or None
        current_user.bio       = (form.bio.data or '').strip() or None
        current_user.language  = form.language.data or None
        current_user.emergency_contact_name  = (form.emergency_contact_name.data or '').strip() or None
        current_user.emergency_contact_phone = (form.emergency_contact_phone.data or '').strip() or None

        # Gear inventory — validate each submitted ID against the known catalog
        valid_gear_ids = {item['id'] for items in GEAR_CATALOG.values() for item in items}
        submitted_gear = [g for g in request.form.getlist('gear_items') if g in valid_gear_ids]
        current_user.gear_inventory = submitted_gear or None

        new_zip = (form.zip_code.data or '').strip()
        if new_zip != (current_user.zip_code or ''):
            current_user.zip_code = new_zip or None
            current_user.lat = None
            current_user.lng = None
            if new_zip:
                coords = geocode_zip(new_zip)
                if coords:
                    current_user.lat, current_user.lng = coords
                else:
                    flash(_('Zip code saved but could not be geocoded.'), 'warning')

        db.session.commit()
        flash(_('Profile updated.'), 'success')
        return redirect(url_for('auth.profile'))

    owned = set(current_user.gear_inventory or [])
    today = date.today()
    past_signups = (RideSignup.query
                    .filter_by(user_id=current_user.id, is_waitlist=False)
                    .join(Ride, RideSignup.ride_id == Ride.id)
                    .filter(Ride.date < today, Ride.is_cancelled == False)
                    .order_by(Ride.date.desc())
                    .all())
    ytd_signups = [s for s in past_signups if s.ride.date.year == today.year]
    ytd_stats = {
        'rides':     len(ytd_signups),
        'miles':     round(sum(s.ride.distance_miles for s in ytd_signups), 1),
        'elevation': sum(s.ride.elevation_feet or 0 for s in ytd_signups),
    }
    return render_template('profile.html', form=form,
                           gear_catalog=GEAR_CATALOG, owned_gear=owned,
                           past_signups=past_signups, ytd_stats=ytd_stats)
