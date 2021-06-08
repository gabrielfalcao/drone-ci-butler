from flask import Flask, redirect
from flask_restx import Api

from slack import WebClient
from slack.errors import SlackApiError

from drone_ci_butler.version import version
from drone_ci_butler.config import config

SERVER_NAME = f"DroneAPI Butler v{version}"


class Application(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.oauth = OAuth(self)

    def setup_app(self):
        self.setup_auth()

    def setup_auth(self):
        self.oauth.register(
            name="github",
            # server_metadata_url=CONF_URL,
            client_kwargs={"scope": "user:read user:email"},
        )

    def process_response(self, response):
        response.headers["server"] = SERVER_NAME
        super().process_response(response)
        return response


webapp = Application(__name__)


@webapp.route("/github/hooks/auth")
def github_auth_hook():
    import ipdb;ipdb.set_trace()  # fmt: skip
    return "ok"


@webapp.route("/slack/hooks/auth")
def slack_auth_hook():
    # Verify the "state" parameter
    import ipdb;ipdb.set_trace()  # fmt: skip

    # Retrieve the auth code from the request params
    code_param = request.args["code"]

    # An empty string is a valid token for this request
    client = WebClient()

    # Request the auth tokens from Slack
    response = client.oauth_v2_access(
        client_id=config.slack_client_id,
        client_secret=config.slack_client_secret,
        code=code_param,
    )


api = Api(webapp)
