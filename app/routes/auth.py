from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..extensions import db, bcrypt
from ..models import User
from ..forms import RegisterForm, LoginForm

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


@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')
