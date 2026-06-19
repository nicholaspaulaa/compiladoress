import { test } from "@playwright/test";

import { ensureLoggedIn } from "../helpers/auth.js";
import {
  cleanupPendingRun,
  runDemoAndType,
  waitForIdeReady,
  waitForRunIdle,
} from "../helpers/ide.js";
import { waitForTerminalText } from "../helpers/terminal.js";

test.describe("Stdin (leia)", () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
    await waitForIdeReady(page);
  });

  test.afterEach(async ({ page }) => {
    await cleanupPendingRun(page);
  });

  test("stdin interativo envia valor para leia e imprime resultado", async ({
    page,
  }) => {
    test.setTimeout(50_000);
    await runDemoAndType(page, "42\n");
    await waitForTerminalText(page, /(^|\n)42(\n|$)/, 25_000);
    await waitForRunIdle(page);
  });
});
