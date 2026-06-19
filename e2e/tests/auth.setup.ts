import { test as setup } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";

import { login, requireTestCredentials } from "../helpers/auth.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const authFile = path.join(__dirname, "../.auth/user.json");

setup("autenticar usuario de teste", async ({ page }) => {
  requireTestCredentials();
  await login(page);
  await page.context().storageState({ path: authFile });
});
