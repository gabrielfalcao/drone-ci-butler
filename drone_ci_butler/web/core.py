import json
from pathlib import Path
from flask import Flask, redirect, send_from_directory, request

from flask_cors import CORS
from flask_session import Session
from functools import lru_cache
from authlib.integrations.flask_client import OAuth
from loginpass import GitHub, Slack


from flask_restx import Api
from drone_ci_butler.config import config
from drone_ci_butler.logs import get_logger
from drone_ci_butler.version import version
from .oauth import create_flask_blueprint

SERVER_NAME = f"drone-ci-butler.ngrok.io"


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
        self.route("/settings")(self.serve_index)
        self.route("/success")(self.serve_index)

    def serve_index(self, path=None):
        return send_from_directory(static_path, "index.html")

    def setup_api(self):
        self.api = Api(
            self,
            version=version,
            default="API",
            title="Drone CI Monitor API",
            endpoint=f"/api/v{version}/",
            description="Manage settings and notifications",
        )

    def handle_oauth_authorization(self, remote, token, user_info):
        if token:
            self.save_oauth_token(remote.name, token)
        if user_info:
            self.save_oauth_user(user_info)
        import ipdb;ipdb.set_trace()  # fmt: skip
        return redirect("/settings")

    def save_oauth_token(self, provider_name: str, token: dict):
        print("save oauth token")
        import ipdb;ipdb.set_trace()  # fmt: skip

    def save_oauth_user(self, user_info: dict):
        print("save oauth user")
        import ipdb;ipdb.set_trace()  # fmt: skip

    def setup_auth(self):
        if isinstance(getattr(self, "oauth", None), OAuth):
            return

        self.oauth = OAuth(self)

        backends = [GitHub, Slack]
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
