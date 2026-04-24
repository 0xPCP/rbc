from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    TextAreaField, SelectField, FloatField, IntegerField, DateField, TimeField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL, NumberRange


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
    submit      = SubmitField('Save Settings')


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
    ride_leader = StringField('Ride Leader', validators=[Optional(), Length(max=100)])
    route_url = StringField('Route URL (Strava, RideWithGPS, etc.)', validators=[Optional(), URL(), Length(max=500)])
    video_url = StringField('Video URL (YouTube or Vimeo)', validators=[Optional(), URL(), Length(max=500)])
    description = TextAreaField('Description / Notes', validators=[Optional()])
    is_cancelled = BooleanField('Mark as Cancelled')
    is_recurring = BooleanField('Repeat weekly (generates 8 weeks of instances)')
    submit = SubmitField('Save Ride')
