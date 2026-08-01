# Registro de ventas de la heladería

Status: ready-for-agent

## Problem Statement

La persona que atiende la heladería necesita registrar Ventas con rapidez y conservar información económica confiable sin depender de datos que puedan cambiar después. También necesita administrar el catálogo de Productos, consultar lo vendido en un Día de venta, corregir una Observación y dejar constancia de una Anulación sin editar ni eliminar la Venta original.

El sistema debe proteger estas operaciones detrás de una sesión persistente, funcionar correctamente en la infraestructura web ya elegida y mantener una única interpretación de importes, horarios, Productos inactivos e imágenes. El repositorio todavía no contiene una implementación, por lo que esta primera entrega debe establecer una base completa pero deliberadamente acotada.

## Solution

Construir una aplicación web autenticada para una sola persona, con tres flujos principales:

- Administrar un catálogo de Productos activos e inactivos, cada uno con nombre, precio e Imagen de producto opcional.
- Armar localmente una selección de Productos, confirmar una Venta con un único Medio de pago y recibir el resultado definitivo calculado por el servidor.
- Consultar las Ventas de cualquier Día de venta, ver el Total vendido y gestionar la Observación o una única Anulación de cada Venta.

La aplicación conservará en cada Detalle de venta el nombre, Precio de venta y Cantidad confirmados. Las reglas económicas y temporales se resolverán en el backend dentro de transacciones de PostgreSQL. El navegador accederá al backend mediante rutas same-origin `/api/*`; el proxy de Next.js no contendrá lógica de negocio.

## User Stories

