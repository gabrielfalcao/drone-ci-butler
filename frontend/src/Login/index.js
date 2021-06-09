import React from "react";
import { useAuth } from "drone-ci-butler/auth";
import Screen from "drone-ci-butler/components/Screen";

import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";

function Home() {
  const { isAuthenticated } = useAuth();

  return (
    <Screen>
      <Modal.Dialog>
        <Modal.Header>
          <Modal.Title>Authentication</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          <p>
            First, login with Github so I watch out for Drone builds authored by
            you.
          </p>
          <p>
            Then connect to Slack so I know what user to message when a build
            fails.
          </p>
        </Modal.Body>

        <Modal.Footer>
          <Button
            href="https://drone-ci-butler.ngrok.io/oauth/login/github"
            variant="dark"
          >
            Login with Github
          </Button>
          <Button
            href="https://drone-ci-butler.ngrok.io/oauth/login/slack"
            variant="primary"
            disabled={!isAuthenticated}
          >
            Connect with Slack
          </Button>
        </Modal.Footer>
      </Modal.Dialog>

      <p></p>
    </Screen>
  );
}

export default Home;
