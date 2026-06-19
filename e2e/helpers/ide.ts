import { expect, type Page } from "@playwright/test";

import { waitForTerminalText } from "./terminal.js";

export async function waitForIdeReady(page: Page): Promise<void> {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.waitForFunction(
    () =>
      Boolean(
        (window as unknown as { __e2eSetCode?: unknown }).__e2eSetCode &&
          (window as unknown as { __e2eSendStdin?: unknown }).__e2eSendStdin,
      ),
    { timeout: 20_000 },
  );
  await expect(page.getByTestId("ide-run-btn")).toBeVisible();
}

export async function clickRun(page: Page): Promise<void> {
  await page.getByTestId("ide-run-btn").click();
}

export async function clickStop(page: Page): Promise<void> {
  await page.getByTestId("ide-stop-btn").click();
}

export async function waitForRunIdle(
  page: Page,
  timeoutMs = 15_000,
): Promise<void> {
  const runBtn = page.getByTestId("ide-run-btn");
  await expect(runBtn).toBeEnabled({ timeout: timeoutMs });
  await expect(runBtn).toHaveText("[ RUN ]");
}

export async function waitForNasmCompiled(
  page: Page,
  timeoutMs = 30_000,
): Promise<void> {
  const panel = page.locator(".ide-nasm-panel");
  await expect(panel).toContainText("global _start", { timeout: timeoutMs });
  await expect(panel).not.toContainText("aguardando compilacao", {
    timeout: 5_000,
  });
}

export async function waitForExecReady(
  page: Page,
  timeoutMs = 25_000,
): Promise<void> {
  await page.waitForFunction(
    () =>
      (window as unknown as { __e2eExecReady?: boolean }).__e2eExecReady ===
      true,
    { timeout: timeoutMs },
  );
}

export async function waitForExecuting(
  page: Page,
  timeoutMs = 25_000,
): Promise<void> {
  await waitForExecReady(page, timeoutMs);
  await expect(page.getByTestId("ide-stop-btn")).toBeEnabled({
    timeout: 5_000,
  });
}

export async function setEditorCode(page: Page, code: string): Promise<void> {
  const marker = code.trim().split("\n")[0];

  await page.evaluate((nextCode) => {
    const setter = (
      window as unknown as { __e2eSetCode?: (c: string) => void }
    ).__e2eSetCode;
    if (!setter) throw new Error("__e2eSetCode indisponivel");
    setter(nextCode);
  }, code);

  await expect(
    page.locator(".ide-editor-host .view-lines").first(),
  ).toContainText(marker, { timeout: 8_000 });
}

/** Run e espera NASM gerado (nao exige fim da execucao). */
export async function clickRunUntilNasm(page: Page): Promise<void> {
  await clickRun(page);
  await waitForTerminalText(page, /compile_and_run/i, 10_000);
  await waitForNasmCompiled(page);
}

export async function sendStdin(page: Page, input: string): Promise<void> {
  await page.evaluate((data) => {
    const send = (
      window as unknown as { __e2eSendStdin?: (d: string) => void }
    ).__e2eSendStdin;
    if (!send) throw new Error("__e2eSendStdin indisponivel");
    send(data);
  }, input);
}

export async function runDemoAndType(page: Page, input: string): Promise<void> {
  await clickRun(page);
  await waitForTerminalText(page, /compile_and_run/i, 10_000);
  await waitForExecuting(page);
  await sendStdin(page, input);
}

export async function cleanupPendingRun(page: Page): Promise<void> {
  try {
    const stopBtn = page.getByTestId("ide-stop-btn");
    if (await stopBtn.isEnabled({ timeout: 500 })) {
      await stopBtn.click();
      await waitForRunIdle(page, 12_000);
    }
  } catch {
    // ignora
  }
}
