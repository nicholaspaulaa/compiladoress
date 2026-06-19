import { expect, test } from "@playwright/test";

import { requireTestCredentials } from "../helpers/auth.js";

test.describe("Login", () => {
  test.beforeAll(() => {
    requireTestCredentials();
  });

  test("login com credenciais de teste redireciona para a IDE", async ({
    page,
  }) => {
    const { email, password } = requireTestCredentials();

    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "SIMPLES EDITOR" })).toBeVisible();

    await page.locator("#email").fill(email);
    await page.locator("#password").fill(password);
    await page.getByRole("button", { name: /ENTRAR/i }).click();

    await expect(page).toHaveURL("/");
    await expect(page.getByTestId("ide-run-btn")).toBeVisible();
    await expect(page.locator("#terminal-host")).toBeVisible();
  });
});
