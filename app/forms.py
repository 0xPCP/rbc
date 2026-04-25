from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    TextAreaField, SelectField, FloatField, IntegerField, DateField, TimeField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL, NumberRange, Regexp


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 50)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')


class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 50)])
    email    = StringField('Email Address', validators=[DataRequired(), Email()])
    zip_code = StringField('Zip Code', validators=[Optional(), Length(max=10)])
    submit   = SubmitField('Save Changes')


class ClubForm(FlaskForm):
    name        = StringField('Club Name', validators=[DataRequired(), Length(max=200)])
    slug        = StringField('URL Slug', validators=[DataRequired(), Length(max=80)])
    description = TextAreaField('Description', validators=[Optional()])
    city        = StringField('City', validators=[Optional(), Length(max=100)])
    state       = StringField('State', validators=[Optional(), Length(max=50)])
    zip_code    = StringField('Zip Code', validators=[Optional(), Length(max=10)])
    address     = StringField('Address', validators=[Optional(), Length(max=500)])
    website     = StringField('Website', validators=[Optional(), URL(), Length(max=500)])
    contact_email = StringField('Contact Email', validators=[Optional(), Email(), Length(max=255)])
    logo_url    = StringField('Logo URL', validators=[Optional(), URL(), Length(max=500)])
    is_active   = BooleanField('Active (visible to users)', default=True)
    submit      = SubmitField('Save Club')


class ClubSettingsForm(FlaskForm):
    """Club admin version — no slug, no is_active."""
    name        = StringField('Club Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    city        = StringField('City', validators=[Optional(), Length(max=100)])
    state       = StringField('State', validators=[Optional(), Length(max=50)])
    zip_code    = StringField('Zip Code', validators=[Optional(), Length(max=10)])
    address     = StringField('Address', validators=[Optional(), Length(max=500)])
    website     = StringField('Website', validators=[Optional(), URL(), Length(max=500)])
    contact_email = StringField('Contact Email', validators=[Optional(), Email(), Length(max=255)])
    logo_url    = StringField('Logo URL', validators=[Optional(), URL(), Length(max=500)])
    # Appearance / theming
    theme_primary = StringField('Primary Color', validators=[
        Optional(), Length(max=7),
        Regexp(r'^#[0-9a-fA-F]{6}$', message='Enter a valid hex color (e.g. #3a7bd5).'),
    ])
    theme_accent  = StringField('Accent / Button Color', validators=[
        Optional(), Length(max=7),
        Regexp(r'^#[0-9a-fA-F]{6}$', message='Enter a valid hex color (e.g. #e76f51).'),
    ])
    banner_url    = StringField('Banner Image URL', validators=[Optional(), URL(), Length(max=500)])
    # Membership settings
    is_private         = BooleanField('Private Club')
    require_membership = BooleanField('Require membership to sign up for rides')
    join_approval = SelectField('Join Approval Mode', choices=[
        ('auto',   'Auto-approve — users join immediately upon request'),
        ('manual', 'Manual approval — admin must approve each request'),
    ])
    # Strava integration
    strava_club_id = StringField('Strava Club ID', validators=[Optional(), Length(max=20)])
    # Weather auto-cancel
    auto_cancel_enabled = BooleanField('Enable weather-based auto-cancel')
    cancel_rain_prob    = IntegerField('Cancel if rain probability ≥ (%)',
                                      validators=[Optional(), NumberRange(1, 100)], default=80)
    cancel_wind_mph     = IntegerField('Cancel if wind speed ≥ (mph)',
                                      validators=[Optional(), NumberRange(1, 200)], default=35)
    cancel_temp_min_f   = IntegerField('Cancel if temperature below (°F)',
                                      validators=[Optional(), NumberRange(-60, 120)], default=28)
    cancel_temp_max_f   = IntegerField('Cancel if temperature above (°F)',
                                      validators=[Optional(), NumberRange(-60, 150)], default=100)
    submit      = SubmitField('Save Settings')


class ClubCreateForm(FlaskForm):
    """Multi-step club creation wizard — submitted as a single POST."""
    name          = StringField('Club Name', validators=[DataRequired(), Length(max=200)])
    city          = StringField('City', validators=[Optional(), Length(max=100)])
    state         = StringField('State', validators=[Optional(), Length(max=50)])
    zip_code      = StringField('Zip Code', validators=[Optional(), Length(max=10)])
    is_private    = BooleanField('Private Club')
    # theme_preset is written by JS, validated as a string
    theme_preset  = StringField('Theme Preset', validators=[Optional(), Length(max=30)])
    theme_primary = StringField('Primary Color', validators=[
        Optional(), Length(max=7),
        Regexp(r'^#[0-9a-fA-F]{6}$', message='Enter a valid hex color (e.g. #3a7bd5).'),
    ])
    theme_accent  = StringField('Accent Color', validators=[
        Optional(), Length(max=7),
        Regexp(r'^#[0-9a-fA-F]{6}$', message='Enter a valid hex color (e.g. #e76f51).'),
    ])
    description   = TextAreaField('Description', validators=[Optional()])
    contact_email = StringField('Contact Email', validators=[Optional(), Email(), Length(max=255)])
    website       = StringField('Website URL', validators=[Optional(), URL(), Length(max=500)])
    logo_url      = StringField('Logo URL', validators=[Optional(), URL(), Length(max=500)])
    banner_url    = StringField('Banner Image URL', validators=[Optional(), URL(), Length(max=500)])
    submit        = SubmitField('Create Club')


class RideForm(FlaskForm):
    title = StringField('Ride Title', validators=[DataRequired(), Length(max=200)])
    date = DateField('Date', validators=[DataRequired()])
    time = TimeField('Start Time', validators=[DataRequired()])
    meeting_location = StringField('Meeting Location', validators=[DataRequired(), Length(max=500)])
    distance_miles = FloatField('Distance (miles)', validators=[DataRequired(), NumberRange(min=0.1)])
    elevation_feet = IntegerField('Elevation Gain (feet)', validators=[Optional()])
    pace_category = SelectField('Pace Category', choices=[
        ('A', 'A — Fast (22+ mph)'),
        ('B', 'B — Moderate (18–22 mph)'),
        ('C', 'C — Casual (14–18 mph)'),
        ('D', 'D — Beginner (<14 mph)'),
    ])
    ride_type = SelectField('Ride Type', choices=[
        ('', '— Any / Unspecified —'),
        ('road',     'Road'),
        ('gravel',   'Gravel'),
        ('social',   'Social'),
        ('training', 'Training'),
        ('event',    'Event'),
        ('night',    'Night Ride'),
    ], validators=[Optional()])
    ride_leader = StringField('Ride Leader', validators=[Optional(), Length(max=100)])
    route_url = StringField('Route URL (Strava, RideWithGPS, etc.)', validators=[Optional(), URL(), Length(max=500)])
    video_url = StringField('Video URL (YouTube or Vimeo)', validators=[Optional(), URL(), Length(max=500)])
    description = TextAreaField('Description / Notes', validators=[Optional()])
    max_riders = IntegerField('Max Riders (leave blank for unlimited)', validators=[Optional(), NumberRange(min=1, max=9999)])
    is_cancelled = BooleanField('Mark as Cancelled')
    is_recurring = BooleanField('Repeat weekly (generates 8 weeks of instances)')
    submit = SubmitField('Save Ride')
