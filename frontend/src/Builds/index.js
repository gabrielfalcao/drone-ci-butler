import React from "react";
import { useAuth } from "drone-ci-butler/auth";
import Screen from "drone-ci-butler/components/Screen";

import NotAuthenticated from "drone-ci-butler/components/NotAuthenticated";

function Builds() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <NotAuthenticated />;
  }
  return (
    <Screen>
      <h1>Your list of (failed) builds goes here</h1>
    </Screen>
  );
}

export default Builds;
