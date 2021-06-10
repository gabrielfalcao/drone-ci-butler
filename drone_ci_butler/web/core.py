import json
from pathlib import Path
from flask import Flask, redirect, request, render_template, session

from flask_cors import CORS
from flask_session import Session
from functools import lru_cache
from authlib.integrations.flask_client import OAuth
from loginpass import GitHub
from datetime import datetime
from drone_ci_butler.slack import SlackClient

from flask_restx import Api
from drone_ci_butler import events
from drone_ci_butler.config import config
from drone_ci_butler.logs import get_logger
from drone_ci_butler.version import version
from drone_ci_butler.sql.models.user import AccessToken, User
from .oauth import create_flask_blueprint

SERVER_NAME = f"Drone CI Butler v{version}"


static_path = Path(__file__).parent.joinpath("public")

logger = get_logger(__name__)


class Application(Flask):
    def __init__(self, *args, **kwargs):
        params = {
            "template_folder": str(static_path),
            "static_url_path": "/",
            "static_folder": str(static_path),
        }
        params.update(kwargs)

        super().__init__(__name__, **params)
        self.setup_app()

    def setup_app(self):
        self.config.from_object(config.to_flask())
        self.setup_routes()
        self.setup_cors()
        self.setup_session()
        self.setup_auth()
        self.setup_api()

    def setup_session(self):
        self.session = Session(self)

    def setup_cors(self):
        self.cors = CORS(self)

    def setup_routes(self):
        self.route("/")(self.serve_index)
        self.route("/login")(self.serve_index)
        self.route("/settings")(self.serve_index)
        self.route("/builds")(self.serve_index)

    def serve_index(self, path=None):
        return render_template(
            "index.html",
            user=session.get("user"),
            token=session.get("token"),
            meta={"title": SERVER_NAME, "description": "A Companion for Drone CI"},
        )

    def setup_api(self):
        self.api = Api(
            self,
            version=version,
            default="API",
            title="Drone CI Monitor API",
            endpoint=f"/api/v1",
            description="Manage settings and notifications",
        )

    def handle_oauth_authorization(self, remote, token, user_info):
        self.save_oauth_token(remote.name, token, user_info)
        return redirect("/settings")

    def save_oauth_token(
        self, provider_name: str, token: dict, user_info: dict, email: str = None
    ):
        logger.info("saving oauth token")
        email = email or user_info.get("email")
        username = user_info.get("preferred_username")  # github
        user_id = user_info.get("id")  # slack
        access_token = token.get("access_token")
        refresh_token = token.get("refresh_token")

        if provider_name == "slack" and access_token:
            slack_client = SlackClient()
            user_info = slack_client.get_user_info(user_id)

        db_user = None
        db_token = None

        session[f"{provider_name}_user"] = user_info
        session[f"{provider_name}_token"] = token

        if email:
            params = {
                f"{provider_name}_username": username or user_id,
                f"{provider_name}_email": email,
                f"{provider_name}_access_token": access_token,
                f"{provider_name}_refresh_token": refresh_token,
                f"{provider_name}_json": json.dumps(user_info),
                f"{provider_name}_activated_at": datetime.utcnow(),
                f"updated_at": datetime.utcnow(),
            }

            db_user = User.find_one_by(email=email)
            if not db_user:
                db_user = User.create(email=email, created_at=datetime.utcnow())
                events.user_created.send(self, user=db_user)
            db_user.update_and_save(**params)
            events.user_updated.send(self, user=db_user)

        if db_user:
            session["user"] = db_user.to_dict()

        if token and db_user:
            db_token = db_user.create_token(provider_name, **token)
            events.token_created.send(self, token=db_token, user=db_user)

        if db_token:
            session["token"] = db_token.to_dict()
        else:
            logger.warning(
                f"failed to store token in db: token={token} db_user={db_user}"
            )

    def setup_auth(self):
        if isinstance(getattr(self, "oauth", None), OAuth):
            return

        self.oauth = OAuth(self)

        backends = [
            GitHub,
        ]
        for b in backends:
            b.OAUTH_CONFIG["client_kwargs"].update(
                getattr(config, f"{b.NAME.upper()}_AUTHORIZE_PARAMS")
            )
        self.oauth_blueprint = create_flask_blueprint(
            backends, self.oauth, self.handle_oauth_authorization
        )
        self.register_blueprint(self.oauth_blueprint, url_prefix="/oauth")

    def process_response(self, response):
        response.headers["server"] = SERVER_NAME
        super().process_response(response)
        return response


webapp = Application()
api = webapp.api
oauth = webapp.oauth
cors = webapp.cors
