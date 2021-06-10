import React from "react";
import { useAuth } from "drone-ci-butler/auth";

export default function AddToSlackButton() {
  const { slack } = useAuth();
  if (slack) {
    return null;
  }
  return (
    <a href="https://drone-ci-butler.ngrok.io/oauth/login/slack">
      <img
        alt="Add to Slack"
        height="40"
        width="139"
        src="https://platform.slack-edge.com/img/add_to_slack.png"
        srcset="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x"
      />
    </a>
  );
}
