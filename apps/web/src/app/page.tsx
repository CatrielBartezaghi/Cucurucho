"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, SessionExpiredError, api, buenosAiresToday, Product, Sale, SalesByDay } from "@/lib/api";
import { Catalog } from "@/components/catalog";
import { RegisterSale } from "@/components/register-sale";
import { SalesHistory } from "@/components/sales-history";

type Section = "sale" | "catalog" | "history";

export default function HomePage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [section, setSection] = useState<Section>("sale");
  const [products, setProducts] = useState<Product[]>([]);
  const [history, setHistory] = useState<SalesByDay | null>(null);
  const [day, setDay] = useState(buenosAiresToday());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  function handleError(reason: unknown) {
    if (reason instanceof SessionExpiredError) {
      router.replace("/login");
      return;
    }
    setError(reason instanceof ApiError ? reason.message : "Ocurrió un error inesperado.");
  }

  async function loadProducts(includeInactive = false) {
    try {
      setProducts(await api.products(includeInactive));
    } catch (reason) {
      handleError(reason);
    }
  }

  async function loadHistory(selectedDay = day) {
    try {
      setHistory(await api.sales(selectedDay));
    } catch (reason) {
      handleError(reason);
    }
  }

  useEffect(() => {
    Promise.all([api.me(), api.products(), api.sales(day)])
      .then(([user, catalog, sales]) => {
        setUsername(user.username);
        setProducts(catalog);
        setHistory(sales);
      })
      .catch(handleError)
      .finally(() => setLoading(false));
    // The initial day is intentionally captured once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function logout() {
    try {
      await api.logout();
    } finally {
      router.replace("/login");
    }
  }

  if (loading) return <main className="center" aria-live="polite">Preparando el mostrador…</main>;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Heladería</p>
          <h1>Registro diario</h1>
        </div>
        <div className="user-actions">
          <span>{username}</span>
          <button className="ghost" onClick={logout}>Cerrar sesión</button>
        </div>
      </header>

      <nav className="tabs" aria-label="Secciones principales">
        <button aria-current={section === "sale" ? "page" : undefined} onClick={() => { setSection("sale"); loadProducts(false); }}>Nueva venta</button>
        <button aria-current={section === "catalog" ? "page" : undefined} onClick={() => { setSection("catalog"); loadProducts(true); }}>Productos</button>
        <button aria-current={section === "history" ? "page" : undefined} onClick={() => { setSection("history"); loadHistory(); }}>Ventas del día</button>
      </nav>

      {error && <p className="banner error" role="alert">{error}<button onClick={() => setError("")} aria-label="Cerrar error">×</button></p>}

      <main className="content">
        {section === "sale" && <RegisterSale products={products.filter((product) => product.active)} onConfirmed={(sale) => { setDay(sale.sale_day); loadHistory(sale.sale_day); }} onError={handleError} />}
        {section === "catalog" && <Catalog products={products} onRefresh={() => loadProducts(true)} onError={handleError} />}
        {section === "history" && history && <SalesHistory day={day} history={history} onDayChange={(value) => { setDay(value); loadHistory(value); }} onRefresh={() => loadHistory()} onError={handleError} />}
      </main>
    </div>
  );
}