1. Como persona que atiende la heladería, quiero iniciar sesión, para que únicamente yo pueda acceder al registro de Ventas.
2. Como persona que atiende la heladería, quiero conservar mi sesión entre visitas, para no autenticarme repetidamente durante el trabajo diario.
3. Como persona que atiende la heladería, quiero cerrar sesión, para revocar el acceso desde el navegador actual.
4. Como persona que atiende la heladería, quiero recibir un mensaje genérico cuando las credenciales sean incorrectas, para poder reintentar sin que el sistema revele información de la cuenta.
5. Como persona que atiende la heladería, quiero volver al inicio de sesión cuando mi sesión expire o sea revocada, para entender por qué ya no puedo continuar.
6. Como persona que atiende la heladería, quiero ver los Productos activos, para seleccionar rápidamente lo que se vende.
7. Como persona que administra el catálogo, quiero ver también los Productos inactivos, para poder revisar y reactivar presentaciones anteriores.
8. Como persona que administra el catálogo, quiero crear un Producto con nombre y precio, para incorporarlo a Ventas nuevas.
9. Como persona que administra el catálogo, quiero que un Producto nuevo quede activo, para poder utilizarlo inmediatamente.
10. Como persona que administra el catálogo, quiero saber si el nombre ya existe aunque cambien mayúsculas, acentos o espacios exteriores, para evitar Productos indistinguibles.
11. Como persona que administra el catálogo, quiero corregir el nombre de un Producto, para mantener el catálogo comprensible.
12. Como persona que administra el catálogo, quiero cambiar el precio de un Producto, para cobrar el valor vigente en Ventas futuras.
13. Como persona que administra el catálogo, quiero que un cambio de nombre o precio no altere Detalles de venta anteriores, para preservar el registro histórico.
14. Como persona que administra el catálogo, quiero inactivar un Producto en vez de eliminarlo, para impedir nuevas selecciones sin perder su historia.
15. Como persona que administra el catálogo, quiero reactivar un Producto inactivo, para volver a ofrecerlo sin crear un duplicado.
16. Como persona que administra el catálogo, quiero agregar o reemplazar la Imagen de producto, para reconocerlo visualmente.
17. Como persona que administra el catálogo, quiero quitar una Imagen de producto, para volver a utilizar la imagen genérica.
18. Como persona que administra el catálogo, quiero ver una validación clara si una imagen tiene un formato no admitido o supera 5 MB, para poder elegir otro archivo.
19. Como persona que atiende la heladería, quiero ver una imagen genérica cuando el Producto no tenga imagen propia, para que el diseño siga siendo consistente.
20. Como persona que atiende la heladería, quiero agregar Productos activos a una selección en curso, para preparar una Venta antes de confirmarla.
21. Como persona que atiende la heladería, quiero aumentar o disminuir la Cantidad de cada selección, para reflejar las unidades vendidas.
22. Como persona que atiende la heladería, quiero que las cantidades sean siempre enteras y positivas, para evitar Ventas inválidas.
23. Como persona que atiende la heladería, quiero quitar un detalle de la selección en curso, para corregirla antes de confirmar.
24. Como persona que atiende la heladería, quiero ver el Total de venta mientras preparo la selección, para comunicar el importe a cobrar.
25. Como persona que atiende la heladería, quiero elegir exactamente un Medio de pago, para registrar cómo se abonó la Venta.
26. Como persona que atiende la heladería, quiero que la selección en curso permanezca solamente en el navegador, para no guardar Ventas incompletas.
27. Como persona que atiende la heladería, quiero confirmar una selección no vacía, para crear una Venta completa.
28. Como persona que atiende la heladería, quiero que el servidor use los Productos activos y precios vigentes al confirmar, para que el registro definitivo sea autoritativo.
29. Como persona que atiende la heladería, quiero que una confirmación falle completa si algún Producto ya no existe o está inactivo, para no guardar una Venta parcialmente válida.
30. Como persona que atiende la heladería, quiero conservar mi selección cuando la confirmación falla, para corregir el problema sin empezar de nuevo.
31. Como persona que atiende la heladería, quiero que una doble pulsación o un reintento de red no cree dos Ventas, para evitar duplicados accidentales.
32. Como persona que atiende la heladería, quiero recibir el Momento de venta, los Detalles de venta y el Total de venta definitivos después de confirmar, para comprobar lo registrado.
33. Como persona que atiende la heladería, quiero que una confirmación exitosa limpie la selección en curso, para comenzar la siguiente Venta.
34. Como persona que atiende la heladería, quiero que Productos repetidos enviados al confirmar se conserven como Detalles de venta independientes, para que el backend no imponga una regla de agregación inexistente.
35. Como persona que atiende la heladería, quiero consultar las Ventas de un Día de venta, para revisar la actividad de esa fecha.
36. Como persona que atiende la heladería, quiero que inicialmente se muestre el Día de venta actual de Buenos Aires, para acceder al trabajo de hoy sin configurar la fecha.
37. Como persona que atiende la heladería, quiero cambiar el Día de venta consultado, para revisar fechas anteriores.
38. Como persona que atiende la heladería, quiero ver las Ventas ordenadas desde la más reciente, para encontrar primero las operaciones actuales.
39. Como persona que atiende la heladería, quiero abrir el detalle de una Venta, para ver sus Productos, cantidades, precios, Medio de pago y Momento de venta.
40. Como persona que atiende la heladería, quiero distinguir claramente una Venta anulada, para no confundirla con una Venta que contribuye al Total vendido.
41. Como persona que atiende la heladería, quiero ver el Motivo de anulación conservado en una Venta anulada, para entender por qué fue invalidada.
42. Como persona que atiende la heladería, quiero ver el Total vendido del Día de venta consultado, para conocer la suma de las Ventas no anuladas.
43. Como persona que atiende la heladería, quiero que el Total vendido se actualice después de una Anulación, para mantener correcto el resultado del día.
44. Como persona que atiende la heladería, quiero anular una Venta completa con un Motivo de anulación obligatorio, para invalidarla sin editarla ni eliminarla.
45. Como persona que atiende la heladería, quiero confirmar explícitamente una Anulación, para reducir errores irreversibles.
46. Como persona que atiende la heladería, quiero que un segundo intento de anular la misma Venta sea rechazado, para preservar la regla de una única Anulación.
47. Como persona que atiende la heladería, quiero agregar una Observación después de confirmar una Venta, para conservar contexto no financiero.
48. Como persona que atiende la heladería, quiero reemplazar o quitar una Observación, para mantener actualizado ese contexto.
49. Como persona que atiende la heladería, quiero modificar la Observación incluso después de una Anulación, para que la invalidación no bloquee información contextual.
50. Como persona que atiende la heladería, quiero que la aplicación explique los errores con mensajes claros en español, para poder recuperarme sin conocimientos técnicos.
51. Como persona que atiende la heladería, quiero que las acciones en curso deshabiliten envíos repetidos y muestren progreso, para saber que el sistema está trabajando.
52. Como persona que atiende la heladería, quiero usar los flujos principales con teclado y tecnologías de asistencia, para que la interfaz no dependa exclusivamente del puntero.
53. Como persona que atiende la heladería, quiero utilizar la aplicación desde una computadora, tableta o teléfono moderno, para adaptarla al dispositivo disponible en el local.
54. Como persona que atiende la heladería, quiero que un error al reemplazar una imagen conserve la imagen anterior, para no dejar el Producto en un estado incompleto.
55. Como persona que atiende la heladería, quiero que una pérdida de red no muestre una Venta como confirmada sin respuesta del servidor, para evitar asumir que se registró algo que todavía no puede comprobarse.

