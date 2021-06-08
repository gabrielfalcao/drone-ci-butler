import React from "react";

import "@nyt-cms/ink/tokens/typography/fonts";
import { typography, utility } from "@nyt-cms/ink";

import { css, cx } from "pretty-lights";

const code = css`
  overflow: auto;
  display: block;
  line-break: revert;
  max-width: 800px;
`;

function Settings() {
  return (
    <>
      <div>
        <pre className={code}>
          <p>User</p>
          {JSON.stringify(window.DRONE_CI_BUTLER_USER, null, 2)}
        </pre>
      </div>
      <div>
        <p>Token</p>
        <pre className={code}>
          {JSON.stringify(window.DRONE_CI_BUTLER_TOKEN, null, 2)}
        </pre>
      </div>
    </>
  );
}

export default Settings;
