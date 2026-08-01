# 01 — Establecer la aplicación autenticada

**What to build:** Una aplicación web desplegable y protegida para la única persona que atiende la heladería. Debe permitir iniciar una sesión persistente, acceder a una pantalla autenticada, cerrar la sesión del navegador actual y regresar al inicio de sesión cuando el acceso expire o sea revocado.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] El monorepo contiene un frontend Next.js y un backend FastAPI que pueden desplegarse como proyectos Vercel separados; el navegador usa rutas same-origin `/api/*` y el proxy no contiene reglas de negocio.
- [ ] La aplicación y las migraciones reproducibles usan PostgreSQL 17, con conexión agrupada para el tráfico normal y conexión directa para Alembic.
- [ ] Existe una única cuenta provisionada operativamente; su contraseña se verifica con Argon2id y parámetros configurables, y la contraseña original no se persiste ni se registra.
- [ ] Un login válido crea un identificador opaco y aleatorio en una cookie `Secure`, `HttpOnly` y `SameSite=Lax`; PostgreSQL conserva solamente una representación no reutilizable del token.
- [ ] La sesión dura 30 días desde la autenticación, se rota al iniciar sesión nuevamente y puede revocarse inmediatamente al cerrar sesión.
- [ ] Las credenciales incorrectas producen un mensaje genérico en español que no permite distinguir qué dato falló.
- [ ] Todas las rutas funcionales exigen una sesión válida y las mutaciones rechazan solicitudes que no tengan un origen same-origin válido.
- [ ] La interfaz redirige al login ante una sesión expirada o revocada, deshabilita envíos mientras están en curso y comunica el progreso y los errores de forma accesible.
- [ ] Las respuestas de error tienen una forma estable con código legible por máquina, mensaje en español y errores por campo cuando correspondan.
- [ ] Las pruebas HTTP en proceso ejercitan login, cookie, acceso autenticado, expiración, rotación, revocación y logout contra PostgreSQL 17 con las migraciones reales.
- [ ] Una prueba de navegador recorre el inicio y cierre de sesión a través del frontend, el proxy, el backend y PostgreSQL reales, con navegación por teclado y presentación funcional en computadora, tableta y teléfono.
- [ ] El contrato OpenAPI se valida automáticamente y el frontend concentra los tipos y transformaciones del contrato HTTP en un único adaptador comprobado como compatible.
