import { describe, expect, it, vi } from "vitest";
import { addMoney, api, buenosAiresToday, SessionExpiredError } from "./api";

describe("adaptador HTTP", () => {
  it("convierte una sesión vencida en una señal única para la interfaz", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      code: "session_required",
      message: "Tu sesión venció o fue revocada. Iniciá sesión nuevamente.",
      field_errors: {},
    }), { status: 401, headers: { "Content-Type": "application/json" } })));

    await expect(api.products()).rejects.toBeInstanceOf(SessionExpiredError);
  });

  it("calcula importes provisionales en centavos y no con suma binaria", () => {
    expect(addMoney([{ price: "0.10", quantity: 1 }, { price: "0.20", quantity: 1 }])).toBe("0.30");
    expect(addMoney([{ price: "4500.00", quantity: 2 }, { price: "1200.50", quantity: 3 }])).toBe("12601.50");
  });

  it("calcula el Día de venta en Buenos Aires aunque UTC ya sea el día siguiente", () => {
    expect(buenosAiresToday(new Date("2026-08-02T01:30:00Z"))).toBe("2026-08-01");
  });
});

