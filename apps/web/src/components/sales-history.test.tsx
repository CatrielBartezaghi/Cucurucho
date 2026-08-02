import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SalesHistory } from "./sales-history";

const sale = {
  id: "s1",
  payment_method: "cash" as const,
  total: "1000.00",
  sold_at: "2026-08-01T15:00:00Z",
  sale_day: "2026-08-01",
  observation: null,
  annulment: null,
  details: [{ id: "d1", product_id: "p1", product_name: "Palito", unit_price: "1000.00", quantity: 1, position: 0 }],
};

it("cancela una Anulación antes de llamar al contrato HTTP", async () => {
  vi.spyOn(window, "prompt").mockReturnValue("Error de carga");
  vi.spyOn(window, "confirm").mockReturnValue(false);
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  render(<SalesHistory day="2026-08-01" history={{ day: "2026-08-01", total_sold: "1000.00", sales: [sale] }} onDayChange={vi.fn()} onRefresh={vi.fn()} onError={vi.fn()} />);

  const summary = screen.getByText("Efectivo").closest("summary");
  expect(summary).not.toBeNull();
  await user.click(summary!);
  await user.click(screen.getByRole("button", { name: "Anular Venta" }));
  expect(window.confirm).toHaveBeenCalled();
  expect(fetchMock).not.toHaveBeenCalled();
});

it("muestra el Precio de venta unitario conservado en cada Detalle de venta", async () => {
  const user = userEvent.setup();
  render(<SalesHistory day="2026-08-01" history={{ day: "2026-08-01", total_sold: "1000.00", sales: [sale] }} onDayChange={vi.fn()} onRefresh={vi.fn()} onError={vi.fn()} />);

  await user.click(screen.getByText("Efectivo").closest("summary")!);

  expect(screen.getByText("$ 1.000,00 c/u")).toBeInTheDocument();
});

it("conserva el Motivo de anulación para reintentar después de un error recuperable", async () => {
  const prompt = vi.spyOn(window, "prompt").mockReturnValue(" Error de carga ");
  vi.spyOn(window, "confirm").mockReturnValue(true);
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
    code: "temporary_error", message: "Reintentá.", field_errors: {},
  }), { status: 503, headers: { "Content-Type": "application/json" } })));
  const onError = vi.fn();
  const user = userEvent.setup();
  render(<SalesHistory day="2026-08-01" history={{ day: "2026-08-01", total_sold: "1000.00", sales: [sale] }} onDayChange={vi.fn()} onRefresh={vi.fn()} onError={onError} />);
  await user.click(screen.getByText("Efectivo").closest("summary")!);

  await user.click(screen.getByRole("button", { name: "Anular Venta" }));
  await waitFor(() => expect(onError).toHaveBeenCalled());
  await user.click(screen.getByRole("button", { name: "Anular Venta" }));

  expect(prompt).toHaveBeenNthCalledWith(2, "Motivo de anulación", " Error de carga ");
});

it("conserva la Observación para reintentar después de un error recuperable", async () => {
  const prompt = vi.spyOn(window, "prompt").mockReturnValue(" Cliente habitual ");
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
    code: "temporary_error", message: "Reintentá.", field_errors: {},
  }), { status: 503, headers: { "Content-Type": "application/json" } })));
  const onError = vi.fn();
  const user = userEvent.setup();
  render(<SalesHistory day="2026-08-01" history={{ day: "2026-08-01", total_sold: "1000.00", sales: [sale] }} onDayChange={vi.fn()} onRefresh={vi.fn()} onError={onError} />);
  await user.click(screen.getByText("Efectivo").closest("summary")!);

  await user.click(screen.getByRole("button", { name: "Agregar Observación" }));
  await waitFor(() => expect(onError).toHaveBeenCalled());
  await user.click(screen.getByRole("button", { name: "Agregar Observación" }));

  expect(prompt).toHaveBeenNthCalledWith(2, "Observación", " Cliente habitual ");
});

it("muestra progreso sin combinar el nuevo Día de venta con datos anteriores", () => {
  render(<SalesHistory day="2026-08-02" history={null} loading onDayChange={vi.fn()} onRefresh={vi.fn()} onError={vi.fn()} />);

  expect(screen.getByText("Consultando Ventas…")).toBeInTheDocument();
  expect(screen.queryByText("Total vendido")).not.toBeInTheDocument();
});
