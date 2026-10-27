"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, buenosAiresToday, pesos, ProfitReport } from "@/lib/api";

interface Props { onError: (reason: unknown) => void }

export function Profitability({ onError }: Props) {
  const today = buenosAiresToday();
  const [from, setFrom] = useState(today.slice(0, 8) + "01");
  const [to, setTo] = useState(today);
  const [data, setData] = useState<ProfitReport | null>(null);
  const [loading, setLoading] = useState(true);

  async function load(start: string, end: string) {
    setLoading(true);
    try {
      setData(await api.profitability(start, end));
    } catch (error) {
      onError(error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(from, to);
    // Fetch initial period once when the user opens the section.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function submit(event: FormEvent) {
    event.preventDefault();
    load(from, to);
  }

  return (
    <section aria-labelledby="profit-title">
      <div className="section-heading">
        <div><p className="eyebrow">Resultados</p><h2 id="profit-title">Rentabilidad bruta</h2></div>
      </div>
      <p className="muted">Ingresos menos insumos asociados a cada venta. No incluye alquiler, sueldos, impuestos, servicios, comisiones ni mermas.</p>
      <form className="period-form" onSubmit={submit}>
        <label>Desde<input type="date" required value={from} onChange={(event) => setFrom(event.target.value)} /></label>
        <label>Hasta<input type="date" required value={to} onChange={(event) => setTo(event.target.value)} /></label>
        <button className="primary" disabled={loading}>Consultar</button>
      </form>
      {loading && <p className="muted" role="status">Calculando rentabilidad…</p>}
      {data && !loading && <>
        <div className="profit-kpis">
          <article><small>Facturación total</small><strong>{pesos(data.total_revenue)}</strong></article>
          <article><small>Ventas con costo conocido</small><strong>{pesos(data.known_revenue)}</strong></article>
          <article><small>Costo de esos insumos</small><strong>{pesos(data.known_cost)}</strong></article>
          <article><small>Ganancia bruta calculable</small><strong>{pesos(data.gross_profit)}</strong></article>
          <article><small>Margen bruto calculable</small><strong>{data.gross_margin_pct === null ? "Sin datos" : Number(data.gross_margin_pct).toFixed(1) + "%"}</strong></article>
        </div>
        {data.missing_lines > 0 && <p className="cost-warning" role="status">
          Hay {data.missing_lines} renglones de venta sin costo histórico completo, por {pesos(data.unknown_revenue)}.
          Se excluyen del cálculo de ganancia y margen, aunque sí están incluidos en la facturación total.
          Las ventas anteriores a la configuración de costos tampoco pueden calcularse automáticamente.
        </p>}
        <section className="cost-panel">
          <h3>Por producto</h3>
          <div className="cost-table-scroll">
            <table className="cost-table">
              <thead><tr><th>Producto</th><th>Facturado</th><th>Costo conocido</th><th>Ganancia bruta</th><th>Margen</th><th>Sin costo</th></tr></thead>
              <tbody>{data.products.map((product) => <tr key={product.product_id}>
                <td>{product.name}</td>
                <td>{pesos(product.revenue)}</td>
                <td>{pesos(product.known_cost)}</td>
                <td>{pesos(product.gross_profit)}</td>
                <td>{product.gross_margin_pct === null ? "—" : Number(product.gross_margin_pct).toFixed(1) + "%"}</td>
                <td>{product.missing_lines}</td>
              </tr>)}</tbody>
            </table>
            {!data.products.length && <p className="muted">No hay ventas no anuladas en este período.</p>}
          </div>
        </section>
        <p className="muted">El margen se calcula exclusivamente sobre ventas con recetas y costos completos. Las compras se usan para actualizar el costo de cada insumo, no se descuentan nuevamente de la ganancia.</p>
      </>}
    </section>
  );
}
