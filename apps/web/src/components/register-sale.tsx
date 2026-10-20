"use client";

import { useMemo, useState } from "react";
import { api, Category, PaymentMethod, pesos, Product, Sale } from "@/lib/api";
import { paymentMethods } from "@/lib/payment-methods";

interface CartLine {
  localId: string;
  product: Product;
  quantity: number;
  weightKg: string;
  amount: string;
  entryMethod: "weight" | "amount";
}

interface Props {
  products: Product[];
  categories?: Category[];
  onConfirmed: (sale: Sale) => void;
  onError: (reason: unknown) => void;
}

export function RegisterSale({ products, categories, onConfirmed, onError }: Props) {
  const [cart, setCart] = useState<CartLine[]>([]);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | "">("");
  const [busy, setBusy] = useState(false);
  const [state, setState] = useState<"editing" | "pending" | "uncertain" | "confirmed">("editing");
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());
  const [confirmedSale, setConfirmedSale] = useState<Sale | null>(null);
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<string[]>([]);
  const availableCategories = useMemo(
    () =>
      categories ??
      Array.from(new Map(products.map((product) => [product.category.id, product.category])).values()),
    [categories, products],
  );
  const visibleProducts = useMemo(
    () =>
      selectedCategoryIds.length === 0
        ? products
        : products.filter((product) => selectedCategoryIds.includes(product.category.id)),
    [products, selectedCategoryIds],
  );
  const total = useMemo(() => {
    const cents = cart.reduce((sum, line) => {
      if (line.product.pricing_type === "weight") {
        const amount = parseDecimal(line.amount);
        return sum + (Number.isFinite(amount) && amount > 0 ? Math.round(amount * 100) : 0);
      }
      return sum + Math.round(Number(line.product.price) * 100) * line.quantity;
    }, 0);
    return (cents / 100).toFixed(2);
  }, [cart]);
  const validCart = cart.every((line) => line.product.pricing_type !== "weight" || (
    parseDecimal(line.weightKg) > 0 && parseDecimal(line.amount) > 0 &&
    /^\d+(?:[.,]\d{1,3})?$/.test(line.weightKg) &&
    /^\d+(?:[.,]\d{1,2})?$/.test(line.amount)
  ));
  const selectionLocked = busy || state === "uncertain";

  function parseDecimal(value: string): number {
    return Number(value.replace(",", "."));
  }

  function add(product: Product) {
    setCart((current) => [...current, {
      localId: crypto.randomUUID(), product, quantity: 1,
      weightKg: "", amount: "", entryMethod: "weight",
    }]);
    setState("editing");
  }

  function quantity(localId: string, delta: number) {
    setCart((current) =>
      current.map((line) =>
        line.localId === localId ? { ...line, quantity: Math.max(1, line.quantity + delta) } : line,
      ),
    );
  }

  function updateWeight(localId: string, weightKg: string) {
    setCart((current) => current.map((line) => {
      if (line.localId !== localId) return line;
      const weight = parseDecimal(weightKg);
      const amount = weightKg.trim() && Number.isFinite(weight) && weight > 0
        ? (Math.round(weight * Number(line.product.price) * 100) / 100).toFixed(2)
        : "";
      return { ...line, weightKg, amount, entryMethod: "weight" };
    }));
  }

  function updateAmount(localId: string, amount: string) {
    setCart((current) => current.map((line) => {
      if (line.localId !== localId) return line;
      const value = parseDecimal(amount);
      const weightKg = amount.trim() && Number.isFinite(value) && value > 0
        ? (Math.round((value / Number(line.product.price)) * 1000) / 1000).toFixed(3)
        : "";
      return { ...line, amount, weightKg, entryMethod: "amount" };
    }));
  }

  async function confirm() {
    if (!paymentMethod || cart.length === 0 || !validCart || busy) return;
    setBusy(true);
    setState("pending");
    try {
      const sale = await api.confirmSale(
        idempotencyKey,
        paymentMethod,
        cart.map((line) => ({
          product_id: line.product.id, quantity: line.quantity,
          ...(line.product.pricing_type === "weight"
            ? line.entryMethod === "weight"
              ? { weight_kg: line.weightKg.replace(",", ".") }
              : { amount: line.amount.replace(",", ".") }
            : {}),
        })),
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
          <label className="category-filter">
            Filtrar por Categorías
            <select
              multiple
              value={selectedCategoryIds}
              onChange={(event) =>
                setSelectedCategoryIds(
                  Array.from(event.currentTarget.selectedOptions, (option) => option.value),
                )
              }
              aria-label="Filtrar por Categorías"
            >
              {availableCategories.map((category) => (
                <option key={category.id} value={category.id}>{category.name}</option>
              ))}
            </select>
            <small>Elegí una o varias. Sin selección se muestran todas.</small>
          </label>
          {products.length === 0 ? <p className="empty">No hay Productos activos.</p> : (
            visibleProducts.length === 0 ? <p className="empty">No hay Productos en las Categorías seleccionadas.</p> : <div className="picker-grid">
              {visibleProducts.map((product) => (
                <button className="picker" key={product.id} aria-label={`Agregar ${product.name}`} disabled={selectionLocked} onClick={() => add(product)}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={product.image_url ?? "/product-placeholder.svg"} alt="" />
                  <span>{product.name}<small>{product.category.name}</small></span><strong>{pesos(product.price)}{product.pricing_type === "weight" ? " / kg" : ""}</strong>
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
                <li className={line.product.pricing_type === "weight" ? "weighted-sale" : ""} key={line.localId}>
                  <div><strong>{line.product.name}</strong><small>{pesos(line.product.price)} {line.product.pricing_type === "weight" ? "/ kg" : "c/u"}</small></div>
                  {line.product.pricing_type === "weight" ? (
                    <div className="weighted-inputs">
                      <label>Peso (kg)
                        <input
                          aria-label={`Peso en kg de ${line.product.name}`}
                          value={line.weightKg} inputMode="decimal" placeholder="1,250"
                          disabled={selectionLocked}
                          onChange={(event) => updateWeight(line.localId, event.target.value)}
                        />
                      </label>
                      <label>Importe ($)
                        <input
                          aria-label={`Importe de ${line.product.name}`}
                          value={line.amount} inputMode="decimal" placeholder="15000"
                          disabled={selectionLocked}
                          onChange={(event) => updateAmount(line.localId, event.target.value)}
                        />
                      </label>
                      {line.entryMethod === "amount" && <small>Peso estimado según el importe.</small>}
                    </div>
                  ) : (
                    <div className="quantity" aria-label={`Cantidad de ${line.product.name}`}>
                      <button onClick={() => quantity(line.localId, -1)} disabled={selectionLocked || line.quantity === 1}>−</button>
                      <span>{line.quantity}</span>
                      <button onClick={() => quantity(line.localId, 1)} disabled={selectionLocked}>+</button>
                    </div>
                  )}
                  <button className="remove" aria-label={`Quitar ${line.product.name}`} disabled={selectionLocked} onClick={() => setCart((current) => current.filter((item) => item.localId !== line.localId))}>×</button>
                </li>
              ))}
            </ol>
          )}
          <div className="total"><span>Total</span><strong>{pesos(total)}</strong></div>
          <fieldset>
            <legend>Medio de pago</legend>
            <div className="payment-grid">
              {paymentMethods.map(([value, label]) => <label key={value}><input type="radio" name="payment" value={value} checked={paymentMethod === value} disabled={selectionLocked} onChange={() => setPaymentMethod(value)} />{label}</label>)}
            </div>
          </fieldset>
          <button className="primary confirm" disabled={busy || cart.length === 0 || !paymentMethod || !validCart} onClick={confirm}>
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
