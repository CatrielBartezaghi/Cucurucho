import { PaymentMethod } from "./api";

export const paymentMethodLabels: Record<PaymentMethod, string> = {
  cash: "Efectivo",
  transfer: "Transferencia",
  debit_card: "Tarjeta de débito",
  credit_card: "Tarjeta de crédito",
  qr: "QR",
};

export const paymentMethods = Object.entries(paymentMethodLabels) as Array<[PaymentMethod, string]>;
