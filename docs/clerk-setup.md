# Configuración de Clerk para desarrollo

Guía para quien configura Clerk por primera vez en RM Shop. Se hace **una sola vez** para todo el equipo (ver el [paso 8](#8-recomendación-de-equipo)). Sin Clerk el proyecto arranca igual: la API responde `/health` y el frontend muestra una pantalla de configuración; solo fallan las partes que necesitan Clerk (inicio de sesión y `GET /me`).

> **Nota sobre el panel.** Clerk cambia con frecuencia los nombres de menús y botones. Los pasos marcan con ⚠️ lo que no pudimos confirmar contra la documentación vigente (1 de noviembre de 2026); si la etiqueta no coincide, busca la opción equivalente en la sección indicada.

## 1. Crear la aplicación y habilitar correo y contraseña

1. Entra a <https://dashboard.clerk.com> y crea una aplicación nueva, por ejemplo `RM Shop (desarrollo)`. Las aplicaciones nuevas son una **instancia de desarrollo** (sus claves empiezan por `pk_test_` y `sk_test_`).
2. En el menú lateral abre **User & authentication**.
3. En **Email**, activa **Sign-up with email** y el método de verificación **Email verification code** (código por correo). El enlace de verificación también sirve, pero obliga a abrirlo en el mismo navegador.
4. Activa **Password** como método de acceso.
5. Deja desactivados los inicios de sesión social: esta versión no los usa.

### Reglas de contraseña (P-2, supuesto)

El backlog deja las reglas de complejidad sin definir (P-2). Mientras la clienta no las fije, el equipo usa este **supuesto**, que se configura solo en Clerk (ni el frontend ni el backend validan contraseñas):

- Longitud mínima de 8 caracteres.
- Rechazar contraseñas filtradas en brechas de seguridad conocidas (**Reject compromised passwords**) ⚠️.
- Sin exigir mayúsculas, números ni símbolos.

En el panel: **User & authentication → Password** ⚠️ (la sección exacta puede variar). Si la clienta define otras reglas, solo se cambia ahí. Clerk devuelve errores de campo (contraseña corta, vacía o comprometida) que el formulario muestra marcando el campo (AC-HU-7-3).

### Textos de los mensajes

Los mensajes del formulario vienen de `@clerk/localizations` (`esES`). El criterio AC-HU-7-2 exige "Este correo ya está registrado", y `esES` dice otra cosa, así que `apps/frontend/src/app/localization.ts` lo sobrescribe. Si un criterio futuro pide otro texto, se agrega ahí.

## 2. Hacer obligatoria la verificación del correo

En la misma página **User & authentication**, en **Email**, deja activada la opción **Verify at sign-up** ⚠️ (la etiqueta puede variar). Con esto nadie completa el registro sin verificar su correo, y el backend puede suponer que toda sesión válida es de un correo verificado (`IsCustomer`).

## 3. Personalizar el token de sesión

El backend lee `email`, `first_name`, `last_name` y `role` del token. Sin esta plantilla, `GET /me` crea el usuario con correo y nombres vacíos y nadie puede ser administrador.

1. En el menú lateral abre **Sessions**.
2. En **Customize session token**, abre el editor **Claims**.
3. Pega exactamente este JSON y pulsa **Save**:

```json
{
  "email": "{{user.primary_email_address}}",
  "first_name": "{{user.first_name}}",
  "last_name": "{{user.last_name}}",
  "role": "{{user.public_metadata.role}}"
}
```

Notas:

- Los claims `sub`, `azp`, `exp`, `iat`, `iss`, `jti` y `nbf` los pone Clerk siempre y no se pueden sobrescribir.
- Las variables `{{user.primary_email_address}}`, `{{user.first_name}}` y `{{user.last_name}}` y la notación con puntos para metadatos (`{{user.public_metadata.…}}`) están en la documentación de Clerk. ⚠️ El ejemplo exacto con `public_metadata.role` no aparece allí; si el panel lo rechaza, avisa al equipo.
- El token viaja en una cookie de unos 4 KB; después de los claims de Clerk quedan cerca de 1,2 KB para los propios. Estos cuatro caben de sobra.
- Clerk renueva el token cada 60 segundos. Tras cambiar un rol, el nuevo valor puede tardar hasta un minuto en llegar a la API; cerrar sesión y volver a entrar lo fuerza.

## 4. Copiar las claves

1. En el menú lateral abre **API keys**.
2. Copia la **Publishable key** (`pk_test_…`) en `apps/frontend/.env`:

   ```dotenv
   VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
   ```

3. Copia la **Secret key** (`sk_test_…`) en `apps/backend/.env`:

   ```dotenv
   CLERK_SECRET_KEY=sk_test_...
   ```

4. Aplica los cambios. Compose lee los `.env` al crear los contenedores, y `docker compose restart` **no** los vuelve a leer:

   ```bash
   docker compose up -d
   ```

5. `CLERK_JWT_KEY` déjala **vacía** por ahora. Es opcional: con la clave pública PEM de la instancia (página **API keys**, ⚠️ bajo **Show JWT public key** o **Advanced**) la API verificaría los tokens sin llamar a Clerk, pero el formato de un PEM de varias líneas dentro de un `.env` de Docker Compose no está probado todavía. Sin ella, el backend descarga las claves públicas de Clerk con `CLERK_SECRET_KEY` y las guarda en caché.

Nunca pongas la `CLERK_SECRET_KEY` en el frontend ni en ningún archivo que se suba a git.

## 5. Origen autorizado

El origen no se configura en el panel de Clerk. El token de sesión lleva en su claim `azp` el origen desde el que se inició la sesión, y la API solo acepta los orígenes de `CLERK_AUTHORIZED_PARTIES`. El valor de `apps/backend/.env.example` ya es el de desarrollo local:

```dotenv
CLERK_AUTHORIZED_PARTIES=http://localhost:5173
```

Si abres el frontend desde otra dirección (por ejemplo `http://127.0.0.1:5173`), agrégala separada por comas. Si la variable queda vacía, la API rechaza todas las peticiones autenticadas con un error de configuración (`503 clerk_not_configured`).

## 6. Webhooks en local (opcional en el sprint 1)

El endpoint `POST /api/v1/webhooks/clerk` ya existe y mantiene sincronizada la tabla `users` (`user.created`, `user.updated`, `user.deleted`). Sin webhooks todo funciona igual: el primer `GET /me` autenticado crea el usuario local. Los webhooks solo hacen falta para probar la sincronización de cambios y bajas.

Clerk solo llama a direcciones públicas, así que necesitas un túnel hacia el puerto 8000:

```bash
ngrok http 8000
# o, con Cloudflare Tunnel:
cloudflared tunnel --url http://localhost:8000
```

1. Copia la URL pública que muestra el túnel (por ejemplo `https://abc123.ngrok-free.app`).
2. Agrega su host a `DJANGO_ALLOWED_HOSTS` en `apps/backend/.env` (por ejemplo `…,abc123.ngrok-free.app`) y ejecuta `docker compose up -d`. Sin esto Django responde `400` porque rechaza el host del túnel.
3. En Clerk abre **Webhooks** y pulsa **Add Endpoint**.
4. En **Endpoint URL** escribe `https://abc123.ngrok-free.app/api/v1/webhooks/clerk`.
5. En **Subscribe to events** marca `user.created`, `user.updated` y `user.deleted`, y pulsa **Create**.
6. En la página del endpoint copia el **Signing Secret** (empieza por `whsec_`; puede estar oculto tras el icono del ojo) en `apps/backend/.env`:

   ```dotenv
   CLERK_WEBHOOK_SECRET=whsec_...
   ```

7. Ejecuta `docker compose up -d` y, en la pestaña **Testing** del endpoint, envía un evento de ejemplo con **Send Example**. En **Message Attempts** debe aparecer **Succeeded**.

La URL del túnel cambia en cada sesión con ngrok gratuito, salvo que uses un dominio estático; actualiza el endpoint en Clerk cuando cambie. Clerk reintenta los eventos que reciben un error 4xx o 5xx.

## 7. Convertir un usuario en administrador (manual)

Hasta que exista el comando de gestión de HU-11, el rol se asigna a mano. El administrador es un usuario distinto del cliente: crea una cuenta nueva para él (o usa una existente).

1. El usuario debe haberse registrado al menos una vez (por `/registro` o `/admin/ingresar`).
2. En Clerk abre **Users** y selecciona al usuario.
3. En **User details**, ⚠️ sección de metadatos, edita **Public metadata** y guarda este JSON:

   ```json
   { "role": "admin" }
   ```

   Alternativa con la API de Clerk (reemplaza el identificador y la clave):

   ```bash
   curl -X PATCH https://api.clerk.com/v1/users/user_XXXXXXXX/metadata \
     -H "Authorization: Bearer $CLERK_SECRET_KEY" \
     -H "Content-Type: application/json" \
     -d '{"public_metadata": {"role": "admin"}}'
   ```

4. Pide al usuario que cierre sesión y vuelva a entrar por `/admin/ingresar`. El frontend lee el rol de `publicMetadata.role` y la API lo lee del claim `role` del token (puede tardar hasta un minuto, ver el paso 3).

Si el rol no es exactamente `admin`, el frontend muestra "No tienes permisos" y la API responde `403` en las rutas de administración. El límite de 3 administradores aún no se valida: llegará con HU-11.

## 8. Recomendación de equipo

- Usen **una sola instancia de desarrollo de Clerk** compartida. Cada persona con su propia instancia obliga a repetir esta guía, y los usuarios y roles de prueba no se comparten.
- Quien crea la instancia entrega las claves por un canal seguro (gestor de contraseñas o mensaje cifrado), nunca por el chat del grupo ni por correo sin cifrar.
- Las claves van solo en los archivos `.env`, que están en `.gitignore`. **Nunca** las subas a git. Si se filtra una clave, rótala en **API keys** y avisa al equipo.
- La instancia de producción será otra, con sus propias claves (`pk_live_` y `sk_live_`), cuando llegue el despliegue.

## Redirecciones

Al terminar el registro (después de verificar el correo con el código) y al iniciar sesión, el cliente vuelve a la página de la que venía (`redirect_url`) o, si no hay, al inicio (`/`). El panel de administración siempre termina en `/admin/productos`. Se configura con `fallbackRedirectUrl` en `SignUpPage.tsx` y `SignInPage.tsx`.

## Comprobación

1. Abre <http://localhost:5173/registro>, crea una cuenta y verifica el correo con el código que llega.
2. Inicia sesión en <http://localhost:5173/ingresar>. En la página de inicio, el bloque "Estado de la API (solo desarrollo)" debe mostrar el resultado de `GET /me` con tu correo y `"role": null`.
3. En la base debe existir un usuario nuevo: `docker compose exec db psql -U rmshop -c "select id, email, clerk_user_id from users;"`.
