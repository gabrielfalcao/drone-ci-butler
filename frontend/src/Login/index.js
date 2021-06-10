import React from "react";
import { useAuth } from "drone-ci-butler/auth";
import Screen from "drone-ci-butler/components/Screen";
import AddToSlackButton from "drone-ci-butler/components/AddToSlackButton";

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
          {!isAuthenticated ? (
            <p>
              First, login with Github so I watch out for Drone builds authored
              by you.
            </p>
          ) : null}
          {isAuthenticated ? (
            <p>
              Now connect to Slack so I know what user to message when a build
              fails.
            </p>
          ) : null}
        </Modal.Body>

        <Modal.Footer>
          {!isAuthenticated ? (
            <Button
              href="https://drone-ci-butler.ngrok.io/oauth/login/github"
              variant="dark"
            >
              Login with Github
            </Button>
          ) : null}
          {isAuthenticated ? <AddToSlackButton /> : null}
        </Modal.Footer>
      </Modal.Dialog>

      <p></p>
    </Screen>
  );
}

export default Home;
