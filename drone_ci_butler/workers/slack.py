def notify(message, stage, step, output):
    print(message)
    # author = User.find_one_by(github_username=build.author_login)
    # if not author:
    #     # ignore builds from github users who did not opt-in
    #     return

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🔴 Build failed for the PR {pr_number} {owner}/{repo}",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"**Stage:** stage.name"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"**Step:** step.name"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"{message}"},
        },
        {"type": "divider"},
    ]

    client = SlackClient().slack
    channel = "C023Z62N59Q"
    user_id = "W01BD07TYGP"
    self.logger.info(f"posting message to slack user @gabriel.falcao")
    message_response = client.chat_postMessage(
        channel=user_id,
        blocks=blocks,
    )
