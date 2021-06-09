import React from "react";
import { useAuth, AuthButton } from "drone-ci-butler/auth";
import Screen from "drone-ci-butler/components/Screen";

import Modal from "react-bootstrap/Modal";

function Home() {
  const auth = useAuth();
  const { user, isAuthenticated } = auth;
  console.log("isAuthenticated", isAuthenticated);
  console.log("auth", auth);
  return (
    <Screen>
      <Modal.Dialog>
        <Modal.Header>
          <Modal.Title>
            Hi{isAuthenticated ? ` ${user},` : ","} I’m{" "}
            <strong>@drone-ci-butler</strong> 👋{" "}
          </Modal.Title>
        </Modal.Header>

        <Modal.Body>
          <p>
            I let you know immediately when a Drone build step fails with a
            possible root-cause and maybe even a suggestion for fix. I can also
            send you the full build if you want to.
          </p>
        </Modal.Body>

        <Modal.Footer>
          <AuthButton />
        </Modal.Footer>
      </Modal.Dialog>

      <p></p>
    </Screen>
  );
}

export default Home;
