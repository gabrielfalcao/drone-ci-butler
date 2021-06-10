import React from "react";
import { useAuth } from "drone-ci-butler/auth";
import Screen from "drone-ci-butler/components/Screen";
import Card from "react-bootstrap/Card";
import Button from "react-bootstrap/Button";
import ListGroup from "react-bootstrap/ListGroup";
import Row from "react-bootstrap/Row";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Tab from "react-bootstrap/Tab";
import AddToSlackButton from "drone-ci-butler/components/AddToSlackButton";
import NotAuthenticated from "drone-ci-butler/components/NotAuthenticated";

function Settings() {
  const { github, token, slack, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <NotAuthenticated />;
  }
  return (
    <Screen>
      <Tab.Container
        id="list-group-tabs-example"
        defaultActiveKey="#authentication"
      >
        <Row>
          <Col sm={4}>
            <ListGroup>
              <ListGroup.Item action href="#authentication">
                Authentication
              </ListGroup.Item>
              <ListGroup.Item action href="#slack-notifications">
                Slack Notifications
              </ListGroup.Item>
            </ListGroup>
          </Col>
          <Col sm={4}>
            <Tab.Content>
              <Tab.Pane eventKey="#authentication">
                <Card>
                  <Card.Header>Authentication</Card.Header>
                  <Card.Img variant="top" src={github.picture} />

                  <Card.Body>
                    <Card.Title>{github.name}</Card.Title>
                    <Card.Title>
                      Github Username: {github.preferred_username}
                    </Card.Title>
                    <Card.Text>{github.email}</Card.Text>
                    <Card.Title>Github Access Token</Card.Title>
                    <Card.Text>
                      <pre>{token.github_token}</pre>
                    </Card.Text>
                  </Card.Body>
                  <hr />
                  {slack ? (
                    <>
                      <Card.Body>
                        <Card.Title>Slack ID: {slack.id}</Card.Title>
                        <Card.Title>Slack Access Token</Card.Title>
                        <Card.Text>
                          <pre>{token.slack_token}</pre>
                        </Card.Text>
                        <Card.Text>{slack.scope}</Card.Text>
                      </Card.Body>
                    </>
                  ) : (
                      <AddToSlackButton />
                    )}
                </Card>
              </Tab.Pane>
              <Tab.Pane eventKey="#slack-notifications">
                <Card>
                  <Card.Header>Slack Notification Settings</Card.Header>
                  <Card.Body>
                    <Card.Title>Send slack messages for:</Card.Title>
                    <Form>
                      <p></p>
                      <Form.Check
                        type="checkbox"
                        id="slack-msg-failed-builds"
                        label="Failed builds"
                        checked
                        disabled
                      />
                      <Form.Check
                        type="checkbox"
                        id="slack-msg-succeeded-builds"
                        label="Succeeded builds"
                        disabled
                      />
                    </Form>
                  </Card.Body>
                  <Card.Footer style={{ textAlign: "right" }}>
                    <Button disabled variant="dark">
                      Save
                    </Button>
                  </Card.Footer>
                </Card>
              </Tab.Pane>
            </Tab.Content>
          </Col>
        </Row>
      </Tab.Container>
    </Screen>
  );
}

export default Settings;
