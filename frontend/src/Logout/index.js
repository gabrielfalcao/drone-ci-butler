import React from "react";
import { useAuth } from "drone-ci-butler/auth";
import Screen from "drone-ci-butler/components/Screen";
import { LinkContainer } from "react-router-bootstrap";
import { useHistory } from "react-router";

import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";

function Logout() {
  const { signout } = useAuth();
  const history = useHistory();

  return (
    <Screen>
      <Modal.Dialog>
        <Modal.Header>
          <Modal.Title>Do you really want to logout ?</Modal.Title>
        </Modal.Header>

        <Modal.Footer>
          <Button
            variant="danger"
            onClick={() =>
              signout(() => {
                history.push("/");
              })
            }
          >
            Yes, logout
          </Button>

          <LinkContainer to="/">
            <Button>Cancel</Button>
          </LinkContainer>
        </Modal.Footer>
      </Modal.Dialog>

      <p></p>
    </Screen>
  );
}

export default Logout;
