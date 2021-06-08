import React from "react";

import "@nyt-cms/ink/tokens/typography/fonts";
import {
  Button,
  UserIcon,
  breakpoints,
  colors,
  gridLayout,
  spacing,
  typography,
  utility,
} from "@nyt-cms/ink";

import { css, cx } from "pretty-lights";

const verticalAlignBottom = css`
  vertical-align: bottom;
`;
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

function App() {
  const { history } = this.props;
  return (
    <div className={gridLayout}>
      <main className={cx(mainContent)}>
        <p className={cx(typography.head.lg)}>Drone CI Monitor</p>
        <div className={innerContent}>&nbsp;</div>
        <div className={cx(defaultStyle, innerContent, utility.boxShadow1)}>
          <p>Hi, I’m @drone-ci-butler 👋 </p>
          <p>
            I let you know immediately when a Drone build step fails with a
            possible root-cause and maybe even a suggestion for fix. I can also
            send you the full build if you want to.
          </p>
          <p className={centeredBlock}>
            <Button href="/github/connect" variant={Button.Variants.PRIMARY}>
              <UserIcon className={verticalAlignBottom} role="presentation" />
              Login with Github
            </Button>
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
