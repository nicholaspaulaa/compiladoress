import { expect, type Page } from "@playwright/test";

export function requireTestCredentials(): { email: string; password: string } {
  const email = process.env.E2E_TEST_EMAIL;
  const password = process.env.E2E_TEST_PASSWORD;
  if (!email || !password) {
    throw new Error(
      "Defina E2E_TEST_EMAIL e E2E_TEST_PASSWORD (veja e2e/.env.example)",
    );
  }
  return { email, password };
}

export async function login(page: Page): Promise<void> {
  const { email, password } = requireTestCredentials();

  await page.goto("/login");
  await page.locator("#email").fill(email);
  await page.locator("#password").fill(password);
  await page.getByRole("button", { name: /ENTRAR/i }).click();

  await expect(page).toHaveURL("/");
  await expect(
    page.getByRole("heading", { name: "SIMPLES EDITOR" }),
  ).toBeVisible();
}

export async function ensureLoggedIn(page: Page): Promise<void> {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  if (page.url().includes("/login")) {
    await login(page);
  }
}
