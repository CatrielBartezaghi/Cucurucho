# 08 — Anular una Venta

**What to build:** La persona que atiende la heladería puede invalidar una Venta completa una única vez mediante una confirmación explícita y un Motivo de anulación obligatorio, conservando intacto el registro original y actualizando el Total vendido.

**Blocked by:** 07 — Consultar las Ventas de un Día de venta.

**Status:** ready-for-agent

- [ ] La Anulación exige un Motivo de anulación recortado y no vacío y solicita confirmación explícita antes de ejecutar la acción irreversible.
- [ ] Una Anulación exitosa conserva el motivo y su momento junto con todos los datos económicos y temporales originales de la Venta.
- [ ] Una Venta anulada permanece visible, se distingue claramente y muestra su Motivo de anulación.
- [ ] El Total vendido del Día de venta se actualiza para excluir la Venta anulada.
- [ ] Un segundo intento de anular la misma Venta se rechaza como conflicto con un mensaje claro en español.
- [ ] No existe una operación para revertir la Anulación, eliminar la Venta ni modificar sus Detalles, Medio de pago, Precio de venta, Total de venta, Momento o Día de venta.
- [ ] La acción muestra progreso, impide envíos repetidos, conserva el motivo ante errores recuperables y ofrece foco visible, controles etiquetados y operación completa mediante teclado.
- [ ] Las pruebas HTTP con PostgreSQL real demuestran que la Anulación es atómica, irreversible, de una sola vez y exige un motivo válido.
- [ ] Las pruebas HTTP comprueban el Total vendido antes y después de anular sin alterar los datos originales de la Venta.
- [ ] Las pruebas de interacción cubren confirmación, cancelación del diálogo, error recuperable y presentación de la Venta anulada; una prueba de navegador recorre Anulación y actualización del Total vendido.
