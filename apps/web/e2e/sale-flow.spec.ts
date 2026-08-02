import { expect, test } from "@playwright/test";

test("crea un Producto, confirma, consulta y anula una Venta, y cierra sesión", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Usuario").fill(process.env.E2E_USERNAME ?? "operadora");
  await page.getByLabel("Contraseña").fill(process.env.E2E_PASSWORD ?? "helado-seguro");
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page.getByRole("heading", { name: "Nueva Venta" })).toBeVisible();

  await page.getByRole("button", { name: "Productos" }).click();
  const productName = `Cucurucho E2E ${Date.now()}`;
  await page.getByLabel("Nombre").fill(productName);
  await page.getByLabel("Precio").fill("1200.50");
  await page.getByRole("button", { name: "Agregar Producto" }).click();
  await expect(page.getByRole("heading", { name: productName })).toBeVisible();

  await page.getByRole("button", { name: "Nueva venta" }).click();
  const product = page.getByRole("button", { name: `Agregar ${productName}` });
  await expect(product).toBeVisible();
  await product.click();
  await page.getByLabel("Efectivo").click();
  await page.getByRole("button", { name: "Confirmar Venta" }).click();
  await expect(page.getByText(/Venta confirmada por/)).toBeVisible();

  await page.getByRole("button", { name: "Ventas del día" }).click();
  const total = page.locator(".day-total");
  const totalBefore = parseArgentineMoney(await total.textContent());
  const sale = page.locator(".sale-card").filter({ hasText: productName });
  await expect(sale).toBeVisible();
  await sale.locator("summary").click();
  page.on("dialog", async (dialog) => {
    await dialog.accept(dialog.type() === "prompt" ? "Error de carga E2E" : undefined);
  });
  await sale.getByRole("button", { name: "Anular Venta" }).click();
  await expect(sale.getByText("Anulada")).toBeVisible();
  await expect.poll(async () => parseArgentineMoney(await total.textContent())).toBe(totalBefore - 1200.5);
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page.getByRole("heading", { name: "Registro de ventas" })).toBeVisible();
});

function parseArgentineMoney(value: string | null): number {
  const numeric = value?.replace(/[^\d,.-]/g, "").replaceAll(".", "").replace(",", ".") ?? "0";
  return Number(numeric);
}
