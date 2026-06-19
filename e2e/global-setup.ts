import { requireTestCredentials } from "./helpers/auth.js";

const baseUrl = process.env.E2E_BASE_URL ?? "http://localhost";

export default async function globalSetup(): Promise<void> {
  requireTestCredentials();

  const deadline = Date.now() + 120_000;
  let lastError = "desconhecido";

  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseUrl}/api/health`);
      if (response.ok) {
        return;
      }
      lastError = `HTTP ${response.status}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await new Promise((resolve) => setTimeout(resolve, 2_000));
  }

  throw new Error(
    `Stack E2E indisponivel em ${baseUrl}/api/health (${lastError}). ` +
      "Suba: docker compose up --build",
  );
}
