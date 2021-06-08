import React from "react";

import {
  Button,
  UserIcon,
  breakpoints,
  colors,
  gridLayout,
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
  return (
    <>
      <p>Hi, I’m @drone-ci-monitor 👋 </p>
      <p>
        I let you know immediately when a Drone build step fails with a possible
        root-cause and maybe even a suggestion for fix. I can also send you the
        full build if you want to.
      </p>

      <div className={gridLayout}>
        <div className={cx(defaultStyle, innerContent, utility.boxShadowInset)}>
          <p className={centeredBlock}>
            <Button
              href="/oauth/login/github"
              variant={Button.Variants.PRIMARY}
            >
              <UserIcon className={verticalAlignBottom} role="presentation" />
              Login with Github
            </Button>
          </p>
        </div>
      </div>
    </>
  );
}

export default Login;
