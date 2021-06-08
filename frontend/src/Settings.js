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
      <Dialog isOpen={isOpen} onClose={closeDialog}>
        <Dialog.Header>Settings</Dialog.Header>
        Dialog Body
        <Dialog.Footer>
          <ButtonGroup>
            <Button aria-label="Close Dialog" onClick={closeDialog}>
              Close Dialog
            </Button>
            <Button variant={Button.Variants.PRIMARY}>Primary Action</Button>
          </ButtonGroup>
        </Dialog.Footer>
      </Dialog>
      <div className={gridLayout}>
        <main className={cx(mainContent)}>
          <p className={cx(typography.head.md)}>Drone CI Monitor</p>
          <div className={innerContent}>&nbsp;</div>
          <div className={cx(defaultStyle, innerContent, utility.boxShadow1)}>
            <p className={cx(typography.head.md)}>
              First, login with Github, then to Slack
            </p>
            <p className={centeredBlock}>
              <Button variant={Button.Variants.PRIMARY}>
                Login with Github
              </Button>
              <Button
                type="button"
                aria-label="Open Dialog"
                onClick={openDialog}
              >
                Open Dialog
              </Button>
            </p>
          </div>
          <p className={cx(centeredBlock, innerContent)}>
            <Spinner />
          </p>
          <div className={innerContent}>&nbsp;</div>
        </main>
      </div>
    </>
  );
}

export default Settings;
