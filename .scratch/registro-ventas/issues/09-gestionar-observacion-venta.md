# 09 — Gestionar la Observación de una Venta

**What to build:** La persona que atiende la heladería puede agregar, reemplazar o quitar contexto no financiero de una Venta mediante una Observación, incluso después de una Anulación, sin modificar ningún dato económico o temporal.

**Blocked by:** 07 — Consultar las Ventas de un Día de venta.

**Status:** ready-for-agent

- [ ] Una Venta sin Observación puede recibir una después de haber sido confirmada.
- [ ] Agregar o reemplazar una Observación exige texto no vacío después de recortar espacios exteriores.
- [ ] Una Observación existente puede reemplazarse por otro texto válido o quitarse para dejarla ausente.
- [ ] Las mismas operaciones están disponibles cuando la Venta ya fue anulada.
- [ ] Modificar la Observación no cambia Detalles, Medio de pago, Precio de venta, Total de venta, Total vendido, Momento de venta, Día de venta ni datos de la Anulación.
- [ ] La interfaz HTTP trata la Observación como una operación explícita asociada a la Venta y no expone una actualización genérica de campos económicos.
- [ ] La interfaz conserva el texto editable ante errores recuperables, muestra progreso, evita envíos repetidos y comunica las validaciones en español.
- [ ] Los controles de Observación son etiquetados, presentan foco visible, funcionan con teclado y se adaptan a computadora, tableta y teléfono.
- [ ] Las pruebas HTTP con PostgreSQL real cubren agregar, reemplazar, quitar, rechazar texto vacío y modificar antes y después de una Anulación.
- [ ] Las pruebas de interacción comprueban que la Observación actualizada aparece en el detalle sin alterar el estado ni los totales de la Venta.
