export type PaymentMethod = "cash" | "transfer" | "debit_card" | "credit_card" | "qr";

export interface ApiErrorBody {
  code: string;
  message: string;
  field_errors: Record<string, string>;
}

export class ApiError extends Error {
  constructor(public status: number, public body: ApiErrorBody) {
    super(body.message);
  }
}

export class SessionExpiredError extends ApiError {}

export interface Product {
  id: string;
  name: string;
  price: string;
  active: boolean;
  image_url: string | null;
}

export interface SaleDetail {
  id: string;
  product_id: string;
  product_name: string;
  unit_price: string;
  quantity: number;
  position: number;
}

export interface Sale {
  id: string;
  payment_method: PaymentMethod;
  total: string;
  sold_at: string;
  sale_day: string;
  observation: string | null;
  annulment: { reason: string; annulled_at: string } | null;
  details: SaleDetail[];
}

export interface SalesByDay {
  day: string;
  total_sold: string;
  sales: Sale[];
}

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
  login: (username: string, password: string) =>
    request<void>("/api/sesion/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: () => request<void>("/api/sesion/logout", { method: "POST" }),
  me: () => request<{ id: string; username: string }>("/api/sesion/actual"),
  products: (includeInactive = false) =>
    request<Product[]>(`/api/productos${includeInactive ? "?incluir_inactivos=true" : ""}`),
  createProduct: (name: string, price: string) =>
    request<Product>("/api/productos", {
      method: "POST",
      body: JSON.stringify({ name, price }),
    }),
  updateProduct: (id: string, name: string, price: string) =>
    request<Product>(`/api/productos/${id}`, {
      method: "PUT",
      body: JSON.stringify({ name, price }),
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
  confirmSale: (
    idempotencyKey: string,
    paymentMethod: PaymentMethod,
    details: Array<{ product_id: string; quantity: number }>,
  ) =>
    request<Sale>("/api/ventas", {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ payment_method: paymentMethod, details }),
    }),
  sales: (day: string) => request<SalesByDay>(`/api/ventas?dia=${encodeURIComponent(day)}`),
  annulSale: (id: string, reason: string) =>
    request<Sale>(`/api/ventas/${id}/anulacion`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  saveObservation: (id: string, observation: string) =>
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
