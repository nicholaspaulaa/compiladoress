import { test } from "@playwright/test";

import { ensureLoggedIn } from "../helpers/auth.js";
import {
  cleanupPendingRun,
  clickRun,
  clickStop,
  waitForExecuting,
  waitForIdeReady,
  waitForRunIdle,
} from "../helpers/ide.js";
import { waitForTerminalText } from "../helpers/terminal.js";

test.describe("Stop", () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
    await waitForIdeReady(page);
  });

  test.afterEach(async ({ page }) => {
    await cleanupPendingRun(page);
  });

  test("Stop interrompe execucao aguardando leia", async ({ page }) => {
    await clickRun(page);
    await waitForExecuting(page);

    await clickStop(page);
    await waitForTerminalText(page, /interrompido/i, 12_000);
    await waitForRunIdle(page);
  });
});
