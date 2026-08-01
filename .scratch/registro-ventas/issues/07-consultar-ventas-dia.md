# 07 — Consultar las Ventas de un Día de venta

**What to build:** La persona que atiende la heladería puede revisar cualquier Día de venta, comenzando por el día actual de Buenos Aires, ver sus Ventas desde la más reciente, abrir cada detalle y conocer el Total vendido del día.

**Blocked by:** 05 — Armar y confirmar una Venta.

**Status:** ready-for-agent

- [ ] La vista inicial calcula el Día de venta actual en `America/Argentina/Buenos_Aires`, sin depender del día UTC ni de la zona horaria del servidor o dispositivo.
- [ ] La persona puede elegir otro Día de venta y consultar también días sin actividad.
- [ ] La respuesta devuelve las Ventas del día ordenadas por Momento de venta descendente junto con el Total vendido.
- [ ] Cada Venta puede abrirse para ver sus Detalles en orden, Cantidades, Precios de venta, Medio de pago, Momento de venta y Total de venta conservados.
- [ ] El Total vendido se calcula exclusivamente con Ventas no anuladas y se intercambia como cadena decimal con dos posiciones.
- [ ] La consulta no ofrece edición de Detalles, Medio de pago, Precio de venta, Total de venta, Momento de venta ni Día de venta.
- [ ] La interfaz presenta fechas, horas e importes de forma comprensible en español, funciona con teclado y tecnologías de asistencia y se adapta a computadora, tableta y teléfono.
- [ ] Las acciones de consulta muestran progreso y errores recuperables sin ocultar innecesariamente la fecha elegida.
- [ ] Las pruebas HTTP con PostgreSQL real cubren días vacíos, orden descendente, Ventas a ambos lados de medianoche UTC y de Buenos Aires, detalle histórico y cálculo del Total vendido.
- [ ] Las pruebas de interacción cubren la fecha inicial, el cambio de Día de venta y la apertura de un detalle; una prueba de navegador consulta la Venta previamente confirmada.