## Implementation Decisions

### Alcance y módulos

- La primera entrega es un registro de Ventas online para una sola persona. No intenta cubrir todo un ERP.
- El backend tendrá tres módulos profundos: `Sesiones`, `CatalogoDeProductos` y `Ventas`. FastAPI será un adaptador HTTP; no contendrá reglas de negocio en los controladores.
- `Sesiones` presentará una interfaz para autenticar, resolver la sesión actual y cerrarla.
- `CatalogoDeProductos` presentará una interfaz para listar, crear y modificar Productos; activar o inactivar; y agregar, reemplazar o quitar la Imagen de producto.
- `Ventas` presentará una interfaz para confirmar una Venta, consultar las Ventas de un Día de venta, obtener un detalle, anular una vez y agregar, reemplazar o quitar la Observación.
- El seam externo principal será la interfaz HTTP same-origin. Las reglas de negocio, el acceso a PostgreSQL y la asignación del tiempo quedarán detrás de esa interfaz.
- Vercel Blob tendrá un port interno de almacenamiento de imágenes con un adaptador de producción y otro de prueba. No se expondrán interfaces de repositorio o reloj a los consumidores de los módulos.

### Arquitectura y despliegue

- Se respetará el monorepo con frontend Next.js y backend FastAPI desplegados como proyectos Vercel separados.
- El navegador utilizará `/api/*` en el origen del frontend. El proxy reenviará las solicitudes al backend sin ejecutar lógica de negocio.
- Neon PostgreSQL 17 será el almacén persistente. La aplicación utilizará la conexión agrupada y Alembic utilizará una conexión directa para migraciones.
- Las imágenes públicas se almacenarán en Vercel Blob; PostgreSQL conservará su referencia. Se aceptarán JPEG, PNG y WebP de hasta 5 MB.
- La aplicación será responsive, con prioridad en la velocidad de uso desde computadora o tableta y soporte funcional para teléfono.

### Autenticación y sesiones

- Existirá una sola cuenta provisionada de forma operativa. No habrá registro público, roles, invitaciones ni administración de múltiples cuentas.
- Las contraseñas se almacenarán con Argon2id y parámetros configurables; nunca se persistirá ni registrará la contraseña original.
- El inicio de sesión emitirá un identificador de sesión opaco y aleatorio. El navegador lo conservará en una cookie `Secure`, `HttpOnly` y `SameSite`, mientras PostgreSQL conservará únicamente una representación no reutilizable del token y su estado de expiración o revocación.
- La cookie usará `SameSite=Lax`. La sesión durará 30 días desde la autenticación y se rotará al iniciar sesión nuevamente; cerrar sesión la revocará inmediatamente.
- Todas las rutas funcionales exigirán una sesión válida. Las mutaciones también validarán el origen same-origin para reducir solicitudes cruzadas no deseadas.
- Los errores de autenticación no revelarán si el nombre de cuenta o la contraseña fue el dato incorrecto.

### Catálogo de Productos

- Un Producto se creará activo por defecto y nunca se eliminará físicamente mediante la aplicación; se inactivará o reactivará.
- El nombre visible se recortará en sus extremos. Para imponer unicidad se conservará además una forma normalizada que aplique comparación Unicode sin acentos y sin distinción entre mayúsculas y minúsculas.
- La unicidad se aplicará sobre Productos activos e inactivos, porque un Producto inactivo puede reactivarse.
- El precio será un Importe positivo con un máximo de dos decimales. Los valores monetarios no usarán punto flotante binario.
- Los cambios posteriores de nombre, precio, actividad o imagen no modificarán ningún Detalle de venta existente.
- Las operaciones de imagen coordinarán Blob y PostgreSQL de forma que un fallo de carga o persistencia deje vigente la imagen anterior. La eliminación de objetos reemplazados será segura y observable; una falla de limpieza no deberá hacer que PostgreSQL apunte a una imagen inexistente.
- Los Productos sin referencia de Blob utilizarán una imagen genérica incluida en el frontend.

### Confirmación de Ventas

