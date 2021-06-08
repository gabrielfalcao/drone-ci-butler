import React from "react";
import { BrowserRouter as Router, Switch, Route, Link } from "react-router-dom";
import { Menu } from "@nyt-cms/ink";
import Login from "./Login";
import Settings from "./Settings";

import "@nyt-cms/ink/tokens/typography/fonts";
import {
  breakpoints,
  colors,
  gridLayout,
  spacing,
  typography,
} from "@nyt-cms/ink";

import { css, cx } from "pretty-lights";

const defaultStyle = css`
  border: 1px solid ${colors.border};
  padding: ${spacing.sm};
`;

const mainContent = css`
  grid-column: 1 / 3;
  @media ${breakpoints.MEDIUM} {
    grid-column: 2 / 6;
  }
  @media ${breakpoints.LARGE} {
    grid-column: 3 / 11;
  }
`;

const rightedBlock = css`
  text-align: right;
  display: block;
  margin-top: -${spacing.lg};
  padding: 0;
`;

export default function App() {
  return (
    <Router>
      <div>
        {/*
            A <Switch> looks through all its children <Route>
            elements and renders the first one whose path
            matches the current URL. Use a <Switch> any time
            you have multiple routes, but you want only one
            of them to render at a time
          */}
        <div className={gridLayout}>
          <main className={cx(mainContent)}>
            <div className={cx(typography.head.lg)}>
              Drone CI Monitor
              <div className={rightedBlock}>
                <Menu id="preview" placeholder="Menu" aria-label="Menu">
                  <Menu.Item key="home" value="home">
                    <Link to="/">Home</Link>
                  </Menu.Item>

                  <Menu.Item key="github_login" value="github_login">
                    <a href="/oauth/login/github">Github Login</a>
                  </Menu.Item>

                  <Menu.Item key="slack_login" value="slack_login">
                    <a href="/oauth/login/slack">Slack Login</a>
                  </Menu.Item>

                  <Menu.Item key="login" value="login">
                    <a href="/oauth/login/github">Login</a>
                  </Menu.Item>

                  <Menu.Item key="settings" value="settings">
                    <Link to="/settings">Settings</Link>
                  </Menu.Item>
                </Menu>
              </div>
            </div>

            <div className={mainContent}>&nbsp;</div>
            <div className={cx(defaultStyle, mainContent)}>
              <Switch>
                <Route exact path="/">
                  <Login />
                </Route>
                <Route path="/settings">
                  <Settings />
                </Route>
              </Switch>
            </div>
          </main>
        </div>
      </div>
    </Router>
  );
}
