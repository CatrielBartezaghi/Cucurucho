import type { components } from "./openapi.generated";

type Schemas = components["schemas"];
type LoginInput = Schemas["LoginInput"];
type ProductInput = Schemas["ProductInput"];
type CategoryInput = Schemas["CategoryInput"];
type SaleInput = Schemas["SaleInput"];
type ObservationInput = Schemas["ObservationInput"];
type AnnulmentInput = Schemas["AnnulmentInput"];

export type PaymentMethod = SaleInput["payment_method"];
export type ApiErrorBody = Schemas["ErrorOutput"];

export class ApiError extends Error {
  constructor(public status: number, public body: ApiErrorBody) {
    super(body.message);
  }
}

export class SessionExpiredError extends ApiError {}

export type Category = Schemas["CategoryOutput"];
export type Product = Schemas["ProductOutput"];
export type SaleDetail = Schemas["SaleDetailOutput"];
export type Sale = Schemas["SaleOutput"];
export type SalesByDay = Schemas["SalesByDayOutput"];

export type Supply = {
  id: string; name: string; unit: "kg" | "unit";
  current_unit_cost: string | null; active: boolean;
};
export type SupplyPurchase = {
  id: string; supply_id: string; supply_name: string;
  quantity: string; total_cost: string; unit_cost: string; purchased_at: string;
};
export type RecipeItem = {
  supply_id: string; supply_name: string; unit: "kg" | "unit";
  quantity: string; mode: "variable" | "fixed"; unit_cost: string | null;
};
export type Recipe = { product_id: string; items: RecipeItem[] };
export type RecipeChange = { supply_id: string; quantity: string; mode: "variable" | "fixed" };
export type ProfitItem = {
  product_id: string; name: string; revenue: string; known_revenue: string;
  known_cost: string; gross_profit: string; gross_margin_pct: string | null;
  missing_lines: number; lines: number;
};
export type ProfitReport = {
  from: string; to: string; total_revenue: string; known_revenue: string;
  unknown_revenue: string; known_cost: string; gross_profit: string;
  gross_margin_pct: string | null; missing_lines: number; products: ProfitItem[];
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(path, { ...init, headers, credentials: "same-origin" });
  if (!response.ok) {
    const fallback: ApiErrorBody = {
      code: "unexpected_error",
      message: "Ocurrió un error inesperado. Reintentá.",
      field_errors: {},
    };
    const body = (await response.json().catch(() => fallback)) as ApiErrorBody;
    if (response.status === 401) throw new SessionExpiredError(response.status, body);
    throw new ApiError(response.status, body);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  login: (username: LoginInput["username"], password: LoginInput["password"]) =>
    request<void>("/api/sesion/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: () => request<void>("/api/sesion/logout", { method: "POST" }),
  me: () => request<Schemas["CurrentSessionOutput"]>("/api/sesion/actual"),
  products: (includeInactive = false) =>
    request<Product[]>(`/api/productos${includeInactive ? "?incluir_inactivos=true" : ""}`),
  categories: () => request<Category[]>("/api/categorias"),
  createCategory: (name: CategoryInput["name"]) =>
    request<Category>("/api/categorias", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),
  updateCategory: (id: string, name: CategoryInput["name"]) =>
    request<Category>(`/api/categorias/${id}`, {
      method: "PUT",
      body: JSON.stringify({ name }),
    }),
  createProduct: (
    name: ProductInput["name"],
    price: ProductInput["price"],
    categoryId: string,
    pricingType: ProductInput["pricing_type"] = "unit",
  ) =>
    request<Product>("/api/productos", {
      method: "POST",
      body: JSON.stringify({ name, price, category_id: categoryId, pricing_type: pricingType }),
    }),
  updateProduct: (
    id: string,
    name: ProductInput["name"],
    price: ProductInput["price"],
    categoryId: string,
    pricingType: ProductInput["pricing_type"] = "unit",
  ) =>
    request<Product>(`/api/productos/${id}`, {
      method: "PUT",
      body: JSON.stringify({ name, price, category_id: categoryId, pricing_type: pricingType }),
    }),
  setProductActive: (id: string, active: boolean) =>
    request<Product>(`/api/productos/${id}/${active ? "activar" : "inactivar"}`, {
      method: "POST",
    }),
  replaceProductImage: (id: string, image: File) => {
    const body = new FormData();
    body.append("image", image);
    return request<Product>(`/api/productos/${id}/imagen`, { method: "PUT", body });
  },
  removeProductImage: (id: string) =>
    request<Product>(`/api/productos/${id}/imagen`, { method: "DELETE" }),

  supplies: () => request<Supply[]>("/api/insumos"),
  createSupply: (name: string, unit: "kg" | "unit") =>
    request<Supply>("/api/insumos", { method: "POST", body: JSON.stringify({ name, unit }) }),
  updateSupply: (id: string, name: string, active: boolean) =>
    request<Supply>(`/api/insumos/${id}`, { method: "PUT", body: JSON.stringify({ name, active }) }),
  purchases: () => request<SupplyPurchase[]>("/api/compras-insumos"),
  createPurchase: (supply_id: string, quantity: string, total_cost: string) =>
    request<SupplyPurchase>("/api/compras-insumos", {
      method: "POST", body: JSON.stringify({ supply_id, quantity, total_cost }),
    }),
  recipe: (productId: string) =>
    request<Recipe>(`/api/productos/${productId}/receta`),
  saveRecipe: (productId: string, items: RecipeChange[]) =>
    request<Recipe>(`/api/productos/${productId}/receta`, {
      method: "PUT", body: JSON.stringify({ items }),
    }),
  profitability: (from: string, to: string) =>
    request<ProfitReport>(`/api/rentabilidad?desde=${encodeURIComponent(from)}&hasta=${encodeURIComponent(to)}`),
  confirmSale: (
    idempotencyKey: string,
    paymentMethod: PaymentMethod,
    details: SaleInput["details"],
  ) =>
    request<Sale>("/api/ventas", {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ payment_method: paymentMethod, details }),
    }),
  sales: (day: string) => request<SalesByDay>(`/api/ventas?dia=${encodeURIComponent(day)}`),
  annulSale: (id: string, reason: AnnulmentInput["reason"]) =>
    request<Sale>(`/api/ventas/${id}/anulacion`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  saveObservation: (id: string, observation: ObservationInput["observation"]) =>
    request<Sale>(`/api/ventas/${id}/observacion`, {
      method: "PUT",
      body: JSON.stringify({ observation }),
    }),
  removeObservation: (id: string) =>
    request<Sale>(`/api/ventas/${id}/observacion`, { method: "DELETE" }),
};

export function pesos(value: string): string {
  return new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS" }).format(Number(value));
}

export function buenosAiresToday(now = new Date()): string {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Argentina/Buenos_Aires",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const get = (type: Intl.DateTimeFormatPartTypes) => parts.find((part) => part.type === type)?.value;
  return `${get("year")}-${get("month")}-${get("day")}`;
}

export function addMoney(values: Array<{ price: string; quantity: number }>): string {
  const cents = values.reduce((sum, item) => {
    const [whole, decimal = ""] = item.price.split(".");
    return sum + (Number(whole) * 100 + Number(decimal.padEnd(2, "0"))) * item.quantity;
  }, 0);
  return `${Math.trunc(cents / 100)}.${String(cents % 100).padStart(2, "0")}`;
}

export function multiplyMoney(price: string, quantity: number): string {
  return addMoney([{ price, quantity }]);
}
