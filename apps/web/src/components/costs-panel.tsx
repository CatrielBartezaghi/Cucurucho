"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  api, pesos, Product, RecipeChange, Supply, SupplyPurchase,
} from "@/lib/api";

interface Props {
  products: Product[];
  onError: (reason: unknown) => void;
}

const currency = (value: string) => pesos(value);

export function CostsPanel({ products, onError }: Props) {
  const [supplies, setSupplies] = useState<Supply[]>([]);
  const [purchases, setPurchases] = useState<SupplyPurchase[]>([]);
  const [supplyName, setSupplyName] = useState("");
  const [supplyUnit, setSupplyUnit] = useState<"kg" | "unit">("kg");
  const [purchaseSupplyId, setPurchaseSupplyId] = useState("");
  const [purchaseQty, setPurchaseQty] = useState("");
  const [purchaseTotal, setPurchaseTotal] = useState("");
  const [productId, setProductId] = useState(products[0]?.id ?? "");
  const [recipeItems, setRecipeItems] = useState<RecipeChange[]>([]);
  const [recipeLoaded, setRecipeLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");

  async function reload() {
    const [nextSupplies, nextPurchases] = await Promise.all([api.supplies(), api.purchases()]);
    setSupplies(nextSupplies);
    setPurchases(nextPurchases);
  }

  useEffect(() => {
    reload().catch(onError);
    // Load on entry; mutations reload explicitly.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!productId) return;
    let cancelled = false;
    setRecipeLoaded(false);
    api.recipe(productId).then((recipe) => {
      if (cancelled) return;
      setRecipeItems(recipe.items.map(({ supply_id, quantity, mode }) => ({ supply_id, quantity, mode })));
      setRecipeLoaded(true);
    }).catch((error) => { if (!cancelled) onError(error); });
    return () => { cancelled = true; };
  }, [productId, onError]);

  async function action(task: () => Promise<void>, success: string) {
    setBusy(true);
    setNotice("");
    try {
      await task();
      setNotice(success);
    } catch (error) {
      onError(error);
    } finally {
      setBusy(false);
    }
  }

  async function addSupply(event: FormEvent) {
    event.preventDefault();
    await action(async () => {
      await api.createSupply(supplyName.trim(), supplyUnit);
      setSupplyName("");
      await reload();
    }, "Insumo agregado.");
  }

  async function editSupply(supply: Supply) {
    const name = window.prompt("Nombre del insumo", supply.name);
    if (name === null) return;
    await action(async () => {
      await api.updateSupply(supply.id, name, supply.active);
      await reload();
    }, "Insumo actualizado.");
  }

  async function toggleSupply(supply: Supply) {
    await action(async () => {
      await api.updateSupply(supply.id, supply.name, !supply.active);
      await reload();
    }, supply.active ? "Insumo inactivado." : "Insumo reactivado.");
  }

  async function addPurchase(event: FormEvent) {
    event.preventDefault();
    await action(async () => {
      await api.createPurchase(purchaseSupplyId, purchaseQty.replace(",", "."), purchaseTotal.replace(",", "."));
      setPurchaseQty("");
      setPurchaseTotal("");
      await reload();
    }, "Compra registrada. El costo vigente del insumo fue actualizado.");
  }

  async function saveRecipe(event: FormEvent) {
    event.preventDefault();
    await action(async () => {
      await api.saveRecipe(productId, recipeItems.map((item) => ({
        ...item, quantity: item.quantity.replace(",", "."),
      })));
      setRecipeLoaded(true);
    }, "Receta guardada. Las ventas anteriores conservan sus costos.");
  }

  const chosenProduct = products.find((product) => product.id === productId);
  const chosenSupply = supplies.find((supply) => supply.id === purchaseSupplyId);
  const validQty = Number(purchaseQty.replace(",", "."));
  const validTotal = Number(purchaseTotal.replace(",", "."));
  const unitPurchaseCost = validQty > 0 && Number.isFinite(validTotal) ? validTotal / validQty : null;
  const missingSupplyPrices = recipeItems.some((item) =>
    supplies.find((supply) => supply.id === item.supply_id)?.current_unit_cost == null
  );
  const estimatedCost = recipeItems.reduce((sum, item) => {
    const supply = supplies.find((element) => element.id === item.supply_id);
    return sum + Number(supply?.current_unit_cost ?? "0") * Number(item.quantity.replace(",", "."));
  }, 0);
  const validCost = recipeItems.length > 0 && !missingSupplyPrices &&
    recipeItems.every((item) => Number(item.quantity.replace(",", ".")) > 0);
  const estimatedProfit = chosenProduct ? Number(chosenProduct.price) - estimatedCost : 0;

  return (
    <section aria-labelledby="supplies-title">
      <div className="section-heading">
        <div><p className="eyebrow">Costos</p><h2 id="supplies-title">Insumos y recetas</h2></div>
        <span className="pill">{supplies.filter((item) => item.active).length} insumos activos</span>
      </div>
      <p className="muted">Registrá compras y asociá los insumos a cada producto. Por ahora no se descuenta stock automáticamente.</p>
      {notice && <p className="success-note" role="status">{notice}</p>}

      <div className="cost-grid">
        <section className="cost-panel">
          <h3>1. Insumos</h3>
          <form className="cost-form" onSubmit={addSupply}>
            <label>Nombre<input value={supplyName} maxLength={150} required onChange={(event) => setSupplyName(event.target.value)} placeholder="Ej. Helado, pote térmico" /></label>
            <label>Unidad<select value={supplyUnit} onChange={(event) => setSupplyUnit(event.target.value as "kg" | "unit")}><option value="kg">Kilogramo (kg)</option><option value="unit">Unidad (u.)</option></select></label>
            <button className="primary" disabled={busy}>Agregar insumo</button>
          </form>
          <div className="cost-table-scroll">
            <table className="cost-table">
              <thead><tr><th>Insumo</th><th>Costo vigente</th><th>Acciones</th></tr></thead>
              <tbody>{supplies.map((supply) => (
                <tr key={supply.id}>
                  <td><strong>{supply.name}</strong><small>{supply.unit === "kg" ? "Por kg" : "Por unidad"}{!supply.active ? " · Inactivo" : ""}</small></td>
                  <td>{supply.current_unit_cost === null ? "Sin compra" : currency(supply.current_unit_cost)}</td>
                  <td><div className="row-actions">
                    <button type="button" className="ghost" disabled={busy} onClick={() => editSupply(supply)}>Editar</button>
                    <button type="button" className="ghost" disabled={busy} onClick={() => toggleSupply(supply)}>{supply.active ? "Inactivar" : "Reactivar"}</button>
                  </div></td>
                </tr>
              ))}</tbody>
            </table>
            {!supplies.length && <p className="muted">Todavía no cargaste insumos.</p>}
          </div>
        </section>

        <section className="cost-panel">
          <h3>2. Compras</h3>
          <form className="cost-form" onSubmit={addPurchase}>
            <label>Insumo<select required value={purchaseSupplyId} onChange={(event) => setPurchaseSupplyId(event.target.value)}>
              <option value="">Seleccionar insumo</option>
              {supplies.filter((item) => item.active).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select></label>
            <label>Cantidad comprada ({chosenSupply?.unit === "unit" ? "unidades" : "kg"})<input type="number" inputMode="decimal" min="0.001" max="999999999" step="0.001" required value={purchaseQty} onChange={(event) => setPurchaseQty(event.target.value)} /></label>
            <label>Importe total pagado ($)<input type="number" inputMode="decimal" min="0" step="0.01" required value={purchaseTotal} onChange={(event) => setPurchaseTotal(event.target.value)} /></label>
            {unitPurchaseCost !== null && <p className="muted">Costo unitario estimado: {currency(unitPurchaseCost.toFixed(4))}</p>}
            <button className="primary" disabled={busy || !purchaseSupplyId}>Registrar compra</button>
          </form>
          <h3>Últimas compras</h3>
          <div className="cost-table-scroll">
            <table className="cost-table">
              <thead><tr><th>Fecha</th><th>Insumo</th><th>Cantidad</th><th>Total</th></tr></thead>
              <tbody>{purchases.slice(0, 30).map((purchase) => (
                <tr key={purchase.id}>
                  <td>{new Date(purchase.purchased_at).toLocaleDateString("es-AR")}</td>
                  <td>{purchase.supply_name}</td><td>{Number(purchase.quantity)} </td><td>{currency(purchase.total_cost)}</td>
                </tr>
              ))}</tbody>
            </table>
            {!purchases.length && <p className="muted">No hay compras registradas.</p>}
          </div>
        </section>
      </div>

      <section className="cost-panel recipe-panel">
        <h3>3. Receta por producto</h3>
        <p className="muted">Indicá los insumos utilizados en una unidad vendida o en un kilo vendido. En productos vendidos por peso, un insumo fijo se cobra una sola vez por detalle (por ejemplo, una caja de torta).</p>
        <label>Producto<select value={productId} onChange={(event) => setProductId(event.target.value)}>
          {products.map((product) => <option value={product.id} key={product.id}>{product.name} · {product.pricing_type === "weight" ? "por kg" : "unidad"}</option>)}
        </select></label>
        {productId && recipeLoaded && (
          <form onSubmit={saveRecipe} className="recipe-form">
            {recipeItems.map((item, index) => (
              <div className="recipe-row" key={item.supply_id}>
                <label>Insumo<select value={item.supply_id} onChange={(event) => setRecipeItems((items) => items.map((current, i) => i === index ? { ...current, supply_id: event.target.value } : current))}>
                  {supplies.filter((supply) => supply.active || supply.id === item.supply_id).map((supply) =>
                    <option key={supply.id} value={supply.id}>{supply.name} ({supply.unit === "kg" ? "kg" : "u."})</option>)}
                </select></label>
                <label>Cantidad<input type="number" min="0.001" max="999999999" step="0.001" required value={item.quantity} onChange={(event) => setRecipeItems((items) => items.map((current, i) => i === index ? { ...current, quantity: event.target.value } : current))} /></label>
                {chosenProduct?.pricing_type === "weight" && <label>Consumo<select value={item.mode} onChange={(event) => setRecipeItems((items) => items.map((current, i) => i === index ? { ...current, mode: event.target.value as "variable" | "fixed" } : current))}>
                  <option value="variable">Por kg vendido</option><option value="fixed">Fijo por detalle</option>
                </select></label>}
                <button className="ghost" type="button" disabled={busy} onClick={() => setRecipeItems((items) => items.filter((_, i) => i !== index))}>Quitar</button>
              </div>
            ))}
            <button className="ghost" type="button" disabled={busy || supplies.filter((supply) => supply.active && !recipeItems.some((item) => item.supply_id === supply.id)).length === 0} onClick={() => {
              const available = supplies.find((supply) => supply.active && !recipeItems.some((item) => item.supply_id === supply.id));
              if (available) setRecipeItems((items) => [...items, { supply_id: available.id, quantity: "1.000", mode: "variable" }]);
            }}>+ Agregar insumo a la receta</button>
            {chosenProduct && <div className="recipe-estimate">
              <span>Precio de venta por {chosenProduct.pricing_type === "weight" ? "kg" : "unidad"}: <strong>{currency(chosenProduct.price)}</strong></span>
              {validCost ?
                <><span>Costo estimado: <strong>{currency(estimatedCost.toFixed(2))}</strong></span>
                <span>Ganancia bruta estimada: <strong>{currency(estimatedProfit.toFixed(2))}</strong></span></> :
                <span className="muted">Costo incompleto: cargá una receta y registrá compras para todos sus insumos.</span>}
            </div>}
            <button className="primary" disabled={busy || recipeItems.some((item, i) => recipeItems.findIndex((other) => other.supply_id === item.supply_id) !== i)}>Guardar receta</button>
          </form>
        )}
        {productId && !recipeLoaded && <p className="muted">Cargando receta…</p>}
        {!products.length && <p className="muted">Cargá productos antes de definir recetas.</p>}
      </section>
    </section>
  );
}
