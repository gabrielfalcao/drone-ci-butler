import React from "react";
import { useAuth } from "drone-ci-butler/auth";
import Screen from "drone-ci-butler/components/Screen";

import NotAuthenticated from "drone-ci-butler/components/NotAuthenticated";

function Settings() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <NotAuthenticated />;
  }
  return (
    <Screen>
      <h1>Settings Page</h1>
    </Screen>
  );
}

export default Settings;
