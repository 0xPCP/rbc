"""Small runtime schema guards for deployments without Alembic."""
from flask import current_app
from sqlalchemy import inspect, text

from .extensions import db


def _configured_superadmin_emails():
    raw = current_app.config.get('SUPERADMIN_EMAILS', '')
    return {
        email.strip().lower()
        for email in raw.split(',')
        if email.strip()
    }


def ensure_runtime_schema():
    """Apply additive schema fixes required by current code.

    The project currently uses db.create_all() instead of Alembic migrations.
    create_all() does not add columns to existing tables, so keep this limited
    to safe additive changes needed by deployed dev databases.
    """
    inspector = inspect(db.engine)
    if 'users' not in inspector.get_table_names():
        return

    user_columns = {col['name'] for col in inspector.get_columns('users')}
    changed = False

    if 'session_token_version' not in user_columns:
        ddl = 'ALTER TABLE users ADD COLUMN session_token_version INTEGER NOT NULL DEFAULT 0'
        db.session.execute(text(ddl))
        changed = True

    if 'admin_audit_logs' not in inspector.get_table_names():
        from .models import AdminAuditLog
        AdminAuditLog.__table__.create(db.engine, checkfirst=True)
        changed = True

    superadmin_emails = _configured_superadmin_emails()
    if superadmin_emails:
        from .models import User
        users = User.query.filter(User.email.in_(superadmin_emails)).all()
        for user in users:
            if not user.is_admin:
                user.is_admin = True
                changed = True

    if changed:
        db.session.commit()
