import React from "react";

import "@nyt-cms/ink/tokens/typography/fonts";
import {
  Button,
  ButtonGroup,
  Dialog,
  colors,
  spacing,
  Spinner,
  typography,
  breakpoints,
  gridLayout,
  utility,
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

function Settings() {
  const { isOpen, openDialog, closeDialog } = Dialog.useDialogState(false);

  return (
    <>
      <div className={gridLayout}>
        <main className={cx(mainContent)}>
          <p className={cx(typography.head.md)}>Welcome, %user%</p>
          <div className={innerContent}>&nbsp;</div>
          <div className={cx(defaultStyle, innerContent, utility.boxShadow1)}>
            <p className={cx(typography.head.md)}>Settings</p>
            <p className={centeredBlock}>
              <ul>
                <li>foo</li>
              </ul>
            </p>
          </div>
        </main>
      </div>
    </>
  );
}

export default Settings;
