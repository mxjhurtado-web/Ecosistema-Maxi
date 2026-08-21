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
  - Si el cliente escribe: `"finalizar"`, `"terminar"`, `"es todo"`, `"nada mas"`, `"nada mas"`.
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

## 🌐 Bloque Estandar de Idioma Vivo para Todos los System Prompts

Copia y pega este bloque en la parte superior de cada uno de los 15 agentes en Respond.io:

```markdown
# 🌐 GESTIÓN DE IDIOMA Y TRADUCCIÓN NATIVA DE RESPOND.IO (LNG.01 - LNG.03)

1. **DETECCIÓN E IDENTIFICACIÓN AUTOMÁTICA DE IDIOMA (LNG.01):**
   - Aprovecha el motor nativo de IA de Respond.io para detectar de forma automatica el idioma del usuario (Inglés, Español, Portugués, Francés, etc.).
   - Tu respuesta DEBE ser entregada 100% EN EL MISMO IDIOMA en el que el usuario escribió.

2. **SINCRONIZACIÓN Y CAMBIO DINÁMICO DE IDIOMA (LNG.02):**
   - Si en cualquier momento de la conversación el usuario cambia de idioma (ej. venía hablando en español y escribe "Can you help me in English?"), cambia INMEDIATAMENTE tu idioma de atención al nuevo idioma detectado.

3. **TRADUCCIÓN DE MENSAJES LOCALES:**
   - Toda pregunta, aclaración, saludo o mensaje generado por el agente de Respond.io DEBE traducirse al idioma del usuario.

4. **CONSERVACIÓN DE VALORES TÉCNICOS:**
   - Conserva sin traducir los códigos de envío (`CE...`, `TRK...`), folios, nombres propios de personas y el término "Maxitransfers".
```

---

## 🔁 Regla Estandar del Bucle de Retorno al Maestro (@Max)

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


---

## 📝 Textos Listos para Copiar y Pegar en los Cuadros de Instrucción de Respond.io (Todos < 1,000 caracteres)

### 1️⃣ Cuadro: "Asignar a agente o equipo" (Assign to Agent or Team - Max 1,000 chars)
```text
* Configurar según respuesta del campo derivacion de ORBIT:
* estatus_transaccion -> @VerificadorEstatus ({{@ai-agent.1129471}})
* cancelacion_money_order -> @CancelacionMoneyOrder ({{@ai-agent.1130467}})
* historial_envios -> @HistorialEnvios ({{@ai-agent.1130490}})
* cancelacion_envio -> @CancelacionEnvio ({{@ai-agent.1130493}})
* modificacion_datos -> @ModificacionDatos ({{@ai-agent.1130499}})
* pagos_bill_recarga_deposito -> @CoordinacionPago ({{@ai-agent.1130509}})
* soporte_interno -> @AgenteComunicador ({{@ai-agent.1130619}})
* fraude_estafa -> @DerivacionFraudes ({{@ai-agent.1130613}})
* actividad_sospechosa -> @DerivacionBSA ({{@ai-agent.1130615}})
* tipo_input=documento -> @OrquestadorDocumentos ({{@ai-agent.1130617}})
* hablar_con_humano -> Asesores Servicio al Cliente ({{@team.43621}})
* bucle_retorno_maestro -> @Max ({{@ai-agent.1130619}})
```

### 2️⃣ Cuadro: "Cerrar conversaciones" (Close Conversations - Max 1,000 chars)
```text
- Si el cliente escribe "finalizar", cerrar conversación.
- Si el cliente escribe "terminar", cerrar conversación.
- Si el cliente indica que desea concluir la conversación ("es todo", "nada mas", "nada mas"), cerrar conversación.
- Si el sistema o el agente entrega el script oficial de despedida SC.041 o el cierre de encuesta CSAT SC.036, cerrar conversación.
```

### 3️⃣ Cuadro: "Actualizar campos de contacto" (Update Contact Fields - Max 1,000 chars)
```text
Cada vez que en la conversación se mencione o detecte información de contacto:
- perfil_usuario (Texto): Asignar perfil detectado (Remitente, Beneficiario o Agente Autorizado).
- canal_entrada (Texto): Canal por el que ingresa (ej: WhatsApp).
- ultimo_codigo_envio (Texto): Código de envío, folio o tracking number detectado (ej: CE448912564).
- motivo_consulta (Texto): Categoría detectada (Estatus, Cancelación MO, Fraude, BSA, Cobranza).
- estatus_transaccion (Texto): Estatus reportado (PAID, PAYMENT READY, VERIFY HOLD, CANCELLED).
```

