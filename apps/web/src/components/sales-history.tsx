"use client";

import { useState } from "react";
import { api, pesos, Sale, SalesByDay } from "@/lib/api";

const paymentLabels: Record<Sale["payment_method"], string> = {
  cash: "Efectivo",
  transfer: "Transferencia",
  debit_card: "Tarjeta de débito",
  credit_card: "Tarjeta de crédito",
  qr: "QR",
};

interface Props {
  day: string;
  history: SalesByDay;
  onDayChange: (day: string) => void;
  onRefresh: () => Promise<void>;
  onError: (reason: unknown) => void;
}

export function SalesHistory({ day, history, onDayChange, onRefresh, onError }: Props) {
  const [busyId, setBusyId] = useState<string | null>(null);

  async function annul(sale: Sale) {
    const reason = window.prompt("Motivo de anulación");
    if (reason === null) return;
    if (!window.confirm("La Anulación es irreversible. ¿Confirmás que querés anular esta Venta?")) return;
    await action(sale.id, () => api.annulSale(sale.id, reason));
  }

  async function observation(sale: Sale) {
    const value = window.prompt("Observación", sale.observation ?? "");
    if (value === null) return;
    await action(sale.id, () => value.trim() ? api.saveObservation(sale.id, value) : api.removeObservation(sale.id));
  }

  async function action(id: string, task: () => Promise<unknown>) {
    setBusyId(id);
    try {
      await task();
      await onRefresh();
    } catch (reason) {
      onError(reason);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section aria-labelledby="history-title">
      <div className="section-heading">
        <div><p className="eyebrow">Historial</p><h2 id="history-title">Ventas del día</h2></div>
        <label className="date-picker">Día de venta<input type="date" value={day} onChange={(event) => onDayChange(event.target.value)} /></label>
      </div>
      <div className="day-total"><span>Total vendido</span><strong>{pesos(history.total_sold)}</strong></div>
      {history.sales.length === 0 ? <p className="empty large">No hay Ventas registradas para este día.</p> : (
        <div className="sales-list">
          {history.sales.map((sale) => (
            <details className={sale.annulment ? "sale-card annulled" : "sale-card"} key={sale.id}>
              <summary>
                <div><strong>{new Intl.DateTimeFormat("es-AR", { timeStyle: "short", timeZone: "America/Argentina/Buenos_Aires" }).format(new Date(sale.sold_at))}</strong><span>{paymentLabels[sale.payment_method]}</span></div>
                <div><strong>{pesos(sale.total)}</strong><span>{sale.annulment ? "Anulada" : "Confirmada"}</span></div>
              </summary>
              <div className="sale-details">
                <ul>{sale.details.map((detail) => <li key={detail.id}><span>{detail.quantity} × {detail.product_name}</span><strong>{pesos(String(Number(detail.unit_price) * detail.quantity))}</strong></li>)}</ul>
                {sale.observation && <p><strong>Observación:</strong> {sale.observation}</p>}
                {sale.annulment && <p className="annulment"><strong>Motivo de anulación:</strong> {sale.annulment.reason}</p>}
                <div className="row-actions">
                  <button className="ghost" disabled={busyId === sale.id} onClick={() => observation(sale)}>{sale.observation ? "Editar Observación" : "Agregar Observación"}</button>
                  {!sale.annulment && <button className="danger" disabled={busyId === sale.id} onClick={() => annul(sale)}>Anular Venta</button>}
                </div>
              </div>
            </details>
          ))}
        </div>
      )}
    </section>
  );
}

