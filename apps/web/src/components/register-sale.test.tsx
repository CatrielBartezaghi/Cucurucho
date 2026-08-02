import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RegisterSale } from "./register-sale";

const product = { id: "p1", name: "Cucurucho", price: "1200.50", active: true, image_url: null };

describe("armado y confirmación de una Venta", () => {
  it("conserva Productos repetidos como detalles y limpia solo tras respuesta autoritativa", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      id: "s1",
      payment_method: "qr",
      total: "2401.00",
      sold_at: "2026-08-01T15:00:00Z",
      sale_day: "2026-08-01",
      observation: null,
      annulment: null,
      details: [],
    }), { status: 201, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);
    const onConfirmed = vi.fn();
    const user = userEvent.setup();
    render(<RegisterSale products={[product]} onConfirmed={onConfirmed} onError={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Agregar Cucurucho" }));
    await user.click(screen.getByRole("button", { name: "Agregar Cucurucho" }));
    expect(screen.getAllByText("Cucurucho")).toHaveLength(3);
    expect(screen.getByText("$ 2.401,00")).toBeInTheDocument();
    await user.click(screen.getByLabelText("QR"));
    await user.click(screen.getByRole("button", { name: "Confirmar Venta" }));

    await waitFor(() => expect(onConfirmed).toHaveBeenCalled());
    const request = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(request.details).toEqual([
      { product_id: "p1", quantity: 1 },
      { product_id: "p1", quantity: 1 },
    ]);
    expect(screen.getByText("Agregá un Producto para comenzar.")).toBeInTheDocument();
  });

  it("conserva la selección y la misma clave ante una respuesta no comprobable", async () => {
    const fetchMock = vi.fn().mockRejectedValueOnce(new TypeError("network")).mockResolvedValueOnce(
      new Response(JSON.stringify({
        id: "s1", payment_method: "cash", total: "1200.50", sold_at: "2026-08-01T15:00:00Z",
        sale_day: "2026-08-01", observation: null, annulment: null, details: [],
      }), { status: 200, headers: { "Content-Type": "application/json" } }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<RegisterSale products={[product]} onConfirmed={vi.fn()} onError={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Agregar Cucurucho" }));
    await user.click(screen.getByLabelText("Efectivo"));
    await user.click(screen.getByRole("button", { name: "Confirmar Venta" }));
    expect(await screen.findByText(/No pudimos comprobar/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Comprobar confirmación" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(new Headers(fetchMock.mock.calls[0][1].headers).get("Idempotency-Key")).toBe(
      new Headers(fetchMock.mock.calls[1][1].headers).get("Idempotency-Key"),
    );
  });
});
