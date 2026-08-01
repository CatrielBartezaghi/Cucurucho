# 04 — Gestionar la Imagen de producto

**What to build:** La persona que administra el catálogo puede agregar, reemplazar o quitar la Imagen de producto para reconocer visualmente cada presentación, sin perder la imagen vigente cuando una operación externa o de persistencia falla.

**Blocked by:** 02 — Crear y consultar Productos.

**Status:** ready-for-agent

- [ ] La interfaz permite cargar mediante `multipart/form-data` una imagen JPEG, PNG o WebP de hasta 5 MB.
- [ ] Un formato no admitido o un archivo que supera el límite se rechaza con una validación clara en español y no modifica el Producto.
- [ ] Es posible reemplazar una Imagen de producto existente y ver la nueva representación después de una operación exitosa.
- [ ] Es posible quitar la Imagen de producto y volver inmediatamente a la imagen genérica del frontend.
- [ ] Un fallo de carga o persistencia durante un reemplazo conserva la imagen anterior y PostgreSQL nunca queda apuntando a un objeto inexistente.
- [ ] La eliminación de objetos reemplazados o quitados es segura y observable; un fallo de limpieza no invalida la referencia vigente del Producto.
- [ ] El almacenamiento de imágenes está detrás de un port interno con un adaptador de Vercel Blob para producción y un adaptador controlable para pruebas, sin exponerlo en la interfaz pública del módulo.
- [ ] Las imágenes tienen texto alternativo útil y las acciones de carga, reemplazo y eliminación muestran progreso, evitan envíos repetidos y funcionan con teclado.
- [ ] Las pruebas HTTP usan el adaptador controlable para cubrir carga, reemplazo, eliminación, validación y fallos parciales sin solicitudes reales a Vercel.
- [ ] Las pruebas de interacción comprueban la imagen propia y el retorno a la imagen genérica a través del contrato HTTP.
