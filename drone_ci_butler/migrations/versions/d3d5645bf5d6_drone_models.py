"""drone models

Revision ID: d3d5645bf5d6
Revises: 1c250c505256
Create Date: 2021-05-31 18:19:45.470677

"""
from alembic import op
import sqlalchemy as db


# revision identifiers, used by Alembic.
revision = "d3d5645bf5d6"
down_revision = "1c250c505256"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "drone_build",
        db.Column("id", db.Integer, primary_key=True),
        db.Column("number", db.Integer, nullable=False),
        db.Column("status", db.String(255), nullable=False),
        db.Column("link", db.UnicodeText, nullable=False, index=True),
        db.Column("owner", db.Unicode(255), nullable=False),
        db.Column("repo", db.Unicode(255), nullable=False),
        db.Column("author_login", db.Unicode(255), nullable=False),
        db.Column("author_name", db.Unicode(255)),
        db.Column("author_email", db.Unicode(255)),
        db.Column("drone_api_data", db.UnicodeText),
        db.Column("created_at", db.DateTime),
        db.Column("started_at", db.DateTime),
        db.Column("finished_at", db.DateTime),
        db.Column("updated_at", db.DateTime),
    )
    op.create_table(
        "drone_step",
        db.Column("id", db.Integer, primary_key=True),
        db.Column("stored_build_id", db.Integer, index=True),
        db.Column("build_number", db.Integer, nullable=False),
        db.Column("stage_number", db.Integer, nullable=False),
        db.Column("number", db.Integer, nullable=False),
        db.Column("status", db.String(255)),
        db.Column("exit_code", db.Integer),
        db.Column("output_drone_api_data", db.UnicodeText),
        db.Column("started_at", db.DateTime),
        db.Column("stopped_at", db.DateTime),
        db.Column("updated_at", db.DateTime),
    )


def downgrade():
    op.drop_table("drone_step")
    op.drop_table("drone_build")
