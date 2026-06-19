import { expect, test } from "@playwright/test";

import { ensureLoggedIn } from "../helpers/auth.js";
import {
  cleanupPendingRun,
  clickRunUntilNasm,
  setEditorCode,
  waitForIdeReady,
} from "../helpers/ide.js";

const HELLO_CODE = `programa hello
inicio
  escreval 1;
fim
`;

test.describe("Run", () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
    await waitForIdeReady(page);
  });

  test.afterEach(async ({ page }) => {
    await cleanupPendingRun(page);
  });

  test("editar codigo, Run e ver NASM gerado", async ({ page }) => {
    test.setTimeout(40_000);
    await setEditorCode(page, HELLO_CODE);
    await clickRunUntilNasm(page);
    await expect(page.locator(".ide-nasm-panel")).toContainText("print_int");
    await cleanupPendingRun(page);
  });
});
