# Ventas en Cucurucho

Este contexto describe el lenguaje de Cucurucho, la aplicación de registro de ventas de una heladería atendida por una sola persona.

## Language

**Producto**:
Una presentación vendible con nombre único y precio positivo propios, como ¼ kg, ½ kg, cucurucho, torta helada o gaseosa. La unicidad del nombre ignora espacios exteriores y no distingue mayúsculas, minúsculas ni acentos; el producto no identifica sabores, ingredientes ni el peso efectivamente servido.
_Avoid_: Sabor, ingrediente

**Producto inactivo**:
Un producto conservado en el catálogo que no puede seleccionarse en ventas nuevas. Puede reactivarse y sigue siendo reconocible en ventas anteriores.
_Avoid_: Producto eliminado

**Imagen de producto**:
Una representación visual opcional de un producto. Cuando no se proporciona una imagen propia, el producto se presenta con una imagen genérica.
_Avoid_: Imagen obligatoria, galería

**Venta**:
La compra completa y confirmada realizada por una persona. Contiene uno o más detalles con sus respectivas cantidades; un mismo producto puede aparecer en más de un detalle, no puede existir vacía y su armado previo no se guarda. Sus datos económicos y temporales no cambian después de confirmarse.
_Avoid_: Pedido, operación

**Cantidad**:
El número entero y positivo de unidades de un producto incluido en una venta. El peso indicado en el nombre de un producto no convierte su cantidad en fraccionaria.
_Avoid_: Peso servido, cantidad decimal

**Detalle de venta**:
El nombre y precio unitario de un producto, junto con la cantidad vendida, conservados tal como eran al confirmar la venta. Los cambios posteriores del producto no modifican este detalle.
_Avoid_: Producto actual, precio actual

**Medio de pago**:
La forma única mediante la cual se abona una venta: efectivo, transferencia, tarjeta de débito, tarjeta de crédito o QR. Una venta no admite pagos combinados.
_Avoid_: Pago parcial, pago dividido

**Precio de venta**:
El precio unitario efectivamente cobrado por un producto dentro de una venta, tomado del precio vigente del producto y no modificable al registrar la compra. Permanece inalterado aunque posteriormente cambie el precio del producto.
_Avoid_: Precio actual

**Importe**:
Una cantidad expresada exclusivamente en pesos argentinos, con hasta dos decimales. El sistema no maneja otras monedas.
_Avoid_: Monto en dólares, importe convertido

**Total de venta**:
La suma del precio de venta multiplicado por la cantidad de cada detalle de una venta. No incluye descuentos, recargos, impuestos separados ni redondeos adicionales.
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
