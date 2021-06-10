import json
import hashlib
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from urllib.parse import urlparse
from pathlib import Path
from drone_ci_butler.config import config
from drone_ci_butler.logs import get_logger
from drone_ci_butler.sql.models.slack import SlackMessage

logger = get_logger(__name__)


messages_path = Path("~/butler-slack/messages").expanduser().absolute()
messages_path.mkdir(exist_ok=True, parents=True)


def log_api_error(exc):
    response = exc.response.data
    method = urlparse(exc.response.api_url).path.split("/")[-1]
    params = exc.response.req_args.get("params") or exc.response.req_args.get("json")
    logger.error(
        f"failed to call method {method} with params {params} responded with {response}"
    )


def store_message(to: str, msg: dict):
    asjson = json.dumps(msg)

    name = hashlib.sha1(asjson.encode()).hexdigest()
    saved_path = messages_path.joinpath(f"{to}-{name}.json")

    try:
        return SlackMessage.create(
            channel=to,
            ts=msg.get("ts"),
            ok=msg.get("ok"),
            message=asjson,
        )
    except Exception:
        logger.exception(f"failed to store message: {msg} in SQL db")

    with saved_path.open("w") as fd:
        fd.write(asjson)


class SlackClient(object):
    def __init__(self, token: str = None, limit=1000):
        self.slack = WebClient(token=token or config.SLACK_BOT_TOKEN)
        self.limit = limit

    def send_message(self, to: str, **kw):
        # join_response = self.slack.conversations_join(channel=channel)
        response = self.slack.chat_postMessage(channel=to, **kw)
        msg = response.data
        store_message(to, msg)
        return response
        # return client.api_call(api_method="chat.postMessage", **kw)

    def call(self, method_name: str, **kw):
        try:
            return self.slack.api_call(api_method=method_name, json=kw).data
        except SlackApiError as e:
            log_api_error(e)
            return {}

    def get_user_info(self, user_id: str):
        return self.call("users.profile.get", user=user_id)

    def get_user_identity(self):
        return self.call("users.identity")

    def get_conversations(
        self,
    ):

        return self.call("conversations.list", **kw)

    def get_user_conversations(
        self, types="public_channel, private_channel, mpim, im", **kw
    ):
        kw["types"] = types
        return self.call("users.conversations", **kw)

    def get_history(self, channel_id: str):
        try:
            return self.slack.conversations_history(channel=channel_id).data
        except SlackApiError as e:
            log_api_error(e)
            return {}

    def delete_message(self, channel_id: str, ts: str):
        try:
            return self.slack.chat_delete(
                channel=channel_id,
                ts=ts,
            ).data
        except SlackApiError as e:
            log_api_error(e)
            return {}

    # def search_channel_by_name(self, channel_name: str, limit: int = None) -> dict:
    #     limit = limit or self.limit
    #     response = self.slack.conversations_list(
    #         types="public_channel", limit=limit, exclude_archived=True
    #     )
    #     channel = None
    #     next_cursor = response.data.get("response_metadata", {}).get("next_cursor")

    #     page = 0
    #     while next_cursor and not channel:
    #         page += 1
    #         next_cursor = response.data.get("response_metadata", {}).get("next_cursor")

    #         channels = response.data["channels"]
    #         for c in channels:
    #             if c["name"] == channel_name:
    #                 return c

    #         logger.info(f"still looking for channel {channel_name} page {page}")
    #         response = self.slack.conversations_list(
    #             types="public_channel",
    #             limit=limit,
    #             cursor=next_cursor,
    #             exclude_archived=True,
    #         )
    #         next_cursor = response.data.get("response_metadata", {}).get("next_cursor")

    # def search_user_by_name(self, user_name: str, limit: int = None) -> dict:
    #     limit = limit or self.limit
    #     response = self.slack.users_list(limit=limit)
    #     next_cursor = response.data.get("response_metadata", {}).get("next_cursor")
    #     user = None
    #     page = 0
    #     while next_cursor and not user:
    #         page += 1
    #         next_cursor = response.data.get("response_metadata", {}).get("next_cursor")
    #         users = response.data["members"]

    #         for c in users:
    #             if c["profile"]["display_name"] == user_name:
    #                 return c

    #         logger.info(f"still looking for user {user_name} page {page}")

    #         response = self.slack.users_list(cursor=next_cursor, limit=limit)
    #         next_cursor = response.data.get("response_metadata", {}).get("next_cursor")
