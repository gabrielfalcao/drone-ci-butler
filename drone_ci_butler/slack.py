from slack_sdk import WebClient
from drone_ci_butler.config import config
from drone_ci_butler.logs import get_logger

logger = get_logger(__name__)


class SlackClient(object):
    def __init__(self, token: str = None, limit=1000):
        self.slack = WebClient(token=token or config.SLACK_BOT_TOKEN)
        self.limit = limit

    def search_channel_by_name(self, channel_name: str, limit: int = None) -> dict:
        limit = limit or self.limit
        response = self.slack.conversations_list(
            types="public_channel", limit=limit, exclude_archived=True
        )
        channel = None
        next_cursor = response.data.get("response_metadata", {}).get("next_cursor")

        page = 0
        while next_cursor and not channel:
            page += 1
            next_cursor = response.data.get("response_metadata", {}).get("next_cursor")

            channels = response.data["channels"]
            for c in channels:
                if c["name"] == channel_name:
                    return c

            logger.info(f"still looking for channel {channel_name} page {page}")
            response = self.slack.conversations_list(
                types="public_channel",
                limit=limit,
                cursor=next_cursor,
                exclude_archived=True,
            )
            next_cursor = response.data.get("response_metadata", {}).get("next_cursor")

    def search_user_by_name(self, user_name: str, limit: int = None) -> dict:
        limit = limit or self.limit
        response = self.slack.users_list(limit=limit)
        next_cursor = response.data.get("response_metadata", {}).get("next_cursor")
        user = None
        page = 0
        while next_cursor and not user:
            page += 1
            next_cursor = response.data.get("response_metadata", {}).get("next_cursor")
            users = response.data["members"]

            for c in users:
                if c["profile"]["display_name"] == user_name:
                    return c

            logger.info(f"still looking for user {user_name} page {page}")

            response = self.slack.users_list(cursor=next_cursor, limit=limit)
            next_cursor = response.data.get("response_metadata", {}).get("next_cursor")

    def send_message(self, channel: str, **kw):
        # join_response = self.slack.conversations_join(channel=channel)
        return self.slack.chat_postMessage(channel=channel, **kw)
        # return client.api_call(api_method="chat.postMessage", **kw)

    def get_user_info(self, user_id: str):
        return self.slack.api_call(api_method="users.info", json={"user": user_id})
