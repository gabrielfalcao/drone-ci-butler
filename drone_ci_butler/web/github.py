import json
from slack_sdk.errors import SlackApiError

from slack_sdk.signature import SignatureVerifier
from slack_sdk.web import WebClient
from slack_sdk.oauth import AuthorizeUrlGenerator
from slack_sdk.oauth.installation_store import FileInstallationStore, Installation
from slack_sdk.oauth.state_store import FileOAuthStateStore
from flask import request, make_response, redirect, url_for, session, Response
from drone_ci_butler import events
from drone_ci_butler.config import config
from drone_ci_butler.web.core import webapp
from drone_ci_butler.sql.models.user import User, AccessToken


@webapp.route("/github/hooks/events")
def handle_github_webhook():
    try:
        event = json.loads(request.data)
    except Exception:
        logger.exception(f"failed to parse github hook")
        event = request.args

    events.github_event.send(webapp, event=event, request=request)
    return Response(status_code=200)
