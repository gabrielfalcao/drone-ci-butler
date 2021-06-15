"""drone_step_last_modified_at

Revision ID: da5094d9e8ea
Revises: d31ceb7415b0
Create Date: 2021-06-14 23:31:48.887441

"""
from alembic import op
import sqlalchemy as db
from datetime import datetime


# revision identifiers, used by Alembic.
revision = "da5094d9e8ea"
down_revision = "d31ceb7415b0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "drone_step",
        db.Column("last_notified_at", db.DateTime),
    )


def downgrade():
    op.drop_column("drone_step", "last_notified_at")
