import json
import hashlib
import jwt
import bcrypt

from datetime import datetime, timedelta
from dateutil.parser import parse as parse_datetime
from cached_property import cached_property
from typing import Optional, List, Dict
from sqlalchemy import desc
from drone_ci_butler.logs import get_logger

# from uiclasses import Model as DataClass
from chemist import Model, db, metadata
from drone_ci_butler.config import config

logger = get_logger(__name__)


class User(Model):
    table = db.Table(
        "auth_user",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("email", db.String(100), nullable=False, unique=True),
        db.Column("password", db.Unicode(128), nullable=False),
        db.Column("created_at", db.DateTime),
        db.Column("updated_at", db.DateTime),
        db.Column("requested_subscription_at", db.DateTime),
        db.Column("invited_at", db.DateTime),
        db.Column("activated_at", db.DateTime),
    )

    def __str__(self):
        return f"<User id={self.id} email={self.email!r}>"

    def to_dict(self):
        data = self.serialize()
        data.pop("password")
        return data

    def change_password(self, old_password, new_password):
        right_password = self.match_password(old_password)
        if right_password:
            return self.set_password(new_password)

        return False

    def set_password(self, password) -> bool:
        self.set(password=self.secretify_password(password))
        self.save()
        return True

    def match_password(self, plain) -> bool:
        return bcrypt.checkpw(plain.encode("utf-8"), self.password.encode("utf-8"))

    @classmethod
    def find_one_by_email(cls, email):
        email = email.lower()
        return cls.find_one_by(email=email)

    @classmethod
    def authenticate(cls, email, password):
        user = cls.find_one_by_email(email)
        if not user:
            return

        if user.match_password(password):
            return user

    @classmethod
    def secretify_password(cls, plain) -> str:
        if not plain:
            raise RuntimeError(f"cannot hash without a plain password: {plain!r}")
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @classmethod
    def create(cls, email, password, **kw):
        email = email.lower()
        password = cls.secretify_password(password)
        return super(User, cls).create(email=email, password=password, **kw)

    @property
    def token_secret(self):
        return bcrypt.kdf(
            password=config.SECRET_KEY,
            salt=self.password.encode("utf-8"),
            desired_key_bytes=32,
            rounds=100,
        )

    def create_token(
        self, scope: str = "user:email user:read", duration: int = 28800, **kw
    ):
        """
        :param duration: in seconds - defaults to 28800 (8 hours)
        """
        created_at = datetime.utcnow().isoformat()
        access_token = jwt.encode(
            {
                "created_at": created_at,
                "duration": duration,
                "scope": f"{scope}",
            },
            self.token_secret,
            algorithm="HS256",
        )
        return AccessToken.create(
            content=access_token.decode("utf-8"),
            scope=scope,
            user_id=self.id,
            created_at=created_at,
            duration=duration,
        )

    def validate_token(self, access_token: AccessToken) -> bool:
        data = jwt.decode(access_token.content, self.token_secret, algorithms=["HS256"])
        created_at = access_token.created_at
        duration = access_token.duration
        valid_until = parse_datetime(created_at) + timedelta(seconds=duration)
        return datetime.utcnow() < valid_until
