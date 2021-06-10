import json
from slack_sdk.errors import SlackApiError

from slack_sdk.signature import SignatureVerifier
from slack_sdk.web import WebClient
from slack_sdk.oauth import AuthorizeUrlGenerator
from slack_sdk.oauth.installation_store import FileInstallationStore, Installation
from slack_sdk.oauth.state_store import FileOAuthStateStore
from flask import request, make_response, redirect, url_for, session
from drone_ci_butler.config import config
from drone_ci_butler.web.core import webapp
from drone_ci_butler.sql.models import User, AccessToken

# Issue and consume state parameter value on the server-side.
state_store = FileOAuthStateStore(
    expiration_seconds=300, base_dir=config.slack_state_store_path
)
# Persist installation data and lookup it by IDs.
installation_store = FileInstallationStore(
    base_dir=config.slack_installation_store_path
)

# Build https://slack.com/oauth/v2/authorize with sufficient query parameters
authorize_url_generator = AuthorizeUrlGenerator(
    client_id=config.SLACK_CLIENT_ID,
    scopes=[
        "channels:history",
        # View messages and other content in public channels that Drone Monitor has been added to
        "channels:join",
        # Join public channels in a workspace
        "channels:read",
        # View basic information about public channels in a workspace
        "chat:write",
        # Send messages as @drone_monitor
        "files:read",
        # View files shared in channels and conversations that Drone Monitor has been added to
        "files:write",
        # Upload, edit, and delete files as Drone Monitor
        "groups:history",
        # View messages and other content in private channels that Drone Monitor has been added to
        "groups:read",
        # View basic information about private channels that Drone Monitor has been added to
        "groups:write",
        # Manage private channels that Drone Monitor has been added to and create new ones
        "im:history",
        # View messages and other content in direct messages that Drone Monitor has been added to
        "im:read",
        # View basic information about direct messages that Drone Monitor has been added to
        "im:write",
        # Start direct messages with people
        "mpim:history",
        # View messages and other content in group direct messages that Drone Monitor has been added to
        "mpim:read",
        # View basic information about group direct messages that Drone Monitor has been added to
        "mpim:write",
        # Start group direct messages with people
        "users:read",
        # View people in a workspace
        "users:read.email",
        # View email addresses of people in a workspace
    ],
    user_scopes=[
        "identity.avatar",
        # View a user’s Slack avatar
        "identity.basic",
        # View information about a user’s identity
        "identity.email",
        # View a user’s email address
    ],
)

client_id = config.SLACK_CLIENT_ID
client_secret = config.SLACK_CLIENT_SECRET
signing_secret = config.SLACK_SIGNING_SECRET
signature_verifier = SignatureVerifier(signing_secret=signing_secret)


@webapp.route("/oauth/login/slack")
def login_to_slack():
    state = state_store.issue()
    # https://slack.com/oauth/v2/authorize?state=(generated value)&client_id={client_id}&scope=app_mentions:read,chat:write&user_scope=search:read
    url = authorize_url_generator.generate(state)
    return redirect(url)


# Redirect URL
@webapp.route("/oauth/auth/slack", methods=["GET"])
def oauth_callback():
    redirect_uri = url_for(".oauth_callback", _external=True, _scheme="https")
    # Retrieve the auth code and state from the request params
    if "code" in request.args:
        # Verify the state parameter
        if state_store.consume(request.args["state"]):
            client = WebClient()  # no prepared token needed for this
            # Complete the installation by calling oauth.v2.access API method
            oauth_response = client.oauth_v2_access(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                code=request.args["code"],
            )

            installed_enterprise = oauth_response.get("enterprise", {})
            is_enterprise_install = oauth_response.get("is_enterprise_install")
            installed_team = oauth_response.get("team", {})
            installer = oauth_response.get("authed_user", {})
            incoming_webhook = oauth_response.get("incoming_webhook", {})

            bot_token = oauth_response.get("access_token")

            # NOTE: oauth.v2.access doesn't include bot_id in response
            bot_id = None
            enterprise_url = None
            if bot_token is not None:
                auth_test = client.auth_test(token=bot_token)
                bot_id = auth_test["bot_id"]
                if is_enterprise_install is True:
                    enterprise_url = auth_test.get("url")

            installation = Installation(
                app_id=oauth_response.get("app_id"),
                enterprise_id=installed_enterprise.get("id"),
                enterprise_name=installed_enterprise.get("name"),
                enterprise_url=enterprise_url,
                team_id=installed_team.get("id"),
                team_name=installed_team.get("name"),
                bot_token=bot_token,
                bot_id=bot_id,
                bot_user_id=oauth_response.get("bot_user_id"),
                bot_scopes=oauth_response.get("scope"),  # comma-separated string
                user_id=installer.get("id"),
                user_token=installer.get("access_token"),
                user_scopes=installer.get("scope"),  # comma-separated string
                incoming_webhook_url=incoming_webhook.get("url"),
                incoming_webhook_channel=incoming_webhook.get("channel"),
                incoming_webhook_channel_id=incoming_webhook.get("channel_id"),
                incoming_webhook_configuration_url=incoming_webhook.get(
                    "configuration_url"
                ),
                is_enterprise_install=is_enterprise_install,
                token_type=oauth_response.get("token_type"),
            )

            # Store the installation
            installation_store.save(installation)
            user = session.get("user") or {}
            email = user.get("email")
            token_info = dict(oauth_response.data)
            user_info = token_info.pop("authed_user", {}) or {}
            token = webapp.save_oauth_token("slack", token_info, user_info, email=email)
            return redirect("/")
        else:
            return make_response(
                f"Try the installation again (the state value is already expired)", 400
            )

    error = request.args["error"] if "error" in request.args else ""
    return make_response(
        f"Something is wrong with the installation (error: {error})", 400
    )


