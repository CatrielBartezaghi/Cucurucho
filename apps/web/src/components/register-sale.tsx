"use client";

import { useMemo, useState } from "react";
import { addMoney, api, PaymentMethod, pesos, Product, Sale } from "@/lib/api";

interface CartLine {
  localId: string;
  product: Product;
  quantity: number;
}

const paymentMethods: Array<[PaymentMethod, string]> = [
  ["cash", "Efectivo"],
  ["transfer", "Transferencia"],
  ["debit_card", "Tarjeta de débito"],
  ["credit_card", "Tarjeta de crédito"],
  ["qr", "QR"],
];

interface Props {
  products: Product[];
  onConfirmed: (sale: Sale) => void;
  onError: (reason: unknown) => void;
}

export function RegisterSale({ products, onConfirmed, onError }: Props) {
  const [cart, setCart] = useState<CartLine[]>([]);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | "">("");
  const [busy, setBusy] = useState(false);
  const [state, setState] = useState<"editing" | "pending" | "uncertain" | "confirmed">("editing");
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());
  const [confirmedSale, setConfirmedSale] = useState<Sale | null>(null);
  const total = useMemo(
    () => addMoney(cart.map((line) => ({ price: line.product.price, quantity: line.quantity }))),
    [cart],
  );

  function add(product: Product) {
    setCart((current) => [...current, { localId: crypto.randomUUID(), product, quantity: 1 }]);
    setState("editing");
  }

  function quantity(localId: string, delta: number) {
    setCart((current) =>
      current.map((line) =>
        line.localId === localId ? { ...line, quantity: Math.max(1, line.quantity + delta) } : line,
      ),
    );
  }

  async function confirm() {
    if (!paymentMethod || cart.length === 0 || busy) return;
    setBusy(true);
    setState("pending");
    try {
      const sale = await api.confirmSale(
        idempotencyKey,
        paymentMethod,
        cart.map((line) => ({ product_id: line.product.id, quantity: line.quantity })),
      );
      setConfirmedSale(sale);
      setCart([]);
      setPaymentMethod("");
      setIdempotencyKey(crypto.randomUUID());
      setState("confirmed");
      onConfirmed(sale);
    } catch (reason) {
      if (reason instanceof TypeError) setState("uncertain");
      else {
        setState("editing");
        onError(reason);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby="sale-title">
      <div className="section-heading">
        <div><p className="eyebrow">Mostrador</p><h2 id="sale-title">Nueva Venta</h2></div>
        <span className="pill">{cart.length} detalles</span>
      </div>
      <div className="sale-layout">
        <div>
          <h3 className="subheading">Elegí Productos</h3>
          {products.length === 0 ? <p className="empty">No hay Productos activos.</p> : (
            <div className="picker-grid">
              {products.map((product) => (
                <button className="picker" key={product.id} aria-label={`Agregar ${product.name}`} onClick={() => add(product)}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={product.image_url ?? "/product-placeholder.svg"} alt="" />
                  <span>{product.name}</span><strong>{pesos(product.price)}</strong>
                </button>
              ))}
            </div>
          )}
        </div>
        <aside className="cart" aria-label="Selección en curso">
          <h3>Selección</h3>
          {cart.length === 0 ? <p className="empty">Agregá un Producto para comenzar.</p> : (
            <ol className="cart-lines">
              {cart.map((line) => (
                <li key={line.localId}>
                  <div><strong>{line.product.name}</strong><small>{pesos(line.product.price)} c/u</small></div>
                  <div className="quantity" aria-label={`Cantidad de ${line.product.name}`}>
                    <button onClick={() => quantity(line.localId, -1)} disabled={line.quantity === 1}>−</button>
                    <span>{line.quantity}</span>
                    <button onClick={() => quantity(line.localId, 1)}>+</button>
                  </div>
                  <button className="remove" aria-label={`Quitar ${line.product.name}`} onClick={() => setCart((current) => current.filter((item) => item.localId !== line.localId))}>×</button>
                </li>
              ))}
            </ol>
          )}
          <div className="total"><span>Total</span><strong>{pesos(total)}</strong></div>
          <fieldset>
            <legend>Medio de pago</legend>
            <div className="payment-grid">
              {paymentMethods.map(([value, label]) => <label key={value}><input type="radio" name="payment" value={value} checked={paymentMethod === value} onChange={() => setPaymentMethod(value)} />{label}</label>)}
            </div>
          </fieldset>
          <button className="primary confirm" disabled={busy || cart.length === 0 || !paymentMethod} onClick={confirm}>
            {busy ? "Confirmando…" : state === "uncertain" ? "Comprobar confirmación" : "Confirmar Venta"}
          </button>
          <p className="status" aria-live="polite">
            {state === "pending" && "Confirmación en curso."}
            {state === "uncertain" && "No pudimos comprobar el resultado. Reintentá para reconciliar la misma Venta."}
            {state === "confirmed" && confirmedSale && `Venta confirmada por ${pesos(confirmedSale.total)}.`}
          </p>
        </aside>
      </div>
    </section>
  );
}
