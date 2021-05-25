"""http-cache

Revision ID: 1c250c505256
Revises:
Create Date: 2021-05-23 14:50:49.425069

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = "1c250c505256"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "http_interaction",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("request_url", sa.String(255), nullable=False, unique=True),
        sa.Column("request_method", sa.String(10), nullable=False),
        sa.Column("request_headers", sa.UnicodeText()),
        sa.Column("request_params", sa.UnicodeText()),
        sa.Column("request_body", sa.UnicodeText()),
        sa.Column("response_status", sa.Integer),
        sa.Column("response_headers", sa.UnicodeText()),
        sa.Column("response_body", sa.UnicodeText()),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime, default=datetime.utcnow),
    )


def downgrade():
    op.drop_table("http_interaction")
