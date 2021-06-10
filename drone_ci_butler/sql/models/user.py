import hashlib
import jwt
import bcrypt

from datetime import datetime, timedelta
from dateutil.parser import parse as parse_datetime
from typing import Optional, List, Dict
from functools import lru_cache
from sqlalchemy import desc
from drone_ci_butler.logs import get_logger
from drone_ci_butler.util import load_json
from drone_ci_butler.slack import SlackClient

# from uiclasses import Model as DataClass
from chemist import Model, db, metadata
from drone_ci_butler.config import config

logger = get_logger(__name__)


class AccessToken(Model):
    table = db.Table(
        "auth_access_token",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("identity_provider", db.Unicode(255)),
        db.Column("content", db.UnicodeText, nullable=False, unique=True),
        db.Column("refresh_token", db.UnicodeText),
        db.Column("scope", db.UnicodeText, nullable=True),
        db.Column(
            "created_at", db.Unicode(255), default=lambda: datetime.utcnow().isoformat()
        ),
        db.Column("duration", db.Integer),
        db.Column(
            "user_id",
            db.Integer,
            db.ForeignKey("auth_user.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )

    @lru_cache()
    def scopes(self):
        return scope_string_to_set(self.scope)

    @property
    def user(self):
        return User.find_one_by(id=self.user_id) if self.user_id else None

    def to_dict(self):
        data = self.user.to_dict()
        data.pop("id")
        data["access_token"] = self.serialize()
        return data

    def matches_scope(self, scope: str) -> bool:
        expired = not self.user.validate_token(self)
        if expired:
            return False

        scope_choices = scope_string_to_set(scope)
        intersection = self.scopes.intersection(scope_choices)
        if not intersection:
            logger.warning(
                f"token {self} ({self.scopes}) of user {self.user} does not have any of the required scope {scope}"
            )

        return bool(intersection)


class User(Model):
    table = db.Table(
        "auth_user",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("email", db.String(100), nullable=False, unique=True),
        db.Column("password", db.Unicode(128)),
        db.Column("github_username", db.Unicode(255)),
        db.Column("github_email", db.Unicode(255)),
        db.Column("github_access_token", db.UnicodeText),
        db.Column("github_refresh_token", db.UnicodeText),
        db.Column("github_json", db.UnicodeText),
        db.Column("slack_username", db.Unicode(255)),
        db.Column("slack_email", db.Unicode(255)),
        db.Column("slack_access_token", db.UnicodeText),
        db.Column("slack_refresh_token", db.UnicodeText),
        db.Column("slack_json", db.UnicodeText),
        db.Column("settings_json", db.UnicodeText),
        db.Column("created_at", db.DateTime),
        db.Column("updated_at", db.DateTime),
        db.Column("github_activated_at", db.DateTime),
        db.Column("slack_activated_at", db.DateTime),
    )

    def __str__(self):
        return f"<User id={self.id} email={self.email!r}>"

    def slack_client(self):
        return SlackClient(token=self.slack_token)

    def to_dict(self):
        data = self.serialize()
        data.pop("password")
        data["github"] = load_json(data.pop("github_json", ""))
        data["slack"] = load_json(data.pop("slack_json", ""))
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
    def create(cls, email, password=None, **kw):
        email = email.lower()
        if password:
            kw["password"] = cls.secretify_password(password)
        return super(User, cls).create(email=email, **kw)

    def token_secret(self):
        return bcrypt.kdf(
            password=config.SECRET_KEY.encode("utf-8"),
            salt=self.email.encode("utf-8"),
            desired_key_bytes=32,
            rounds=100,
        )

    def create_token(self, provider_name: str, duration: int = 28800, **kw):
        """
        :param duration: in seconds - defaults to 28800 (8 hours)
        """
        created_at = datetime.utcnow().isoformat()
        data = {
            "created_at": created_at,
            "duration": duration,
        }
        scope = kw.get("scope", None)
        data.update(kw)

        access_token = jwt.encode(
            data,
            self.token_secret(),
            algorithm="HS256",
        )
        return AccessToken.create(
            identity_provider=provider_name,
            content=access_token,
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
        return now() < valid_until
