import React from "react";
import { useAuth } from "drone-ci-butler/auth";
import Screen from "drone-ci-butler/components/Screen";
import { useHistory } from "react-router";

import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";

function Builds() {
  const { isAuthenticated } = useAuth();
  const history = useHistory();
  if (!isAuthenticated) {
    return (
      <Screen>
        <Modal.Dialog>
          <Modal.Header>
            <Modal.Title>Not Authenticated</Modal.Title>
          </Modal.Header>

          <Modal.Footer>
            <Button
              variant="primary"
              onClick={() => {
                history.goBack();
              }}
            >
              Go back
            </Button>
          </Modal.Footer>
        </Modal.Dialog>
      </Screen>
    );
  }
  return <Screen></Screen>;
}

export default Builds;
