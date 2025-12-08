# ATHENAS Lite - Configuración de Keycloak

## Problema: "Parámetro no válido: redirect_uri"

El error ocurre porque el redirect_uri no está configurado en el client de Keycloak.

## Solución

### Opción 1: Agregar redirect_uri al client existente (maxi-business-ai)

1. Ir a Keycloak Admin: `https://sso.maxilabs.net/auth/admin`
2. Seleccionar realm: `zeusDev`
3. Ir a **Clients** → **maxi-business-ai**
4. En la pestaña **Settings**:
   - Buscar **Valid Redirect URIs**
   - Agregar: `http://localhost:3000/auth/callback`
   - Agregar: `http://localhost:3000/*` (para desarrollo)
5. En **Web Origins**:
   - Agregar: `http://localhost:3000`
6. Guardar cambios

### Opción 2: Crear un client nuevo para ATHENAS Lite

Si prefieres tener un client separado:

1. Ir a Keycloak Admin: `https://sso.maxilabs.net/auth/admin`
2. Seleccionar realm: `zeusDev`
3. **Clients** → **Create**
4. Configurar:
   - **Client ID**: `athenas-lite-web`
   - **Client Protocol**: `openid-connect`
   - **Access Type**: `confidential`
   - **Valid Redirect URIs**: 
     - `http://localhost:3000/auth/callback`
     - `http://localhost:3000/*`
   - **Web Origins**: `http://localhost:3000`
5. Ir a pestaña **Credentials**
6. Copiar el **Secret**
7. Actualizar `.env` en backend:
   ```
   KEYCLOAK_CLIENT_ID=athenas-lite-web
   KEYCLOAK_CLIENT_SECRET=<secret_copiado>
   ```

### Roles necesarios

Asegurarse de que existan estos roles en Keycloak:
- `athenas-admin` (para administradores)
- `athenas-user` (para usuarios normales)

Si no existen:
1. **Roles** → **Add Role**
2. Crear ambos roles
3. Asignar a usuarios en **Users** → [usuario] → **Role Mappings**

## Verificación

Después de configurar:
1. Reiniciar backend si es necesario
2. Ir a `http://localhost:3000`
3. Click en "Sign in with Google"
4. Debe redirigir correctamente a Keycloak
