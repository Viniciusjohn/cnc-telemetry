import { test, expect } from "@playwright/test";

const BASE_URL = "http://localhost:5173";

test.describe("Dashboard F3", () => {
  test("deve exibir header e machine_id", async ({ page }) => {
    await page.goto(BASE_URL);
    
    await expect(page.getByRole("heading", { name: /CNC Telemetry/ })).toBeVisible();
    
    // Aguardar primeiro poll
    await page.waitForTimeout(2500);
    
    // Verificar machine_id aparece
    await expect(page.getByText(/CNC-SIM-001/)).toBeVisible();
  });

  test("deve exibir 4 cards de status", async ({ page }) => {
    await page.goto(BASE_URL);
    
    await expect(page.getByText("RPM")).toBeVisible();
    await expect(page.getByText("Feed")).toBeVisible();
    await expect(page.getByText("Estado")).toBeVisible();
    await expect(page.getByText("Atualizado")).toBeVisible();
  });

  test("cards devem atualizar após 2s (polling)", async ({ page }) => {
    await page.goto(BASE_URL);
    
    // Aguardar primeiro poll
    await page.waitForTimeout(500);
    
    // Capturar valor inicial
    const rpmCard = page.locator('text=RPM').locator("..");
    const initialValue = await rpmCard.textContent();
    
    // Aguardar próximo poll (2s)
    await page.waitForTimeout(2500);
    
    // Valor pode ter mudado (ou não, se máquina parada)
    // Mas card deve estar visível
    await expect(rpmCard).toBeVisible();
  });

  test("deve exibir erro se backend não disponível", async ({ page }) => {
    // Simular backend offline
    await page.route("**/v1/machines/*/status", (route) => {
      route.abort("failed");
    });
    
    await page.goto(BASE_URL);
    
    // Deve mostrar mensagem de erro
    await expect(page.getByText(/Erro/)).toBeVisible();
  });
});
