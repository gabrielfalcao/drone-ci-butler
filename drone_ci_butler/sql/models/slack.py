import json
import io
import requests
from chemist import Model, db
from datetime import datetime
from drone_ci_butler.drone_api.models import Build, Output
from .base import metadata
from .exceptions import BuildNotFound


class SlackMessage(Model):
    table = db.Table(
        "slack_message",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("channel", db.Unicode(255)),
        db.Column("ts", db.Numeric),
        db.Column("ok", db.Boolean),
        db.Column("message", db.UnicodeText),
        db.Column("sender", db.Unicode(255)),
    )
