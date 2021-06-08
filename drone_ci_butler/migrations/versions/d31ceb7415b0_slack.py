"""slack

Revision ID: d31ceb7415b0
Revises: 3eeb5b329f73
Create Date: 2021-06-08 16:23:19.595135

"""
from alembic import op
import sqlalchemy as db


# revision identifiers, used by Alembic.
revision = "d31ceb7415b0"
down_revision = "3eeb5b329f73"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "slack_message",
        db.Column("id", db.Integer, primary_key=True),
        db.Column("channel", db.Unicode(255)),
        db.Column("ts", db.Numeric),
        db.Column("ok", db.Boolean),
        db.Column("message", db.UnicodeText),
        db.Column("sender", db.Unicode(255)),
    )


def downgrade():
    op.drop_table("slack_message")
