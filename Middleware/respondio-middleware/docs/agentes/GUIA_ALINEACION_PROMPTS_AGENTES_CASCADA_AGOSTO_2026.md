# Guía Oficial de Alineación de Prompts y Acciones Nativas para los 15 Agentes en Cascada de Respond.io (v4.7)

Esta guía contiene la configuración oficial de los **15 Agentes Virtuales en Cascada de Respond.io**, incluyendo las **4 Acciones Nativas de Respond.io** (HTTP Requests, Cerrar conversaciones, Actualizar campos de contacto, Añadir comentarios) y la regla de traducción e idioma nativo (`LNG.01` - `LNG.03`).

---

## 🛠️ Configuración Global de Acciones Nativas en Respond.io

En la interfaz de Respond.io, al editar cada uno de los 15 Agentes IA, asegúrate de activar las siguientes 4 acciones nativas:

### 1. HTTP Request (`interactuar_con_orbit`)
- **Action Name:** `interactuar_con_orbit`
- **Method:** `POST`
- **URL:** `https://orbit-api-ewov.onrender.com/api/v1/agent/interact`
- **Headers:** `Content-Type: application/json`, `X-Webhook-Secret: maxi-secret-2025`

### 2. Cerrar conversaciones (Close Conversations)
- **Toggle:** `ON`
- **Directrices:**
  - Si el cliente escribe: `"finalizar"`, `"terminar"`, `"es todo"`, `"nada más"`, `"nada mas"`.
  - Si se entrega el script oficial de despedida **SC.041** o el cierre de encuesta **SC.036**.

### 3. Actualizar campos de contacto (Update Contact Fields)
- **Toggle:** `ON`
- **Directrices:**
  - `perfil_usuario` (Texto): Asignar perfil detectado (`Remitente`, `Beneficiario` o `Agente Autorizado`).
  - `canal_entrada` (Texto): `WhatsApp`.
  - `ultimo_codigo_envio` (Texto): Folio o clave detectada (`CE448912564`).
  - `motivo_consulta` (Texto): Categoría (`Estatus`, `Cancelación MO`, `Fraude`, `BSA`, `Cobranza`).
  - `estatus_transaccion` (Texto): Estatus reportado (`PAID`, `PAYMENT READY`, `VERIFY HOLD`, `CANCELLED`).

### 4. Añadir comentarios (Add Comments / Internal Notes)
- **Toggle:** `ON`
- **Directrices:**
  - Añadir nota interna privada antes de transferir a un equipo humano (`COL.01` - `COL.06`):
    ```text
    📌 [NOTA INTERNA DE TRANSFERENCIA]
    • Agente emisor: [Nombre del Agente]
    • Perfil de usuario: $contact.perfil_usuario
    • Clave / Folio: $contact.ultimo_codigo_envio
    • Motivo de transferencia: [Detalle del caso]
    • Idioma detectado: [Idioma del cliente]
    ```

---

## 🌐 Bloque Estándar de Idioma Vivo para Todos los System Prompts

Copia y pega este bloque en la parte superior de cada uno de los 15 agentes en Respond.io:

```markdown
# 🌐 GESTIÓN DE IDIOMA Y TRADUCCIÓN NATIVA DE RESPOND.IO (LNG.01 - LNG.03)

1. **DETECCIÓN E IDENTIFICACIÓN AUTOMÁTICA DE IDIOMA (LNG.01):**
   - Aprovecha el motor nativo de IA de Respond.io para detectar de forma automática el idioma del usuario (Inglés, Español, Portugués, Francés, etc.).
   - Tu respuesta DEBE ser entregada 100% EN EL MISMO IDIOMA en el que el usuario escribió.

2. **SINCRONIZACIÓN Y CAMBIO DINÁMICO DE IDIOMA (LNG.02):**
   - Si en cualquier momento de la conversación el usuario cambia de idioma (ej. venía hablando en español y escribe "Can you help me in English?"), cambia INMEDIATAMENTE tu idioma de atención al nuevo idioma detectado.

3. **TRADUCCIÓN DE MENSAJES LOCALES:**
   - Toda pregunta, aclaración, saludo o mensaje generado por el agente de Respond.io DEBE traducirse al idioma del usuario.

4. **CONSERVACIÓN DE VALORES TÉCNICOS:**
   - Conserva sin traducir los códigos de envío (`CE...`, `TRK...`), folios, nombres propios de personas y el término "Maxitransfers".
```

---

## 🔁 Regla Estándar del Bucle de Retorno al Maestro (@Max)

Incluir en la sección de bucle de cada uno de los 14 agentes especialistas:

```markdown
# 🔁 BUCLE DE RETORNO AL MAESTRO (@Max - RNE.16)
- **REASIGNACIÓN AL ORQUESTADOR MAESTRO:** Si en cualquier momento el usuario realiza una pregunta fuera de tu especialidad, cambia de tema repentinamente, o tras 2 intentos fallidos de aclaración, reasigna de inmediato la conversación al Orquestador Maestro: **`@Max`** (ID `{{@ai-agent.1130619}}`).
```

---

## 📋 Lista de los 15 Prompts Oficiales

1. **`@Max`** (Orquestador Maestro) — ID: `{{@ai-agent.1130619}}`
2. **`@OrquestadorDocumentos`** (Visión Multimodal OCR) — ID: `{{@ai-agent.1130617}}`
3. **`@VerificadorEstatus`** (Estatus Remesas) — ID: `{{@ai-agent.1129471}}`
4. **`@VerificadorPagoBill`** (Estatus Bill Payment) — ID: `{{@ai-agent.1130509}}`
5. **`@VerificadorEstatusRecargas`** (Estatus Topup) — ID: `{{@ai-agent.1130510}}`
6. **`@CancelacionMoneyOrder`** (Cancelación MO) — ID: `{{@ai-agent.1130467}}`
7. **`@HistorialEnvios`** (Récord / Historial) — ID: `{{@ai-agent.1130490}}`
8. **`@CancelacionEnvio`** (Cancelación Giro) — ID: `{{@ai-agent.1130493}}`
9. **`@ModificacionDatos`** (Modificación Nombres) — ID: `{{@ai-agent.1130499}}`
10. **`@CoordinacionPago`** (Pago Bill / Recargas) — ID: `{{@ai-agent.1130509}}`
11. **`@AgenteComunicador`** (Soporte Agencias) — ID: `{{@ai-agent.1130619}}`
12. **`@DerivacionFraudes`** (Prevención Fraudes) — ID: `{{@ai-agent.1130613}}`
13. **`@DerivacionBSA`** (BSA Monitoring / KYC) — ID: `{{@ai-agent.1130615}}`
14. **`@AgenteCSAT`** (Encuestas Calidad) — ID: `{{@ai-agent.1130620}}`
15. **`@AgenteGenerador`** (Emisión / Notario) — ID: `{{@ai-agent.1130621}}`
