import { render, screen } from "@testing-library/react";
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