@webapp.route("/slack/events", methods=["POST"])
def slack_app():
    # Verify incoming requests from Slack
    # https://api.slack.com/authentication/verifying-requests-from-slack
    if not signature_verifier.is_valid(
        body=request.get_data(),
        timestamp=request.headers.get("X-Slack-Request-Timestamp"),
        signature=request.headers.get("X-Slack-Signature"),
    ):
        return make_response("invalid request", 403)

    # Handle a slash command invocation
    if "command" in request.form and request.form["command"] == "/open-modal":
        try:
            # in the case where this app gets a request from an Enterprise Grid workspace
            enterprise_id = request.form.get("enterprise_id")
            # The workspace's ID
            team_id = request.form["team_id"]
            # Lookup the stored bot token for this workspace
            bot = installation_store.find_bot(
                enterprise_id=enterprise_id,
                team_id=team_id,
            )
            bot_token = bot.bot_token if bot else None
            if not bot_token:
                # The app may be uninstalled or be used in a shared channel
                return make_response("Please install this app first!", 200)

            # Open a modal using the valid bot token
            client = WebClient(token=bot_token)
            trigger_id = request.form["trigger_id"]
            response = client.views_open(
                trigger_id=trigger_id,
                view={
                    "type": "modal",
                    "callback_id": "modal-id",
                    "title": {"type": "plain_text", "text": "Awesome Modal"},
                    "submit": {"type": "plain_text", "text": "Submit"},
                    "blocks": [
                        {
                            "type": "input",
                            "block_id": "b-id",
                            "label": {
                                "type": "plain_text",
                                "text": "Input label",
                            },
                            "element": {
                                "action_id": "a-id",
                                "type": "plain_text_input",
                            },
                        }
                    ],
                },
            )
            return make_response("", 200)
        except SlackApiError as e:
            code = e.response["error"]
            return make_response(f"Failed to open a modal due to {code}", 200)

    elif "payload" in request.form:
        # Data submission from the modal
        payload = json.loads(request.form["payload"])
        if (
            payload["type"] == "view_submission"
            and payload["view"]["callback_id"] == "modal-id"
        ):
            submitted_data = payload["view"]["state"]["values"]
            print(
                submitted_data
            )  # {'b-id': {'a-id': {'type': 'plain_text_input', 'value': 'your input'}}}
            # You can use WebClient with a valid token here too
            return make_response("", 200)

    # Indicate unsupported request patterns
    return make_response("", 404)


{
    "access_token": "xoxb-2177882080-2131978732069-dU5zEMJ86CDYAc8rsRnLhzEA",
    "app_id": "A023J88CTF1",
    "authed_user": {
        "access_token": "xoxp-2177882080-1414377123169-2136252220551-51993d649c0b8cfcccdf90735e7d9083",
        "id": "W01BD07TYGP",
        "scope": "identity.basic,identity.email,identity.avatar",
        "token_type": "user",
    },
    "bot_user_id": "U023VUSMJ21",
    "enterprise": {"id": "EAG3RTG90", "name": "The New York Times Co"},
    "is_enterprise_install": False,
    "ok": True,
    "scope": "channels:read,chat:write,channels:join,users:read,users:read.email,groups:read,im:read,mpim:read,im:write,mpim:write,groups:write,channels:history,im:history,groups:history,mpim:history,files:write,files:read",
    "team": {"id": "T0257RY2C", "name": "The New York Times"},
    "token_type": "bot",
}
