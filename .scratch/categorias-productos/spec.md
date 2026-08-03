# Categorías de Productos

## Alcance

- Todo Producto pertenece obligatoriamente a una única Categoría.
- El sistema incluye inicialmente las Categorías `Helado`, `Envasado` y `Otros`.
- La migración asigna `Helado` a todos los Productos existentes.
- La persona administradora puede crear Categorías y cambiarles el nombre.
- Al crear o editar un Producto se debe elegir su Categoría.
- En Nueva Venta se pueden seleccionar varias Categorías para filtrar los Productos activos.
- Si no se selecciona ninguna Categoría, se muestran todos los Productos activos.

## Interfaces públicas bajo prueba

- API HTTP: listado, creación y edición de Categorías; creación y edición de Productos con Categoría obligatoria.
- `RegisterSale`: filtro de Productos por la unión de las Categorías seleccionadas.

