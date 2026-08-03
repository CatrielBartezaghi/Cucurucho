"use client";

import { FormEvent, useState } from "react";
import { api, Category, pesos, Product } from "@/lib/api";

interface Props {
  products: Product[];
  categories: Category[];
  onRefresh: () => Promise<void>;
  onError: (reason: unknown) => void;
}

export function Catalog({ products, categories, onRefresh, onError }: Props) {
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [categoryName, setCategoryName] = useState("");
  const [busy, setBusy] = useState(false);

  async function create(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await api.createProduct(name, price, categoryId);
      setName("");
      setPrice("");
      await onRefresh();
    } catch (reason) {
      onError(reason);
    } finally {
      setBusy(false);
    }
  }

  async function edit(product: Product) {
    const nextName = window.prompt("Nombre del Producto", product.name);
    if (nextName === null) return;
    const nextPrice = window.prompt("Precio en pesos", product.price);
    if (nextPrice === null) return;
    setBusy(true);
    try {
      await api.updateProduct(product.id, nextName, nextPrice, product.category.id);
      await onRefresh();
    } catch (reason) {
      onError(reason);
    } finally {
      setBusy(false);
    }
  }

  async function createCategory(event: FormEvent) {
    event.preventDefault();
    await action(async () => {
      await api.createCategory(categoryName);
      setCategoryName("");
    });
  }

  async function renameCategory(category: Category) {
    const nextName = window.prompt("Nombre de la Categoría", category.name);
    if (nextName === null) return;
    await action(() => api.updateCategory(category.id, nextName));
  }

  async function assignCategory(product: Product, nextCategoryId: string) {
    await action(() =>
      api.updateProduct(product.id, product.name, product.price, nextCategoryId),
    );
  }

  async function changeImage(product: Product, file?: File) {
    if (!file) return;
    setBusy(true);
    try {
      await api.replaceProductImage(product.id, file);
      await onRefresh();
    } catch (reason) {
      onError(reason);
    } finally {
      setBusy(false);
    }
  }

  async function action(task: () => Promise<unknown>) {
    setBusy(true);
    try {
      await task();
      await onRefresh();
    } catch (reason) {
      onError(reason);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby="catalog-title">
      <div className="section-heading">
        <div><p className="eyebrow">Catálogo</p><h2 id="catalog-title">Productos</h2></div>
        <span className="pill">{products.filter((product) => product.active).length} activos</span>
      </div>
      <div className="category-management">
        <form onSubmit={createCategory}>
          <label>Nueva Categoría<input value={categoryName} onChange={(event) => setCategoryName(event.target.value)} required /></label>
          <button className="ghost" disabled={busy}>Agregar Categoría</button>
        </form>
        <div className="category-list" aria-label="Categorías">
          {categories.map((category) => (
            <button className="ghost" type="button" disabled={busy} key={category.id} onClick={() => renameCategory(category)}>
              {category.name} · Renombrar
            </button>
          ))}
        </div>
      </div>
      <form className="create-product" onSubmit={create}>
        <label>Nombre<input value={name} onChange={(event) => setName(event.target.value)} required /></label>
        <label>Precio<input value={price} onChange={(event) => setPrice(event.target.value)} inputMode="decimal" placeholder="0,00" required /></label>
        <label>Categoría<select value={categoryId} onChange={(event) => setCategoryId(event.target.value)} required><option value="">Elegí una</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
        <button className="primary" disabled={busy}>Agregar Producto</button>
      </form>
      <div className="product-grid">
        {products.map((product) => (
          <article className={`product-card ${product.active ? "" : "inactive"}`} key={product.id}>
            {/* Product image URLs come from the configured public blob store. */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={product.image_url ?? "/product-placeholder.svg"} alt={product.image_url ? `Imagen de ${product.name}` : `Imagen genérica de ${product.name}`} />
            <div className="product-body">
              <div className="product-title"><h3>{product.name}</h3><span>{product.active ? "Activo" : "Inactivo"}</span></div>
              <strong>{pesos(product.price)}</strong>
              <label>Categoría<select value={product.category.id} disabled={busy} onChange={(event) => assignCategory(product, event.target.value)}>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
              <div className="row-actions">
                <button className="ghost" disabled={busy} onClick={() => edit(product)}>Editar</button>
                <label className="file-action">{product.image_url ? "Reemplazar imagen" : "Agregar imagen"}<input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => changeImage(product, event.target.files?.[0])} disabled={busy} /></label>
                {product.image_url && <button className="ghost" disabled={busy} onClick={() => action(() => api.removeProductImage(product.id))}>Quitar imagen</button>}
                <button className="ghost" disabled={busy} onClick={() => action(() => api.setProductActive(product.id, !product.active))}>{product.active ? "Inactivar" : "Reactivar"}</button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
