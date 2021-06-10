import React from "react";
//import { Link } from "react-router-dom";
import { useAuth, AuthButton } from "drone-ci-butler/auth";
import { Redirect } from "react-router-dom";
import Screen from "drone-ci-butler/components/Screen";

import AddToSlackButton from "drone-ci-butler/components/AddToSlackButton";
import Modal from "react-bootstrap/Modal";

function Home() {
  const auth = useAuth();
  const { user, slack, github, isAuthenticated } = auth;
  if (slack) {
    return <Redirect to="/settings" />;
  }
  console.log("isAuthenticated", isAuthenticated);
  console.log("auth", auth);
  return (
    <Screen>
      <Modal.Dialog>
        <Modal.Header>
          <Modal.Title>
            {github ? (
              `Welcome ${user.github_username} 👋`
            ) : (
              <>
                Hi, I’m <strong>@drone-ci-butler</strong> 👋{" "}
              </>
            )}
          </Modal.Title>
        </Modal.Header>

        <Modal.Body>
          {!github ? (
            <p>
              I let you know immediately when a Drone build step fails with a
              possible root-cause and maybe even a suggestion for fix. I can
              also send you the full build if you want to.
            </p>
          ) : (
            <p>
              You authenticated with Github sucessfully. Please connect to Slack
              so I can send you messages when your builds fail.
            </p>
          )}
        </Modal.Body>

        {isAuthenticated && !slack ? (
          <Modal.Footer>
            <AddToSlackButton />
          </Modal.Footer>
        ) : (
          <AuthButton />
        )}
      </Modal.Dialog>

      <p></p>
    </Screen>
  );
}

export default Home;
