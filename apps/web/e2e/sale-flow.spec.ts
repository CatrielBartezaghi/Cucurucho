import { expect, test } from "@playwright/test";

test("crea un Producto, confirma, consulta y anula una Venta, y cierra sesión", async ({ page }) => {
  await page.goto("/login");
  const username = page.getByLabel("Usuario");
  const password = page.getByLabel("Contraseña");
  await username.fill(process.env.E2E_USERNAME ?? "operadora");
  await username.press("Tab");
  await expect(password).toBeFocused();
  await password.fill(process.env.E2E_PASSWORD ?? "helado-seguro");
  await password.press("Enter");
  await expect(page.getByRole("heading", { name: "Nueva Venta" })).toBeVisible();

  await page.getByRole("button", { name: "Productos" }).press("Enter");
  const productName = `Cucurucho E2E ${Date.now()}`;
  await page.getByLabel("Nombre").fill(productName);
  await page.getByLabel("Precio").fill("1200.50");
  await page.locator(".create-product").getByLabel("Categoría").selectOption({ label: "Helado" });
  await page.getByRole("button", { name: "Agregar Producto" }).press("Enter");
  await expect(page.getByRole("heading", { name: productName })).toBeVisible();

  await page.getByRole("button", { name: "Nueva venta" }).press("Enter");
  const product = page.getByRole("button", { name: `Agregar ${productName}` });
  await expect(product).toBeVisible();
  await product.press("Enter");
  await page.getByLabel("Efectivo").press("Space");
  await page.getByRole("button", { name: "Confirmar Venta" }).press("Enter");
  await expect(page.getByText(/Venta confirmada por/)).toBeVisible();

  await page.getByRole("button", { name: "Ventas del día" }).press("Enter");
  const total = page.locator(".day-total");
  const totalBefore = parseArgentineMoney(await total.textContent());
  const sale = page.locator(".sale-card").filter({ hasText: productName });
  await expect(sale).toBeVisible();
  await sale.locator("summary").press("Enter");
  page.on("dialog", async (dialog) => {
    await dialog.accept(dialog.type() === "prompt" ? "Error de carga E2E" : undefined);
  });
  await sale.getByRole("button", { name: "Anular Venta" }).press("Enter");
  await expect(sale.getByText("Anulada")).toBeVisible();
  await expect.poll(async () => parseArgentineMoney(await total.textContent())).toBe(totalBefore - 1200.5);
  await page.getByRole("button", { name: "Cerrar sesión" }).press("Enter");
  await expect(page.getByRole("heading", { name: "Cucurucho" })).toBeVisible();
});

function parseArgentineMoney(value: string | null): number {
  const numeric = value?.replace(/[^\d,.-]/g, "").replaceAll(".", "").replace(",", ".") ?? "0";
  return Number(numeric);
}
