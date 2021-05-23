from chemist import (
    Model, db
)
from datetime import datetime
from .base import metadata



class HttpInteraction(Model):
    table = db.Table('http_interaction',metadata,
        db.Column('id', db.Integer, primary_key=True),

        db.Column('request_url', db.String(255), nullable=False, unique=True),
        db.Column('request_method', db.String(10), nullable=False),
        db.Column('request_headers', db.UnicodeText(), nullable=False),
        db.Column('request_body', db.UnicodeText()),

        db.Column('response_status', db.Integer, nullable=False, unique=True),
        db.Column('response_headers', db.UnicodeText(), nullable=False),
        db.Column('response_body', db.UnicodeText()),

        db.Column('created_at', db.DateTime, default=datetime.utcnow),
        db.Column('updated_at', db.DateTime, default=datetime.utcnow)
    )