- La selección previa a la confirmación será estado local del navegador y no se persistirá ni recibirá identidad de Venta.
- La solicitud de confirmación incluirá uno o más detalles con identificador de Producto y Cantidad, un único Medio de pago y una clave de idempotencia generada por el cliente.
- Los valores admitidos para el Medio de pago serán efectivo, transferencia, tarjeta de débito, tarjeta de crédito y QR; no se aceptarán combinaciones.
- El backend permitirá que el mismo identificador de Producto aparezca más de una vez y conservará cada aparición como un Detalle de venta independiente.
- Dentro de una única transacción, `Ventas` verificará que cada Cantidad sea entera y positiva, resolverá los Productos, exigirá que estén activos, tomará el nombre y precio vigentes, calculará cada importe y el Total de venta, asignará el Momento de venta y persistirá todos los datos.
- La transacción garantizará que cada snapshot corresponda a una versión confirmada y coherente del Producto, incluso si existe una modificación concurrente.
- Si falla cualquier validación o escritura, no se persistirá ninguna parte de la Venta.
- El Momento de venta se guardará como instante con zona horaria y el Día de venta se asignará utilizando `America/Argentina/Buenos_Aires`. Ambos serán inmutables.
- Los Detalles de venta conservarán como mínimo la referencia del Producto, su nombre, Precio de venta, Cantidad y orden dentro de la Venta. No existirá una restricción de unicidad por Producto dentro de una Venta.
- El Total de venta se calculará exactamente como la suma de Precio de venta por Cantidad. Se persistirá como dato inmutable y deberá coincidir con los detalles.
- Los importes se intercambiarán por JSON como cadenas decimales con dos posiciones, nunca como números de punto flotante.
- Repetir una confirmación con la misma clave de idempotencia y el mismo contenido devolverá la Venta ya creada. Reutilizarla con contenido diferente se rechazará como conflicto.
- La respuesta exitosa será la representación autoritativa completa de la Venta. El frontend solamente limpiará su selección después de recibirla.

### Historial, Anulación y Observación

- La consulta principal recibirá un Día de venta y devolverá sus Ventas ordenadas por Momento de venta descendente junto con el Total vendido.
- El Día de venta inicial del frontend será el día actual calculado en `America/Argentina/Buenos_Aires`, no el día UTC ni el del servidor.
- Las Ventas anuladas permanecerán visibles y conservarán todos sus datos originales, pero no contribuirán al Total vendido.
- La Anulación será una mutación de una sola vez sobre la Venta completa. Exigirá un Motivo de anulación recortado y no vacío, conservará su momento y rechazará intentos posteriores con un conflicto.
- No existirán edición de Detalles de venta, Medio de pago, Precio de venta, Total de venta, Momento de venta ni Día de venta; una equivocación económica se resolverá mediante Anulación y una Venta nueva.
- La Observación será texto opcional. Agregar o reemplazar exigirá texto no vacío después de recortar espacios; quitarla la dejará ausente.
- La Observación podrá cambiar tanto en Ventas no anuladas como anuladas y no afectará el Total vendido.

### Persistencia

- PostgreSQL tendrá entidades persistentes para la cuenta única, sesiones, Productos, Ventas y Detalles de venta.
- Productos tendrá restricciones de unicidad para el nombre normalizado y restricciones positivas para el precio.
- Ventas tendrá unicidad para la clave de idempotencia, campos inmutables para Medio de pago, Momento de venta, Día de venta y Total de venta, y campos opcionales para Observación y Anulación.
- Detalles de venta tendrá restricciones positivas para Cantidad y Precio de venta, preservará su orden y permitirá Productos repetidos.
- Las restricciones importantes se expresarán también en PostgreSQL para proteger los invariantes frente a errores de aplicación.
- Todas las modificaciones de esquema se realizarán mediante migraciones Alembic reproducibles.

### Interfaz HTTP y frontend

- La interfaz HTTP será REST y JSON, salvo la carga de imágenes mediante `multipart/form-data`.
- Habrá operaciones de sesión bajo `/api/sesion`, operaciones del catálogo bajo `/api/productos` y operaciones de registro e historial bajo `/api/ventas`.
- La Anulación y la Observación serán recursos o acciones explícitas asociadas a una Venta; no se ofrecerá una actualización genérica capaz de modificar campos económicos.
- Las respuestas de error tendrán una forma estable con código legible por máquina, mensaje en español y errores por campo cuando corresponda.
- Se distinguirán autenticación inválida, recurso inexistente, datos inválidos y conflictos de estado mediante estados HTTP apropiados.
- El contrato OpenAPI de FastAPI será la fuente del contrato HTTP. El adaptador HTTP del frontend conservará los tipos y transformaciones de red en un solo lugar.
- El frontend deshabilitará acciones mientras estén en curso, mostrará progreso y conservará el estado editable ante fallos recuperables.
- Una confirmación cuya respuesta se pierda se reconciliará reutilizando la misma clave de idempotencia antes de permitir otra Venta equivalente.
- La interfaz mostrará imágenes con texto alternativo útil, controles etiquetados, foco visible, navegación por teclado y confirmación explícita para la Anulación irreversible.

