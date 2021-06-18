"""last_ruleset_processed_at

Revision ID: c0c22e1a7fe6
Revises: 98212b771d8d
Create Date: 2021-06-18 02:31:27.647788

"""
from alembic import op
import sqlalchemy as db
from datetime import datetime


# revision identifiers, used by Alembic.
revision = "c0c22e1a7fe6"
down_revision = "98212b771d8d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "drone_build",
        db.Column("last_ruleset_processed_at", db.DateTime),
    )
    op.add_column(
        "drone_build",
        db.Column("matches_json", db.UnicodeText),
    )


def downgrade():
    op.drop_column("drone_build", "matches_json")
    op.drop_column("drone_build", "last_ruleset_processed_at")
