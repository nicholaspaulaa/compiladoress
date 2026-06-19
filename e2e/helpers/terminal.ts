import type { Page } from "@playwright/test";

type XtermBuffer = {
  buffer: {
    active: {
      length: number;
      getLine: (index: number) => { translateToString: (trim?: boolean) => string } | undefined;
    };
  };
};

function readTerminalBuffer(): string {
  const term = (window as unknown as { __xtermTerminal?: XtermBuffer })
    .__xtermTerminal;
  if (!term) {
    return "";
  }

  const lines: string[] = [];
  for (let i = 0; i < term.buffer.active.length; i++) {
    const line = term.buffer.active.getLine(i);
    if (line) {
      const text = line.translateToString(true);
      if (text.trim()) {
        lines.push(text);
      }
    }
  }
  return lines.join("\n");
}

export async function getTerminalText(page: Page): Promise<string> {
  return page.evaluate(readTerminalBuffer);
}

export async function waitForTerminalText(
  page: Page,
  pattern: RegExp | string,
  timeoutMs = 45_000,
): Promise<void> {
  const source = typeof pattern === "string" ? pattern : pattern.source;
  const flags = typeof pattern === "string" ? "i" : pattern.flags;

  await page.waitForFunction(
    ({ reSource, reFlags }) => {
      const term = (window as unknown as { __xtermTerminal?: XtermBuffer })
        .__xtermTerminal;
      if (!term) {
        return false;
      }
      const lines: string[] = [];
      for (let i = 0; i < term.buffer.active.length; i++) {
        const line = term.buffer.active.getLine(i);
        if (line) {
          lines.push(line.translateToString(true));
        }
      }
      const text = lines.join("\n");
      return new RegExp(reSource, reFlags).test(text);
    },
    { reSource: source, reFlags: flags },
    { timeout: timeoutMs },
  );
}

export async function typeInTerminal(page: Page, text: string): Promise<void> {
  await page.locator("#terminal-host").click();
  await page.keyboard.type(text, { delay: 30 });
}
