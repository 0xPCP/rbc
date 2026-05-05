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


def send_membership_approved(user, club):
    """Notify a user that their membership request was approved."""
    if not user.email:
        return
    html = render_template('email/membership_approved.html', club=club)
    text = render_template('email/membership_approved.txt', club=club)
    _send(f'Membership Approved — {club.name}', [user.email], html, text)
    logger.info('Membership approved email sent to %s for club %d', user.email, club.id)


def send_membership_rejected(user, club):
    """Notify a user that their membership request was rejected."""
    if not user.email:
        return
    html = render_template('email/membership_rejected.html', club=club)
    text = render_template('email/membership_rejected.txt', club=club)
    _send(f'Membership Request — {club.name}', [user.email], html, text)
    logger.info('Membership rejected email sent to %s for club %d', user.email, club.id)


def send_new_ride_notification(ride):
    """
    Notify all club members when a new ride is created.
    Called when an admin creates a new (non-recurring-instance) ride.
    """
    from .models import ClubMembership
    memberships = ClubMembership.query.filter_by(club_id=ride.club_id, status='active').all()
    recipients = [m.user.email for m in memberships if m.user.email]
    if not recipients:
        return
    html = render_template('email/new_ride.html', ride=ride)
    text = render_template('email/new_ride.txt', ride=ride)
    subject = f'New Ride: {ride.title} — {ride.club.name}'
    _send(subject, recipients, html, text)
    logger.info('New ride notification sent for ride %d to %d recipient(s)', ride.id, len(recipients))


def send_waitlist_promoted(signup):
    """Notify a user they've been promoted from the waitlist to confirmed."""
    ride = signup.ride
    user = signup.user
    if not user.email:
        return
    html = render_template('email/waitlist_promoted.html', ride=ride)
    text = render_template('email/waitlist_promoted.txt', ride=ride)
    subject = f"You're off the waitlist — {ride.title}"
    _send(subject, [user.email], html, text)
    logger.info('Waitlist promotion email sent to %s for ride %d', user.email, ride.id)


def send_invite_email(invite):
    """Send a club membership invite to the specified email address."""
    from flask import url_for
    claim_url = url_for('clubs.invite_claim', token=invite.token, _external=True)
    html = render_template('email/invite.html', invite=invite, claim_url=claim_url)
    text = render_template('email/invite.txt', invite=invite, claim_url=claim_url)
    subject = f"You're invited to join {invite.club.name}"
    _send(subject, [invite.email], html, text)
    logger.info('Invite email sent to %s for club %d', invite.email, invite.club_id)


def send_import_welcome_email(invite):
    """
    Send a new-account welcome email to a user created via bulk import.
    Includes a link to set their password and activate their Paceline account.
    """
    from flask import url_for
    setup_url = url_for('auth.setup_account', token=invite.token, _external=True)
    html = render_template('email/import_welcome.html', invite=invite, setup_url=setup_url)
    text = render_template('email/import_welcome.txt', invite=invite, setup_url=setup_url)
    subject = f"Welcome to {invite.club.name} — set up your Paceline account"
    _send(subject, [invite.email], html, text)
    logger.info('Import welcome email sent to %s for club %d', invite.email, invite.club_id)


def send_import_invite_email(invite):
    """
    Notify an existing Paceline user that a club admin has added them to a club.
    They must click to confirm before being added.
    """
    from flask import url_for
    claim_url = url_for('clubs.invite_claim', token=invite.token, _external=True)
    html = render_template('email/import_invite.html', invite=invite, claim_url=claim_url)
    text = render_template('email/import_invite.txt', invite=invite, claim_url=claim_url)
    subject = f"You've been added to {invite.club.name} on Paceline"
    _send(subject, [invite.email], html, text)
    logger.info('Import invite email sent to %s for club %d', invite.email, invite.club_id)


def send_weekly_digest(club, rides):
    """
    Send the Sunday weekly digest to all active club members.
    `rides` is the list of upcoming rides for the next 7 days, pre-queried by the caller.
    """
    from .models import ClubMembership
    memberships = ClubMembership.query.filter_by(club_id=club.id, status='active').all()
    recipients = [m.user.email for m in memberships if m.user.email]
    if not recipients:
        return
    html = render_template('email/weekly_digest.html', club=club, rides=rides)
    text = render_template('email/weekly_digest.txt', club=club, rides=rides)
    subject = f"This week's rides — {club.name}"
    _send(subject, recipients, html, text)
    logger.info('Weekly digest sent for club %d (%s) to %d recipient(s)', club.id, club.name, len(recipients))


def send_feedback_notification(feedback):
    """Notify superadmins that new site feedback was submitted."""
    from .admin_stats import configured_superadmin_emails
    from .models import User

    configured = configured_superadmin_emails()
    active_admins = User.query.filter_by(is_admin=True, is_active=True).all()
    recipients = sorted({
        email
        for email in configured | {user.email for user in active_admins if user.email}
        if email
    })
    if not recipients:
        return
    html = render_template('email/feedback_notification.html', feedback=feedback)
    text = render_template('email/feedback_notification.txt', feedback=feedback)
    _send('New Paceline feedback received', recipients, html, text)
    logger.info('Feedback notification sent for feedback %d to %d recipient(s)', feedback.id, len(recipients))
