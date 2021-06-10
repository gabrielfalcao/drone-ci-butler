"""auth

Revision ID: 3eeb5b329f73
Revises: d3d5645bf5d6
Create Date: 2021-06-08 16:18:19.344847

"""
from alembic import op
import sqlalchemy as db


# revision identifiers, used by Alembic.
revision = "3eeb5b329f73"
down_revision = "d3d5645bf5d6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_user",
        db.Column("id", db.Integer, primary_key=True),
        db.Column("email", db.String(100), nullable=False, unique=True),
        db.Column("password", db.Unicode(128)),
        db.Column("github_username", db.Unicode(255)),
        db.Column("github_email", db.Unicode(255)),
        db.Column("github_access_token", db.UnicodeText),
        db.Column("github_refresh_token", db.UnicodeText),
        db.Column("github_json", db.UnicodeText),
        db.Column("slack_username", db.Unicode(255)),
        db.Column("slack_email", db.Unicode(255)),
        db.Column("slack_access_token", db.UnicodeText),
        db.Column("slack_refresh_token", db.UnicodeText),
        db.Column("slack_json", db.UnicodeText),
        db.Column("settings_json", db.UnicodeText),
        db.Column("created_at", db.DateTime),
        db.Column("updated_at", db.DateTime),
        db.Column("github_activated_at", db.DateTime),
        db.Column("slack_activated_at", db.DateTime),
    )
    op.create_table(
        "auth_access_token",
        db.Column("id", db.Integer, primary_key=True),
        db.Column("identity_provider", db.Unicode(255)),
        db.Column("content", db.UnicodeText, nullable=False, unique=True),
        db.Column("refresh_token", db.UnicodeText),
        db.Column("scope", db.UnicodeText, nullable=True),
        db.Column(
            "created_at", db.Unicode(255), default=lambda: datetime.utcnow().isoformat()
        ),
        db.Column("duration", db.Integer),
        db.Column(
            "user_id",
            db.Integer,
            db.ForeignKey("auth_user.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_table("auth_access_token")
    op.drop_table("auth_user")