## Testing Decisions

- Las pruebas verificarán comportamiento observable a través de interfaces estables; no afirmarán llamadas internas, estructura privada de clases ni detalles del ORM.
- El seam principal de pruebas del backend será la interfaz HTTP de FastAPI ejecutada en proceso mediante su adaptador ASGI. Esto ejercitará juntos los módulos, validación, autenticación, transacciones y serialización.
- Las pruebas HTTP utilizarán PostgreSQL 17 efímero con las migraciones reales aplicadas. No se sustituirá PostgreSQL por SQLite porque sus restricciones, transacciones, Unicode y tipos monetarios no son equivalentes.
- Vercel Blob, al ser una dependencia externa real, se reemplazará por un adaptador de prueba controlable. Se comprobarán carga, reemplazo, eliminación, validación y fallos parciales sin hacer solicitudes reales a Vercel.
- El reloj y la zona horaria serán dependencias internas controlables para probar cambios de Día de venta alrededor de medianoche de Buenos Aires; no formarán parte de la interfaz pública.
- `Sesiones` se probará mediante login, cookie, acceso autenticado, expiración, revocación, rotación y mensajes de error observables.
- `CatalogoDeProductos` se probará mediante creación, modificación, unicidad Unicode, precios inválidos, activación, inactivación y ciclo de vida de Imagen de producto.
- `Ventas` se probará mediante confirmación completa, rollback total, Productos inactivos, cantidades inválidas, Productos repetidos, snapshots históricos, cálculo decimal, Medio de pago, idempotencia y concurrencia relevante.
- El historial se probará con Ventas a ambos lados de medianoche UTC y de Buenos Aires, orden descendente, días vacíos y cálculo del Total vendido antes y después de una Anulación.
- La Anulación se probará como irreversible, de una sola vez y con Motivo de anulación obligatorio. La Observación se probará como agregable, reemplazable y removible antes y después de anular.
- El frontend tendrá pruebas de interacción sobre los flujos de selección, errores recuperables, estado de carga, confirmación idempotente, gestión de catálogo, historial, Observación y Anulación.
- Un conjunto pequeño de pruebas de navegador recorrerá los flujos críticos contra frontend, proxy, backend y PostgreSQL reales: autenticación; creación de Producto; confirmación de Venta; consulta del Día de venta; Anulación y actualización del Total vendido.
- El contrato OpenAPI se validará en CI y el frontend comprobará que su adaptador HTTP sigue siendo compatible.
- No existe código previo ni prior art de pruebas en el repositorio. Esta spec establece la interfaz HTTP como superficie principal desde el primer ticket.

## Out of Scope

- Inventario, stock, recetas, ingredientes, sabores o peso efectivamente servido.
- Compras, proveedores, costos, márgenes o contabilidad.
- Clientes, cuentas corrientes, fidelización o entrega a domicilio.
- Facturación fiscal, comprobantes oficiales, integración con ARCA o impresión de tickets.
- Descuentos, promociones, cupones, recargos, propinas, impuestos separados o redondeos adicionales.
- Pagos parciales, pagos divididos, devoluciones de dinero o integración con procesadores de pago.
- Cierre de caja, arqueo, balance, movimientos de efectivo o conciliación bancaria.
- Edición o eliminación de una Venta confirmada y reversión de una Anulación.
- Registro retroactivo o elección manual del Momento de venta.
- Borrado físico de Productos mediante la aplicación.
- Auditoría histórica de cambios del catálogo más allá de los snapshots incluidos en Detalles de venta.
- Múltiples usuarios, roles, permisos, registro público, recuperación automática de contraseña u OAuth.
- Aplicación offline, sincronización diferida o modo instalable específico.
- Importación o exportación masiva, reportes mensuales, gráficos, métricas por Producto o por Medio de pago.
- Aplicaciones móviles nativas o clientes públicos distintos del navegador.

## Further Notes

- Esta especificación respeta las decisiones existentes de despliegue separado en Vercel, sesiones de servidor y almacenamiento de imágenes en Vercel Blob.
- Los tickets y pruebas deberán usar el vocabulario canónico del contexto: Producto, Venta, Detalle de venta, Medio de pago, Anulación, Observación, Total de venta, Total vendido, Día de venta y Momento de venta.
- La especificación es intencionalmente una primera entrega completa de registro de Ventas, no la definición de un ERP general.
- El siguiente paso es dividir esta spec en tickets tracer-bullet con dependencias explícitas mediante `/to-tickets`.
