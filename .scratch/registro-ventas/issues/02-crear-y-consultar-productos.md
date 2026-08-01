# 02 — Crear y consultar Productos

**What to build:** La persona autenticada puede incorporar un Producto con nombre y precio y verlo inmediatamente entre los Productos activos disponibles. El sistema evita Productos indistinguibles, representa los importes con exactitud y mantiene una presentación consistente aunque todavía no exista una Imagen de producto propia.

**Blocked by:** 01 — Establecer la aplicación autenticada.

**Status:** ready-for-agent

- [ ] La interfaz autenticada permite listar Productos activos y crear un Producto con nombre y precio.
- [ ] Todo Producto nuevo queda activo y disponible inmediatamente después de una creación exitosa.
- [ ] El nombre visible se recorta en sus extremos y no puede quedar vacío.
- [ ] La unicidad del nombre ignora mayúsculas, minúsculas, acentos y espacios exteriores, y un conflicto se explica claramente en español.
- [ ] El precio es un Importe positivo con un máximo de dos decimales y nunca se procesa como punto flotante binario.
- [ ] Los importes se intercambian por JSON como cadenas decimales con dos posiciones.
- [ ] PostgreSQL protege mediante restricciones la unicidad normalizada del nombre y la positividad del precio, y las migraciones son reproducibles.
- [ ] Los Productos sin Imagen de producto propia muestran la imagen genérica incluida en el frontend con texto alternativo útil.
- [ ] La creación conserva los datos editables ante errores recuperables, impide envíos repetidos mientras está en curso y puede operarse con teclado y tecnologías de asistencia.
- [ ] Las pruebas HTTP contra PostgreSQL real cubren creación, consulta, normalización Unicode, duplicados y precios inválidos sin afirmar detalles internos del ORM.
- [ ] Una prueba de navegador recorre la creación de un Producto y comprueba que aparece en el catálogo mediante el límite HTTP same-origin.
