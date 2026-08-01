# 05 — Armar y confirmar una Venta

**What to build:** La persona que atiende la heladería puede armar localmente una selección de Productos activos, ver el Total de venta, elegir un único Medio de pago y confirmar una Venta completa cuyo resultado económico y temporal definitivo es calculado y devuelto por el servidor.

**Blocked by:** 03 — Modificar y activar o inactivar Productos.

**Status:** ready-for-agent

- [ ] La selección en curso vive solamente en el navegador, no tiene identidad de Venta y nunca se persiste antes de confirmar.
- [ ] La interfaz permite agregar Productos activos, aumentar o disminuir Cantidades enteras positivas, quitar detalles y ver el Total de venta provisional con exactitud decimal.
- [ ] La selección conserva apariciones repetidas de un mismo Producto como detalles independientes y permite elegir exactamente un Medio de pago entre efectivo, transferencia, tarjeta de débito, tarjeta de crédito y QR.
- [ ] No puede confirmarse una selección vacía ni una selección con Cantidades inválidas o sin un único Medio de pago.
- [ ] La solicitud incluye una clave de idempotencia generada por el cliente junto con cada identificador de Producto, Cantidad y el Medio de pago elegido.
- [ ] Dentro de una única transacción, el servidor valida Cantidades, resuelve los Productos, exige que estén activos y toma de una versión coherente su nombre y precio vigentes aunque exista una modificación concurrente.
- [ ] Cada Detalle de venta conserva la referencia del Producto, nombre, Precio de venta, Cantidad y orden confirmados; Productos repetidos permanecen como Detalles independientes.
- [ ] El Total de venta es la suma decimal exacta de Precio de venta por Cantidad, se persiste de manera inmutable y se intercambia como cadena con dos posiciones.
- [ ] El servidor asigna un Momento de venta con zona horaria y un Día de venta en `America/Argentina/Buenos_Aires`; ninguno puede elegirse ni modificarse después.
- [ ] Cualquier Producto inexistente o inactivo, validación fallida o error de escritura revierte la transacción completa y no deja una Venta parcial.
- [ ] La respuesta exitosa contiene la representación autoritativa completa de la Venta, incluidos Momento, Día, Detalles, Medio de pago y Total de venta.
- [ ] Una respuesta exitosa limpia la selección; un error recuperable conserva toda la selección y una pérdida de red no presenta la Venta como confirmada sin respuesta autoritativa.
- [ ] Cambiar posteriormente nombre, precio, actividad o imagen de un Producto no modifica ningún Detalle de venta ya confirmado.
- [ ] Las pruebas HTTP con PostgreSQL real cubren confirmación, rollback, Productos inactivos, Cantidades inválidas, Productos repetidos, snapshots históricos, cálculo decimal y concurrencia relevante.
- [ ] Las pruebas de interacción cubren armado, cálculo provisional, estados de carga, error recuperable y limpieza exitosa; una prueba de navegador confirma una Venta de punta a punta.
