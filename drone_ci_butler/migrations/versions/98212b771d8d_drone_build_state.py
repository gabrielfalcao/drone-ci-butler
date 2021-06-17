"""drone_build_state

Revision ID: 98212b771d8d
Revises: da5094d9e8ea
Create Date: 2021-06-17 20:22:22.036395

"""
from alembic import op
import sqlalchemy as db
from datetime import datetime


# revision identifiers, used by Alembic.
revision = "98212b771d8d"
down_revision = "da5094d9e8ea"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "drone_build",
        db.Column("output_retrieved_at", db.DateTime),
    )


def downgrade():
    op.drop_column("drone_build", "output_retrieved_at")
