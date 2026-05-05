"""Small runtime schema guards for deployments without Alembic."""
from sqlalchemy import inspect, text

from .extensions import db


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
    if 'session_token_version' in user_columns:
        return

    dialect = db.engine.dialect.name
    if dialect == 'postgresql':
        ddl = 'ALTER TABLE users ADD COLUMN session_token_version INTEGER NOT NULL DEFAULT 0'
    else:
        ddl = 'ALTER TABLE users ADD COLUMN session_token_version INTEGER NOT NULL DEFAULT 0'
    db.session.execute(text(ddl))
    db.session.commit()
