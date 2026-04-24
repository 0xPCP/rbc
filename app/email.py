"""
Email notification helpers.

All send_* functions are fire-and-forget: they log errors but never raise,
so a mail failure never breaks a user-facing request or the scheduler.

MAIL_SERVER must be configured in the environment for emails to be sent.
When MAIL_SERVER is empty, Flask-Mail suppresses sending automatically.
"""
import logging
from flask import render_template, current_app
from flask_mail import Message
from .extensions import mail

logger = logging.getLogger(__name__)


def _send(subject, recipients, html_body, text_body=None):
    """Send a single message, swallowing all exceptions."""
    if not recipients:
        return
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            body=text_body or '',
        )
        mail.send(msg)
    except Exception as exc:
        logger.warning('Email send failed (%s): %s', subject, exc)


def send_cancellation_emails(ride):
    """
    Notify all signed-up riders that a ride has been cancelled.
    Called when ride.is_cancelled is set to True (manual or auto).
    """
    recipients = [s.user.email for s in ride.signups if s.user.email]
    if not recipients:
        return
    html = render_template('email/cancellation.html', ride=ride)
    text = render_template('email/cancellation.txt', ride=ride)
    subject = f'Ride Cancelled: {ride.title} — {ride.club.name}'
    _send(subject, recipients, html, text)
    logger.info('Cancellation emails sent for ride %d to %d recipient(s)', ride.id, len(recipients))


def send_ride_reminder(ride):
    """
    Send a morning-of reminder to all signed-up riders.
    Called by the scheduler at 6 AM on the day of the ride.
    """
    recipients = [s.user.email for s in ride.signups if s.user.email]
    if not recipients:
        return
    html = render_template('email/reminder.html', ride=ride)
    text = render_template('email/reminder.txt', ride=ride)
    subject = f"Today's Ride: {ride.title} — {ride.club.name}"
    _send(subject, recipients, html, text)
    logger.info('Reminder emails sent for ride %d to %d recipient(s)', ride.id, len(recipients))


def send_new_ride_notification(ride):
    """
    Notify all club members when a new ride is created.
    Called when an admin creates a new (non-recurring-instance) ride.
    """
    from .models import ClubMembership
    memberships = ClubMembership.query.filter_by(club_id=ride.club_id).all()
    recipients = [m.user.email for m in memberships if m.user.email]
    if not recipients:
        return
    html = render_template('email/new_ride.html', ride=ride)
    text = render_template('email/new_ride.txt', ride=ride)
    subject = f'New Ride: {ride.title} — {ride.club.name}'
    _send(subject, recipients, html, text)
    logger.info('New ride notification sent for ride %d to %d recipient(s)', ride.id, len(recipients))
