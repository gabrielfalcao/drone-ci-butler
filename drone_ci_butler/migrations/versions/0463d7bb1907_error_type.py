"""error_type

Revision ID: 0463d7bb1907
Revises: c0c22e1a7fe6
Create Date: 2021-06-18 02:33:35.593421

"""
from alembic import op
import sqlalchemy as db
from datetime import datetime


# revision identifiers, used by Alembic.
revision = "0463d7bb1907"
down_revision = "c0c22e1a7fe6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "drone_build",
        db.Column("error_type", db.Unicode(100)),
    )


def downgrade():
    op.drop_column("drone_build", "error_type")
