# Ventas en Cucurucho

Este contexto describe el lenguaje de Cucurucho, la aplicación de registro de ventas de una heladería atendida por una sola persona.

## Language

**Producto**:
Una presentación vendible con nombre único, precio positivo y forma de venta propia: por unidad o por kilogramo. Ejemplos: ¼ kg, ½ kg, cucurucho, torta helada o gaseosa. El precio de un Producto por kilogramo es su tarifa por kilo. La unicidad del nombre ignora espacios exteriores y no distingue mayúsculas, minúsculas ni acentos; el producto no identifica sabores ni ingredientes.
_Avoid_: Sabor, ingrediente

**Producto inactivo**:
Un producto conservado en el catálogo que no puede seleccionarse en ventas nuevas. Puede reactivarse y sigue siendo reconocible en ventas anteriores.
_Avoid_: Producto eliminado

**Categoría**:
La clasificación obligatoria y editable que agrupa Productos para encontrarlos rápidamente al preparar una Venta. Cada Producto pertenece a una única Categoría; varias Categorías pueden seleccionarse a la vez como filtro y, sin selección, se muestran todos los Productos activos.
_Avoid_: Etiqueta, categoría múltiple por Producto

**Imagen de producto**:
Una representación visual opcional de un producto. Cuando no se proporciona una imagen propia, el producto se presenta con una imagen genérica.
_Avoid_: Imagen obligatoria, galería

**Venta**:
La compra completa y confirmada realizada por una persona. Contiene uno o más detalles con sus respectivas cantidades; un mismo producto puede aparecer en más de un detalle, no puede existir vacía y su armado previo no se guarda. Sus datos económicos y temporales no cambian después de confirmarse.
_Avoid_: Pedido, operación

**Cantidad**:
El número entero y positivo de unidades de un Producto vendido por unidad. Cada Producto vendido por kilogramo ocupa un detalle separado con cantidad 1 y un peso positivo con precisión de gramos.
_Avoid_: Usar cantidades decimales para unidades

**Detalle de venta**:
Conserva el nombre, tarifa y forma de venta del Producto, su cantidad, el peso cuando corresponde, el modo de ingreso (peso o importe) y el importe efectivamente cobrado. Los cambios posteriores del Producto no modifican estos datos.
_Avoid_: Producto actual, precio actual

**Medio de pago**:
La forma única mediante la cual se abona una venta: efectivo, transferencia, tarjeta de débito, tarjeta de crédito o QR. Una venta no admite pagos combinados.
_Avoid_: Pago parcial, pago dividido

**Precio de venta**:
Tarifa histórica por unidad o por kilogramo, tomada del Producto vigente al confirmar la Venta. No es editable directamente; para los Productos por kilogramo puede ingresarse el peso o el importe final. La tarifa histórica permanece inalterada cuando cambia el Producto.
_Avoid_: Precio actual

**Importe**:
Una cantidad expresada exclusivamente en pesos argentinos, con hasta dos decimales. El sistema no maneja otras monedas.
_Avoid_: Monto en dólares, importe convertido

**Total de venta**:
La suma de los importes de los detalles de una Venta. Para unidades se multiplica la tarifa por la cantidad; para kilos ingresados se multiplica la tarifa por el peso y se redondea a centavos; si se ingresa el importe final se guarda exactamente ese importe y se estima el peso a tres decimales. No hay descuentos ni recargos.
_Avoid_: Subtotal, total estimado

**Anulación**:
La invalidación irreversible de una venta confirmada sin editarla ni eliminarla. Cada venta puede anularse una sola vez; conserva todos sus datos originales, requiere un motivo inmutable y no puede deshacerse.
_Avoid_: Eliminación, edición, cancelación

**Motivo de anulación**:
El texto obligatorio y no vacío que explica una anulación. Queda conservado sin cambios junto con la venta anulada.
_Avoid_: Observación de anulación, comentario editable

**Observación**:
Un texto opcional y no vacío asociado a una venta que puede agregarse, reemplazarse o quitarse después de confirmarla, incluso tras su anulación. No altera sus productos, importes, medio de pago, momento ni estado.
_Avoid_: Nota financiera, corrección de venta

**Total vendido**:
La suma de los totales de las ventas no anuladas de un día de venta. Las ventas anuladas no contribuyen al total.
_Avoid_: Cierre de caja, balance

**Día de venta**:
El día calendario de `America/Argentina/Buenos_Aires` al que pertenece una venta. No depende de la fecha o zona horaria del servidor.
_Avoid_: Día UTC, jornada de caja

**Momento de venta**:
El instante asignado por el sistema cuando se confirma una venta. No puede elegirse ni modificarse manualmente.
_Avoid_: Fecha de carga, fecha retroactiva



## Costos y rentabilidad (desde la versión 0004)

**Insumo**:
Bien adquirido para elaborar o entregar un Producto. Se identifica por nombre único y unidad de medida (kg o unidad). Se puede inactivar sin borrar su historial.

**Compra de insumo**:
Registro de cantidad, importe total y costo unitario calculado en el momento de la compra. No se modifica ni elimina. La última compra registrada actualiza el costo unitario vigente del Insumo; no se calcula costo promedio ponderado del inventario ni stock físico en esta etapa.

**Receta de producto**:
Asociación entre un Producto y uno o varios Insumos, con cantidad de consumo. Para Productos vendidos por unidad, el consumo escala por la cantidad vendida. Para Productos vendidos por peso, el consumo «variable» escala por kg facturado, mientras el consumo «fijo» aplica una vez por detalle (por ejemplo el envase). La receta editable se aplica solo a ventas futuras.

**Costo histórico de detalle**:
Al confirmar una Venta se congela el costo estimado de insumos a partir de la receta y los últimos costos unitarios registrados. Si falta una receta o el costo vigente de cualquier insumo, el costo del detalle es desconocido (`NULL`), nunca cero. Modificar compras, precios o recetas no recalcula ventas anteriores. Las ventas históricas anteriores a esta funcionalidad no tienen costo.

**Ganancia bruta calculable**:
Ingresos de los detalles con costo histórico conocido menos esos costos. El margen se divide solo por los ingresos de esos detalles, y se muestran aparte los ingresos pendientes de costear. Las anulaciones excluyen por completo ingresos y costos. No representa utilidad neta: no descuenta servicios, alquiler, sueldos, impuestos, comisiones, desperdicios ni otros gastos generales.

**Stock**:
Fuera del alcance actual. Las compras quedan registradas para futura gestión de existencias, pero las ventas no descuentan inventario y no se ofrecen saldos físicos engañosos.
