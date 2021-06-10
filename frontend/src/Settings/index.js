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
            <ListGroup variant="dark">
              <ListGroup.Item action href="#authentication">
                Authentication
              </ListGroup.Item>
              <ListGroup.Item action href="#slack-notifications">
                Slack Notifications
              </ListGroup.Item>
              <ListGroup.Item action href="#github-notifications">
                Github Notifications
              </ListGroup.Item>
            </ListGroup>
          </Col>
          <Col sm={8}>
            <Tab.Content>
              <Tab.Pane eventKey="#authentication">
                <Card>
                  <Card.Header>Authentication Info</Card.Header>
                  {github ? (
                    <>
                      <Card.Body>
                        <Card.Title>Github Name: {github.name}</Card.Title>
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
                    </>
                  ) : null}
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
                    <Card.Title>Send me Slack messages when</Card.Title>
                    <Form>
                      <p></p>
                      <Form.Check
                        type="checkbox"
                        id="slack-msg-failed-builds"
                        label="A build fails"
                        checked
                        disabled
                      />
                      <Form.Check
                        type="checkbox"
                        id="slack-msg-failed-pipeline"
                        label="A pipeline fails"
                        checked
                        disabled
                      />
                      <Form.Check
                        type="checkbox"
                        id="slack-msg-failed-pipeline"
                        label="A step fails"
                        checked
                        disabled
                      />

                      <Form.Check
                        type="checkbox"
                        id="slack-msg-succeeded-builds"
                        label="A build succeeds"
                        disabled
                      />
                    </Form>
                  </Card.Body>
                  <Card.Footer style={{ textAlign: "right" }}>
                    <Button disabled variant="warning">
                      Save
                    </Button>
                  </Card.Footer>
                </Card>
              </Tab.Pane>
            </Tab.Content>
            <Tab.Content>
              <Tab.Pane eventKey="#github-notifications">
                <Card>
                  <Card.Header>Github Notification Settings</Card.Header>
                  <Card.Body>
                    <Card.Title>Comment on my PRs</Card.Title>
                    <Form>
                      <p></p>
                      <Form.Check
                        type="checkbox"
                        id="github-comment-infra-errors"
                        label="When an infrastructure error happens"
                        checked
                        disabled
                      />
                      <Form.Check
                        type="checkbox"
                        id="github-comment-every-error"
                        label="When any failure happens"
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
