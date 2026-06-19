import { test } from "@playwright/test";

import { ensureLoggedIn } from "../helpers/auth.js";
import {
  cleanupPendingRun,
  clickRun,
  setEditorCode,
  waitForIdeReady,
  waitForRunIdle,
} from "../helpers/ide.js";
import { waitForTerminalText } from "../helpers/terminal.js";

const INFINITE_LOOP_CODE = `programa loop
inteiro x;
inicio
  x <- 1;
  enquanto x = 1 faca
    escreval x;
  fimenquanto
fim
`;

test.describe("Timeout", () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
    await waitForIdeReady(page);
  });

  test.afterEach(async ({ page }) => {
    await cleanupPendingRun(page);
  });

  test("loop infinito dispara timeout apos ~10s", async ({ page }) => {
    test.setTimeout(35_000);

    await setEditorCode(page, INFINITE_LOOP_CODE);
    await clickRun(page);
    await waitForTerminalText(page, /compile_and_run/i, 10_000);
    await waitForTerminalText(page, /timeout\s*\(\s*10\s*s\s*\)/i, 18_000);
    await waitForRunIdle(page);
  });
});
