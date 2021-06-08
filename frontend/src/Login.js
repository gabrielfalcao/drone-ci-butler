import React, { useReducer /* useState */ } from "react";

import {
  /* Button, */
  UserIcon,
  EmailIcon,
  breakpoints,
  colors,
  gridLayout,
  typography,
  spacing,
  utility,
} from "@nyt-cms/ink";

import { css, cx } from "pretty-lights";

const verticalAlignBottom = css`
  vertical-align: bottom;
`;
const defaultStyle = css`
  border: 0px solid ${colors.border};
  padding: ${spacing.sm};
`;

const innerContent = css`
  grid-column: 1 / 3;
  @media ${breakpoints.MEDIUM} {
    grid-column: 2 / 6;
  }
  @media ${breakpoints.LARGE} {
    grid-column: 3 / 11;
  }
`;

const centeredBlock = css`
  text-align: center;
`;

function Login() {
  function reducer(state, action) {
    switch (action.type) {
      case "increment":
        return { ...state, count: state.count + 1 };
      case "decrement":
        return { ...state, count: state.count - 1 };
      default:
        return state;
    }
  }

  const [user, dispatchUser] = useReducer(reducer, window.DRONE_CI_BUTLER_USER);
  const [token, dispatchToken] = useReducer(
    reducer,
    window.DRONE_CI_BUTLER_TOKEN
  );
  console.log("user", user);
  console.log("token", token);

  return (
    <>
      <p className={cx(typography.body.md)}>
        Hi, I’m <strong>@drone-ci-butler</strong> 👋{" "}
      </p>
      <p className={cx(typography.body.md)}>
        I let you know immediately when a Drone build step fails with a possible
        root-cause and maybe even a suggestion for fix. I can also send you the
        full build if you want to.
      </p>

      <div className={gridLayout}>
        <div className={cx(defaultStyle, innerContent, utility.boxShadowInset)}>
          <p className={cx(centeredBlock, typography.body.md)}>
            <a href="/oauth/login/github">
              <UserIcon className={verticalAlignBottom} role="presentation" />
              Login with Github
            </a>
          </p>
          <p className={cx(centeredBlock, typography.body.md)}>
            <a href="/oauth/login/slack">
              <EmailIcon className={verticalAlignBottom} role="presentation" />
              Login with Slack
            </a>
          </p>
        </div>
      </div>
    </>
  );
}

export default Login;
