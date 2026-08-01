# 03 — Modificar y activar o inactivar Productos

**What to build:** La persona que administra el catálogo puede corregir el nombre o precio de un Producto, inactivarlo sin eliminarlo, consultar también los Productos inactivos y reactivarlo cuando vuelva a ofrecerse.

**Blocked by:** 02 — Crear y consultar Productos.

**Status:** ready-for-agent

- [ ] La interfaz permite consultar claramente Productos activos e inactivos.
- [ ] Es posible modificar el nombre y el precio aplicando las mismas reglas de normalización, unicidad e Importe que durante la creación.
- [ ] Un Producto puede inactivarse y deja de aparecer entre las opciones disponibles para Ventas nuevas sin perder su identidad ni sus datos.
- [ ] Un Producto inactivo puede reactivarse y vuelve a estar disponible sin crear un duplicado.
- [ ] La unicidad del nombre se aplica conjuntamente a Productos activos e inactivos.
- [ ] La aplicación no ofrece borrado físico de Productos y las operaciones HTTP expresan activación, inactivación y modificación sin una actualización genérica ambigua.
- [ ] Las acciones muestran progreso, impiden envíos repetidos, conservan el formulario ante errores recuperables y comunican validaciones y conflictos en español.
- [ ] La gestión completa del catálogo es responsive y puede recorrerse con controles etiquetados, foco visible y teclado.
- [ ] Las pruebas HTTP contra PostgreSQL real cubren modificación, conflictos de nombre, activación, inactivación y consulta de ambos estados.
- [ ] Las pruebas de interacción comprueban que los cambios se reflejan en la vista activa o inactiva correspondiente sin depender de detalles internos del módulo.