### 4️⃣ Cuadro: "Añadir comentarios" (Add Comments - Max 1,000 chars)
```text
Añade un comentario interno privado antes de asignar a un equipo humano o reasignar agente:
📌 [NOTA INTERNA DE TRANSFERENCIA]
• Agente emisor: $agent.name
• Perfil usuario: $contact.perfil_usuario
• Clave / Folio: $contact.ultimo_codigo_envio
• Motivo transferencia: $contact.motivo_consulta
• Idioma detectado: Idioma del cliente
```


---

## 🏛️ Configuración Específica de las 4 Acciones Nativas para Cada Uno de los 15 Agentes

Cada agente es independiente y tiene su propia tarjeta de configuración en Respond.io. A continuación se detallan los textos exactos para copiar y pegar en los 4 cuadros de cada agente especializado:

---

### 👑 1. Agente Maestro — Max (`@Max`) - ID: `{{@ai-agent.1130619}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "Max"}}
  ```
* **Asignar a agente o equipo (Max 1,000 chars):**
  ```text
  * Configurar según instrucción de derivación devuelta por ORBIT:
  * estatus_transaccion -> @VerificadorEstatus ({{@ai-agent.1129471}})
  * cancelacion_money_order -> @CancelacionMoneyOrder ({{@ai-agent.1130467}})
  * historial_envios -> @HistorialEnvios ({{@ai-agent.1130490}})
  * cancelacion_envio -> @CancelacionEnvio ({{@ai-agent.1130493}})
  * modificacion_datos -> @ModificacionDatos ({{@ai-agent.1130499}})
  * pagos_bill_recarga_deposito -> @CoordinacionPago ({{@ai-agent.1130509}})
  * soporte_interno -> @AgenteComunicador ({{@ai-agent.1130619}})
  * fraude_estafa -> @DerivacionFraudes ({{@ai-agent.1130613}})
  * actividad_sospechosa -> @DerivacionBSA ({{@ai-agent.1130615}})
  * tipo_input=documento -> @OrquestadorDocumentos ({{@ai-agent.1130617}})
  * hablar_con_humano -> Asesores Servicio al Cliente ({{@team.43621}})
  ```
* **Cerrar conversaciones:**
  ```text
  - Si el cliente escribe "finalizar", "terminar", "es todo" o "nada mas", cerrar conversación.
  - Si se entrega el script oficial de despedida SC.041, cerrar conversación.
  ```
* **Actualizar campos de contacto:**
  ```text
  - perfil_usuario: Asignar Remitente, Beneficiario o Agente.
  - canal_entrada: WhatsApp.
  - motivo_consulta: Asignar categoría detectada (Estatus, Cancela MO, Fraude, BSA).
  ```
* **Añadir comentarios:**
  ```text
  Añade nota interna antes de derivar a Fraudes o BSA:
  📌 [ALERTA DE TRANSFERENCIA DESDE @MAX]
  • Contacto: $contact.id | Motivo: $contact.motivo_consulta | Idioma: Idioma del cliente
  ```

---

### 🔍 2. Agente Verificador de Estatus (`@VerificadorEstatus`) - ID: `{{@ai-agent.1129471}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "VerificadorEstatus"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Si requiere asesor humano o se cumplen 2 intentos fallidos: Asesores Servicio al Cliente ({{@team.43621}})
  * Si la consulta cambia de tema o es fuera de alcance: @Max ({{@ai-agent.1130619}})
  * Si concluye consulta y requiere encuesta: @AgenteCSAT ({{@ai-agent.1130620}})
  ```
* **Cerrar conversaciones:**
  ```text
  - Si el cliente indica que concluyó ("es todo", "nada mas", "finalizar"), transferir a @AgenteCSAT o cerrar conversación tras SC.041.
  ```
* **Actualizar campos de contacto:**
  ```text
  - ultimo_codigo_envio: Clave de envío detectada (ej: CE448912564).
  - estatus_transaccion: Estatus devuelto (PAID, PAYMENT READY, VERIFY HOLD, CANCELLED).
  ```
* **Añadir comentarios:**
  ```text
  📌 [REPORTE ESTATUS GIRO - ESCALAMIENTO]
  • Código: $contact.ultimo_codigo_envio | Estatus: $contact.estatus_transaccion
  • Motivo transferencia: Escalamiento a asesor humano Servicio al Cliente.
  ```

---

### 🧾 3. Agente Verificador Pago Bill (`@VerificadorPagoBill`) - ID: `{{@ai-agent.1130509}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "VerificadorPagoBill"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Si requiere aclaración de factura o asesor humano: Asesores Servicio al Cliente ({{@team.43621}})
  * Si el usuario cambia de tema: @Max ({{@ai-agent.1130619}})
  * Si concluyó exitosamente: @AgenteCSAT ({{@ai-agent.1130620}})
  ```
* **Cerrar conversaciones:**
  ```text
  - Si el cliente escribe "finalizar", "terminar", "es todo", "nada mas", transferir a CSAT o cerrar.
  ```
* **Actualizar campos de contacto:**
  ```text
  - ultimo_codigo_envio: Número de tracking TRK detectado.
  - estatus_transaccion: Estatus de bill payment (PAID, CANCELLED, PENDING).
  ```
* **Añadir comentarios:**
  ```text
  📌 [REPORTE BILL PAYMENT]
  • Tracking TRK: $contact.ultimo_codigo_envio | Estatus: $contact.estatus_transaccion
  • Motivo: Requiere atención especializada de factura.
  ```

---

### 📱 4. Agente Estatus Recargas (`@VerificadorEstatusRecargas`) - ID: `{{@ai-agent.1130510}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "VerificadorEstatusRecargas"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Si requiere aclaración técnica o refund: Asesores Servicio al Cliente ({{@team.43621}})
  * Si el usuario cambia de tema: @Max ({{@ai-agent.1130619}})
  ```
* **Cerrar conversaciones:**
  ```text
  - Cierra la conversación al entregar el comprobante de recarga o tras recibir comando de término.
  ```
* **Actualizar campos de contacto:**
  ```text
  - ultimo_codigo_envio: Número de celular o transacción recarga.
  - estatus_transaccion: Estatus de topup (APLICADA, PENDIENTE, FALLIDA).
  ```
* **Añadir comentarios:**
  ```text
  📌 [REPORTE RECARGA TELEFÓNICA]
  • Número: $contact.ultimo_codigo_envio | Estatus: $contact.estatus_transaccion
  ```

---

### 🎟️ 5. Agente Cancelación Money Order (`@CancelacionMoneyOrder`) - ID: `{{@ai-agent.1130467}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "CancelacionMoneyOrder"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Transferencia obligatoria tras recaudar datos de MO: Asesores Servicio al Cliente ({{@team.43621}})
  * Si la consulta no es sobre Money Order: @Max ({{@ai-agent.1130619}})
  ```
* **Cerrar conversaciones:**
  ```text
  - NO CERRAR. Transferir siempre a asesor humano para procesar reembolso físico.
  ```
* **Actualizar campos de contacto:**
  ```text
  - ultimo_codigo_envio: Número de Money Order / Folio.
  - motivo_consulta: Cancelación de Money Order.
  ```
* **Añadir comentarios:**
  ```text
  📌 [SOLICITUD CANCELACIÓN MONEY ORDER]
  • Folio MO: $contact.ultimo_codigo_envio | Remitente: $contact.name
  • Estado: Datos recaudados, listo para procesar cheque de reembolso.
  ```

---

### ✏️ 6. Agente Modificación de Datos (`@ModificacionDatos`) - ID: `{{@ai-agent.1130499}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "ModificacionDatos"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Transferencia obligatoria con datos: Asesores Servicio al Cliente ({{@team.43621}})
  * Si cambia de tema: @Max ({{@ai-agent.1130619}})
  ```
* **Cerrar conversaciones:**
  ```text
  - NO CERRAR. Transferir a asesor humano para corregir el nombre en sistema.
  ```
* **Actualizar campos de contacto:**
  ```text
  - ultimo_codigo_envio: Clave de envío a modificar.
  - motivo_consulta: Modificación de Nombre / Corrección de Datos.
  ```
* **Añadir comentarios:**
  ```text
  📌 [SOLICITUD MODIFICACIÓN DE DATOS GIRO]
  • Clave Giro: $contact.ultimo_codigo_envio
  • Corrección solicitada: $message.text
  ```

---

### 🚫 7. Agente Cancelación de Envío (`@CancelacionEnvio`) - ID: `{{@ai-agent.1130493}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "CancelacionEnvio"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Transferencia obligatoria: Asesores Servicio al Cliente ({{@team.43621}})
  * Si cambia de tema: @Max ({{@ai-agent.1130619}})
  ```
* **Cerrar conversaciones:**
  ```text
  - NO CERRAR. Transferir a asesor humano para detener el pago en pagador.
  ```
* **Actualizar campos de contacto:**
  ```text
  - ultimo_codigo_envio: Clave de envío a cancelar.
  - motivo_consulta: Cancelación de Giro Activo.
  ```
* **Añadir comentarios:**
  ```text
  📌 [SOLICITUD CANCELACIÓN DE GIRO]
  • Clave Giro: $contact.ultimo_codigo_envio | Perfil: $contact.perfil_usuario
  • Prioridad: Alta (Detener pago urgente).
  ```

---

### 📜 8. Agente Historial de Envíos (`@HistorialEnvios`) - ID: `{{@ai-agent.1130490}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "HistorialEnvios"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Transferencia a asesor para envío de estado de cuenta: Asesores Servicio al Cliente ({{@team.43621}})
  * Si cambia de tema: @Max ({{@ai-agent.1130619}})
  ```
* **Cerrar conversaciones:**
  ```text
  - Cierra tras entregar el resumen en texto o transferir a asesor.
  ```
* **Actualizar campos de contacto:**
  ```text
  - motivo_consulta: Consulta de Historial / Reporte Anual.
  ```
* **Añadir comentarios:**
  ```text
  📌 [SOLICITUD HISTORIAL DE TRANSACCIONES]
  • Cliente: $contact.name | Teléfono: $contact.phone
  ```

---

### 💳 9. Agente Coordinación de Pago (`@CoordinacionPago`) - ID: `{{@ai-agent.1130509}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "CoordinacionPago"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Si es ficha de depósito / balance agencia: Equipo de Cobranza ({{@team.43625}})
  * Si es cliente regular: Asesores Servicio al Cliente ({{@team.43621}})
  * Si cambia de tema: @Max ({{@ai-agent.1130619}})
  ```
* **Cerrar conversaciones:**
  ```text
  - NO CERRAR. Transferir a equipo de Cobranza / Asesor.
  ```
* **Actualizar campos de contacto:**
  ```text
  - motivo_consulta: Coordinación de Pagos / Ficha Depósito.
  ```
* **Añadir comentarios:**
  ```text
  📌 [NOTIFICACIÓN DE FICHA DE DEPÓSITO / COBRANZA]
  • Agencia / Usuario: $contact.name | Detalle: $message.text
  ```

---

### 📢 10. Agente Comunicador Interno (`@AgenteComunicador`) - ID: `{{@ai-agent.1130619}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "AgenteComunicador"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Si es Oversight / IRS: Equipo Auditoría / Compliance
  * Si es Soporte POS / Hardware: Equipo Soporte Técnico ({{@team.43630}})
  * Si es consulta general: @Max ({{@ai-agent.1130619}})
  ```
* **Cerrar conversaciones:**
  ```text
  - Cierra tras notificar al canal de Google Chat correspondiente.
  ```
* **Actualizar campos de contacto:**
  ```text
  - motivo_consulta: Soporte Agencia / Comunicado Interno.
  ```
* **Añadir comentarios:**
  ```text
  📌 [REPORTE INTERNO DE AGENCIA / SOPORTE]
  • Destino: Google Chat Alerta enviada | Intención: $contact.motivo_consulta
  ```

---

### 🚨 11. Agente Derivación Fraudes (`@DerivacionFraudes`) - ID: `{{@ai-agent.1130613}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "DerivacionFraudes"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Transferencia URGENTE a departamento especializado: Equipo Prevención de Fraudes ({{@team.43610}})
  ```
* **Cerrar conversaciones:**
  ```text
  - NO CERRAR NUNCA AUTOMÁTICAMENTE. Requiere atención y protocolo humano obligatorio.
  ```
* **Actualizar campos de contacto:**
  ```text
  - motivo_consulta: ALERTA CRÍTICA FRAUDE / ESTAFA.
  ```
* **Añadir comentarios:**
  ```text
  🚨 [ALERTA CRÍTICA - REPORTE DE FRAUDE / ESTAFA]
  • Cliente: $contact.name | Teléfono: $contact.phone
  • Clave Giro: $contact.ultimo_codigo_envio
  • Detalle reporte: $message.text
  ```

---

### 🔍 12. Agente Derivación BSA (`@DerivacionBSA`) - ID: `{{@ai-agent.1130615}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "DerivacionBSA"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Transferencia a departamento de Cumplimiento: Equipo Cumplimiento BSA ({{@team.43615}})
  ```
* **Cerrar conversaciones:**
  ```text
  - NO CERRAR. Transferir a oficial de Cumplimiento BSA.
  ```
* **Actualizar campos de contacto:**
  ```text
  - motivo_consulta: Cumplimiento BSA / Retención KYC.
  ```
* **Añadir comentarios:**
  ```text
  🔍 [REPORTE CUMPLIMIENTO BSA / KYC HOLD]
  • Clave Giro: $contact.ultimo_codigo_envio | Retención: VERIFY HOLD (KYC)
  • Acción requerida: Validación de documentos de identidad / Formulario P-4.
  ```

---

### 📄 13. Agente Orquestador Documentos (`@OrquestadorDocumentos`) - ID: `{{@ai-agent.1130617}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "OrquestadorDocumentos"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Si OCR detecta recibo de remesa: @VerificadorEstatus ({{@ai-agent.1129471}})
  * Si es ID / Carta KYC: @DerivacionBSA ({{@ai-agent.1130615}})
  * Si es ilegible o texto libre: @Max ({{@ai-agent.1130619}})
  ```
* **Cerrar conversaciones:**
  ```text
  - No cerrar directamente; derivar según clasificación visual.
  ```
* **Actualizar campos de contacto:**
  ```text
  - ultimo_codigo_envio: Código leido por OCR en la imagen.
  - motivo_consulta: Documento Recibido / OCR Multimodal.
  ```
* **Añadir comentarios:**
  ```text
  📸 [LECTURA OCR COMPLETADA]
  • Código extraído: $contact.ultimo_codigo_envio
  • Tipo de documento: Recibo de remesa / Identificación detectada.
  ```

---

### ⭐️ 14. Agente Encuestas CSAT (`@AgenteCSAT`) - ID: `{{@ai-agent.1130620}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "AgenteCSAT"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Si la calificación es 1 a 3 (Inconformidad): Asesores Servicio al Cliente ({{@team.43621}})
  * Si el cliente desea nueva consulta: @Max ({{@ai-agent.1130619}})
  ```
* **Cerrar conversaciones:**
  ```text
  - Si el cliente califica y se entrega el script SC.036, cerrar conversación inmediatamente.
  ```
* **Actualizar campos de contacto:**
  ```text
  - rating_csat: Calificación otorgada (1 al 5).
  ```
* **Añadir comentarios:**
  ```text
  ⭐ [RESULTADO ENCUESTA CSAT]
  • Calificación: $message.text de 5 estrellas.
  ```

---

### ⚙️ 15. Agente Generador (`@AgenteGenerador`) - ID: `{{@ai-agent.1130621}}`

* **HTTP Request (`interactuar_con_orbit`):**
  ```json
  {"user_text": "$message.text", "contact_id": "$contact.id", "metadata": {"agent_name": "AgenteGenerador"}}
  ```
* **Asignar a agente o equipo:**
  ```text
  * Si requiere validación notarial humana: Asesores Servicio al Cliente ({{@team.43621}})
  ```
* **Cerrar conversaciones:**
  ```text
  - Cierra la conversación tras emitir el folio digital y comprobante.
  ```
* **Actualizar campos de contacto:**
  ```text
  - ultimo_codigo_envio: Folio digital generado.
  ```
* **Añadir comentarios:**
  ```text
  🎫 [EMISIÓN DE FOLIO DIGITAL COMPLETADA]
  • Folio: $contact.ultimo_codigo_envio | Estatus: Registrado exitosamente.
  ```
