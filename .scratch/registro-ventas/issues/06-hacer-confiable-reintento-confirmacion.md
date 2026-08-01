# 06 — Hacer confiable el reintento de confirmación

**What to build:** La confirmación de una Venta resiste dobles pulsaciones, reintentos y respuestas perdidas sin crear duplicados ni inducir a la persona a creer que una Venta incierta fue confirmada.

**Blocked by:** 05 — Armar y confirmar una Venta.

**Status:** ready-for-agent

- [ ] PostgreSQL impone la unicidad necesaria para que una clave de idempotencia no pueda crear más de una Venta.
- [ ] Repetir una confirmación con la misma clave y el mismo contenido devuelve la representación autoritativa de la Venta ya creada.
- [ ] Reutilizar una clave con contenido diferente se rechaza como conflicto mediante la forma estable de error y un mensaje claro en español.
- [ ] Una doble pulsación no inicia dos confirmaciones y la interfaz mantiene deshabilitada la acción mientras la solicitud está en curso.
- [ ] Si se pierde la respuesta, la interfaz conserva la selección y reconcilia el resultado reutilizando la misma clave antes de permitir otra Venta equivalente.
- [ ] La persona puede distinguir entre una confirmación en curso, una Venta confirmada, un error corregible y un resultado todavía no comprobable.
- [ ] Los reintentos no cambian el Momento de venta, Detalles, Medio de pago ni Total de venta de la Venta originalmente creada.
- [ ] Las pruebas HTTP con PostgreSQL real cubren solicitudes repetidas iguales, reutilización conflictiva, intentos concurrentes y respuesta recuperada después de una escritura exitosa.
- [ ] Las pruebas de interacción simulan doble pulsación, fallo de red antes de responder y reconciliación posterior sin afirmar llamadas internas.
