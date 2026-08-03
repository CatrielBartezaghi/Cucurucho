import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RegisterSale } from "./register-sale";

const helado = { id: "c1", name: "Helado" };
const product = {
  id: "p1",
  name: "Cucurucho",
  price: "1200.50",
  active: true,
  image_url: null,
  category: helado,
};

describe("armado y confirmación de una Venta", () => {
  it("filtra Productos por la unión de las Categorías seleccionadas", async () => {
    const products = [
      product,
      {
        ...product,
        id: "p2",
        name: "Gaseosa",
        category: { id: "c2", name: "Envasado" },
      },
      {
        ...product,
        id: "p3",
        name: "Cuchara",
        category: { id: "c3", name: "Otros" },
      },
    ];
    const user = userEvent.setup();
    render(<RegisterSale products={products} onConfirmed={vi.fn()} onError={vi.fn()} />);

    const categoryFilter = screen.getByRole("listbox", { name: "Filtrar por Categorías" });
    await user.selectOptions(categoryFilter, ["c1", "c3"]);

    expect(screen.getByRole("button", { name: "Agregar Cucurucho" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Agregar Cuchara" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Agregar Gaseosa" })).not.toBeInTheDocument();

    await user.deselectOptions(categoryFilter, ["c1", "c3"]);
    expect(screen.getByRole("button", { name: "Agregar Gaseosa" })).toBeInTheDocument();
  });

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
    expect(screen.getByRole("button", { name: "Agregar Cucurucho" })).toBeDisabled();
    expect(screen.getByLabelText("Efectivo")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Quitar Cucurucho" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Comprobar confirmación" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(new Headers(fetchMock.mock.calls[0][1].headers).get("Idempotency-Key")).toBe(
      new Headers(fetchMock.mock.calls[1][1].headers).get("Idempotency-Key"),
    );
  });
});
