import React from "react";
import { BrowserRouter, Switch, Route } from "react-router-dom";

import Container from "react-bootstrap/Container";
import Button from "react-bootstrap/Button";
import Navbar from "react-bootstrap/Navbar";
import Nav from "react-bootstrap/Nav";
import Form from "react-bootstrap/Form";
// import FormControl from "react-bootstrap/FormControl";

import { LinkContainer } from "react-router-bootstrap";

import { ProvideAuth, PrivateRoute, AuthButton } from "drone-ci-butler/auth";
import Login from "drone-ci-butler/Login";
import Logout from "drone-ci-butler/Logout";
import Home from "drone-ci-butler/Home";
import Settings from "drone-ci-butler/Settings";
import Builds from "drone-ci-butler/Builds";

const App = () => (
  <ProvideAuth>
    <BrowserRouter>
      <Navbar bg="dark" variant="dark">
        <LinkContainer to="/">
          <Navbar.Brand>Drone CI Monitor</Navbar.Brand>
        </LinkContainer>
        <Nav className="mr-auto">
          <LinkContainer to="/">
            <Nav.Link href="/">Home</Nav.Link>
          </LinkContainer>
          <LinkContainer to="/builds">
            <Nav.Link href="/builds">Builds</Nav.Link>
          </LinkContainer>
        </Nav>
        <Form inline>
          <LinkContainer to="/settings">
            <Button variant="outline-light">Settings</Button>
          </LinkContainer>
          <AuthButton />
        </Form>
      </Navbar>
      <Container>
        <Switch>
          <Route path="/login">
            <Login />
          </Route>
          <Route path="/logout">
            <Logout />
          </Route>
          <PrivateRoute path="/settings">
            <Settings />
          </PrivateRoute>
          <PrivateRoute path="/builds">
            <Builds />
          </PrivateRoute>
          <Route exact path="/">
            <Home />
          </Route>
        </Switch>
      </Container>
    </BrowserRouter>
  </ProvideAuth>
);

export default App;
