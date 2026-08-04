"use client";

import { useState } from "react";
import { api, multiplyMoney, pesos, Sale, SalesByDay } from "@/lib/api";
import { paymentMethodLabels } from "@/lib/payment-methods";

interface Props {
  day: string;
  history: SalesByDay | null;
  loading?: boolean;
  onDayChange: (day: string) => void;
  onRefresh: () => Promise<void>;
  onError: (reason: unknown) => void;
}

export function SalesHistory({ day, history, loading = false, onDayChange, onRefresh, onError }: Props) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [annulmentDrafts, setAnnulmentDrafts] = useState<Record<string, string>>({});
  const [observationDrafts, setObservationDrafts] = useState<Record<string, string>>({});

  async function annul(sale: Sale) {
    const reason = window.prompt("Motivo de anulación", annulmentDrafts[sale.id] ?? "");
    if (reason === null) return;
    if (!reason.trim()) {
      window.alert("Ingresá un motivo de anulación.");
      return;
    }
    setAnnulmentDrafts((current) => ({ ...current, [sale.id]: reason }));
    if (!window.confirm("La Anulación es irreversible. ¿Confirmás que querés anular esta Venta?")) return;
    if (await action(sale.id, () => api.annulSale(sale.id, reason))) {
      setAnnulmentDrafts((current) => {
        const next = { ...current };
        delete next[sale.id];
        return next;
      });
    }
  }

  async function observation(sale: Sale) {
    const value = window.prompt(
      "Observación",
      observationDrafts[sale.id] ?? sale.observation ?? "",
    );
    if (value === null) return;
    setObservationDrafts((current) => ({ ...current, [sale.id]: value }));
    if (await action(sale.id, () => value.trim() ? api.saveObservation(sale.id, value) : api.removeObservation(sale.id))) {
      setObservationDrafts((current) => {
        const next = { ...current };
        delete next[sale.id];
        return next;
      });
    }
  }

  async function action(id: string, task: () => Promise<unknown>): Promise<boolean> {
    setBusyId(id);
    try {
      await task();
      await onRefresh();
      return true;
    } catch (reason) {
      onError(reason);
      return false;
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
      {loading ? <p className="empty large" aria-live="polite">Consultando Ventas…</p> : history === null ? (
        <p className="empty large">No pudimos cargar las Ventas de este día. Reintentá la consulta.</p>
      ) : <>
      <div className="day-total"><span>Total vendido</span><strong>{pesos(history.total_sold)}</strong></div>
      {history.sales.length === 0 ? <p className="empty large">No hay Ventas registradas para este día.</p> : (
        <div className="sales-list">
          {history.sales.map((sale) => (
            <details className={sale.annulment ? "sale-card annulled" : "sale-card"} key={sale.id}>
              <summary>
                <div><strong>{new Intl.DateTimeFormat("es-AR", { timeStyle: "short", timeZone: "America/Argentina/Buenos_Aires" }).format(new Date(sale.sold_at))}</strong><span>{paymentMethodLabels[sale.payment_method]}</span></div>
                <div><strong>{pesos(sale.total)}</strong><span>{sale.annulment ? "Anulada" : "Confirmada"}</span></div>
              </summary>
              <div className="sale-details">
                <ul>{sale.details.map((detail) => <li key={detail.id}><span>{detail.quantity} × {detail.product_name}<small>{pesos(detail.unit_price)} c/u</small></span><strong>{pesos(multiplyMoney(detail.unit_price, detail.quantity))}</strong></li>)}</ul>
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
      </>}
    </section>
  );
}
