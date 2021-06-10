import React, { useContext, createContext, useState } from "react";
import { Route, Redirect } from "react-router-dom";
import { withRouter } from "react-router";
import Button from "react-bootstrap/Button";

// This example has 3 pages: a public page, a protected
// page, and a login screen. In order to see the protected
// page, you must first login. Pretty standard stuff.
//
// First, visit the public page. Then, visit the protected
// page. You're not yet logged in, so you are redirected
// to the login page. After you login, you are redirected
// back to the protected page.
//
// Notice the URL change each time. If you click the back
// button at this point, would you expect to go back to the
// login page? No! You're already logged in. Try it out,
// and you'll see you go back to the page you visited
// just *before* logging in, the public page.

export default PrivateRoute;

const fakeAuth = {
  isAuthenticated: false,
  signin(cb) {
    fakeAuth.isAuthenticated = true;
    cb(window.DRONE_CI_BUTLER_USER, window.DRONE_CI_BUTLER_TOKEN);
  },
  signout(cb) {
    fakeAuth.isAuthenticated = false;
    cb();
  },
};

/** For more details on
 * `authContext`, `ProvideAuth`, `useAuth` and `useProvideAuth`
 * refer to: https://usehooks.com/useAuth/
 */
const authContext = createContext();

export function ProvideAuth({ children }) {
  const auth = useProvideAuth();
  return <authContext.Provider value={auth}>{children}</authContext.Provider>;
}

export function useAuth() {
  return useContext(authContext);
}

export function useProvideAuth() {
  const [user, setUser] = useState(window.DRONE_CI_BUTLER_USER || null);
  const [token, setToken] = useState(window.DRONE_CI_BUTLER_TOKEN || null);

  const signin = (cb) => {
    return fakeAuth.signin((u, t) => {
      setUser(window.DRONE_CI_BUTLER_USER);
      setToken(window.DRONE_CI_BUTLER_TOKEN);
      cb(user, token);
    });
  };

  const signout = (cb) => {
    return fakeAuth.signout(() => {
      setUser(null);
      setToken(null);
      cb();
    });
  };

  const { github_json, slack_json } = user || {};
  const github = github_json ? JSON.parse(user.github_json) : null;
  const slack = slack_json ? JSON.parse(user.slack_json) : null;
  const isAuthenticated = user !== null || token !== null;
  fakeAuth.isAuthenticated = isAuthenticated;
  return {
    signin,
    signout,

    github,
    slack,
    user,
    token,

    setUser,
    setToken,

    isAuthenticated,
  };
}

export const AuthButton = withRouter(({ history }) =>
  fakeAuth.isAuthenticated ? (
    <Button
      onClick={() => {
        history.push("/logout");
      }}
    >
      Sign out
    </Button>
  ) : (
      <Button
        onClick={() => {
          history.push("/login");
        }}
      >
        Sign in
    </Button>
    )
);

export function PrivateRoute({ component: Component, ...rest }) {
  return (
    <Route
      {...rest}
      render={(props) =>
        fakeAuth.isAuthenticated ? (
          <Component {...props} />
        ) : (
            <Redirect
              to={{
                pathname: "/login",
                state: { from: props.location },
              }}
            />
          )
      }
    />
  );
}

export function AuthenticatedRoute({ component: Component, ...rest }) {
  return (
    <Route
      {...rest}
      render={(props) =>
        fakeAuth.isAuthenticated ? <Component {...props} /> : null
      }
    />
  );
}
