import json
import io
import requests
from chemist import Model, db
from datetime import datetime
from .base import metadata
from .exceptions import BuildNotFound


class SlackMessage(Model):
    table = db.Table(
        "slack_message",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("channel", db.Unicode(255), index=True),
        db.Column("ts", db.Numeric),
        db.Column("ok", db.Boolean),
        db.Column("message", db.UnicodeText),
        db.Column("sender", db.Unicode(255)),
    )
