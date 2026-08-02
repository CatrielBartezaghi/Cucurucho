import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Heladería — Registro de ventas",
  description: "Catálogo y registro diario de ventas",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}

