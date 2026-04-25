from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..extensions import db, bcrypt
from ..models import User, Ride, RideSignup
from ..forms import RegisterForm, LoginForm, ProfileForm
from ..geocoding import geocode_zip
from ..gear import GEAR_CATALOG

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        # Check for existing email or username
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash('An account with that email already exists.', 'danger')
            return render_template('auth/register.html', form=form)
        if User.query.filter_by(username=form.username.data).first():
            flash('That username is already taken.', 'danger')
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

        if is_first_user:
            flash('Account created — you have been granted admin access as the first user.', 'success')
        else:
            flash('Account created! You can now sign in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # Check uniqueness for changed fields
        if form.username.data != current_user.username:
            if User.query.filter_by(username=form.username.data).first():
                flash('That username is already taken.', 'danger')
                return redirect(url_for('auth.profile'))
        if form.email.data.lower() != current_user.email:
            if User.query.filter_by(email=form.email.data.lower()).first():
                flash('An account with that email already exists.', 'danger')
                return redirect(url_for('auth.profile'))

        current_user.username = form.username.data
        current_user.email    = form.email.data.lower()
        current_user.emergency_contact_name  = (form.emergency_contact_name.data or '').strip() or None
        current_user.emergency_contact_phone = (form.emergency_contact_phone.data or '').strip() or None

        # Gear inventory — list of checked item IDs
        current_user.gear_inventory = request.form.getlist('gear_items') or None

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
                    flash('Zip code saved but could not be geocoded.', 'warning')

        db.session.commit()
        flash('Profile updated.', 'success')
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
