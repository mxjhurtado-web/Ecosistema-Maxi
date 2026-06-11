# Manual Técnico: Acción "Make HTTP Requests" en Respond.io AI Agents

Este documento detalla cómo configurar la acción nativa de Respond.io **`Make HTTP requests`** para conectar los **AI Agents especializados** directamente con la API de **ORBIT Middleware** sin necesidad de cerrar conversaciones ni salir de la sesión de IA.

---

## ⚡ ¿Cómo funciona esta Acción?

Cuando configuras una acción HTTP en un AI Agent de Respond.io:
1. **Detección de Intención:** El agente analiza el mensaje del cliente e identifica si coincide con la descripción de la acción (por ejemplo, *consultar estatus*).
2. **Recopilación de Variables (Inputs):** Si definiste variables obligatorias (como `$agent.codigo_envio`), el agente de forma autónoma le preguntará al usuario hasta que proporcione el valor en el formato correcto.
3. **Petición HTTP:** Una vez tiene todos los datos, realiza la llamada `POST` a ORBIT Middleware.
4. **Respuesta Inteligente:** El agente recibe la respuesta JSON del servidor, la interpreta contextualmente y le responde al cliente con un tono natural y fluido en español.

---

## 🛠️ Configuración Paso a Paso en Respond.io

En la interfaz de edición de tu AI Agent (por ejemplo, en `@VerificadorEstatus`):

### 1. Activar la Acción
* Busca la sección **Actions** (Acciones).
* Activa el interruptor **Make HTTP requests** (Realizar peticiones HTTP).
* Haz clic en **Add Action** (Añadir Acción).

---

### 2. Configurar la Activación de la Acción
* **Action Name (Nombre de la Acción):** `ConsultarEstatusEnvio`
* **¿Cuándo y cómo debe realizarse esta acción? (Prompt de Activación):**
  > *Use this action to retrieve the shipping status of a package or transaction when the customer asks for their status or provides a transaction code starting with CE. If the API returns an error, tell the customer politely that the transaction details could not be retrieved.*

---

### 3. Información que el Agente IA necesita (Inputs)
Esta sección define las variables que el bot debe recopilar obligatoriamente antes de hacer la llamada a la API:

* Haz clic en **+ Add parameter** (Añadir parámetro) y configúralo así:
  * **Name (Nombre):** `codigo_envio`
  * **Format (Formato):** `Text`
  * **Description (Descripción):** *El código de envío que empieza con las letras CE seguido de un número de 8 o más dígitos (ej. CE12345678).*

---

### 4. Configuración de la API (API Configuration)
Aquí indicamos los detalles de la petición hacia el servidor de ORBIT Middleware:

* **Method (Método):** `POST`
* **URL:** `https://orbit-api-xnyd.onrender.com/webhook`  
  *(Asegúrate de colocar la URL de tu API de ORBIT activa en Render)*
* **Headers (Cabeceras):**
  * `Content-Type`: `application/json`
  * `X-Webhook-Secret`: Pega aquí el valor de tu `WEBHOOK_SECRET` configurado en el archivo `.env` de producción.
* **JSON Body (Cuerpo de la Petición):**
  *(Copia y pega exactamente este JSON. Fíjate cómo pasamos el nombre del agente en la metadata para saltarnos el orquestador principal y consultar la base de datos de estatus de forma directa)*:

```json
{
  "conversation_id": "$contact.id",
  "contact_id": "$contact.id",
  "channel": "$contact.channel",
  "user_text": "$agent.codigo_envio",
  "metadata": {
    "agent_name": "VerificadorEstatus"
  }
}
```

---

## 💡 Manejo de Respuestas por la IA (Interpretar JSON)

Una vez que la API responde con la respuesta de ORBIT:
```json
{
  "status": "ok",
  "reply_text": "📦 *Estatus de Envío:* Su transacción CE100200300 se encuentra en tránsito y estará lista para cobro el día de mañana."
}
```
El AI Agent de Respond.io lee automáticamente el contenido de `"reply_text"` y se lo explica de manera natural al cliente, por ejemplo:
> *"¡Buenas noticias! He consultado en nuestro sistema y tu envío con código CE100200300 se encuentra actualmente en tránsito. Estará listo para que sea cobrado a partir del día de mañana."*

---

## 🧪 Cómo Probar la Acción HTTP

Antes de publicar el agente, utiliza el panel lateral **Test AI Agent** en Respond.io:
1. Escribe: *"¿Cómo va mi envío?"*.
2. El bot debe responder solicitando el código: *"Por favor, compárteme tu código de envío que empieza con CE..."*.
3. Escribe un código de prueba (ej. `CE12345678`).
4. Verás una notificación en el panel de pruebas: `VerificadorEstatus executed ConsultarEstatusEnvio`.
5. Si la llamada es exitosa (código HTTP `2xx`), el bot te dará la respuesta del estatus de forma conversacional.
6. Si haces clic sobre la notificación, podrás ver el **Request** (cURL) enviado y el **Response** (JSON) retornado por ORBIT para depurar posibles errores.

---

## 💬 5. Configuración de la Acción "NotificarGoogleChat"

Si deseas configurar un agente (o una acción dentro de tus agentes existentes) para enviar alertas automáticas y estructuradas a Google Chat:

### A. Configurar la Acción en Respond.io
* **Action Name (Nombre de la Acción):** `NotificarGoogleChat`
* **¿Cuándo y cómo debe realizarse esta acción? (Prompt de Activación):**
  > *Use this action to send a notification or alert to Google Chat when a critical issue, dispute, scam/fraud, or specific warning is identified that requires manual follow-up in the support channel.*

### B. Inputs Requeridos (Variables)
1. **`mensaje_notificacion`** (Format: `Text`): *El mensaje detallado de la alerta a enviar a la sala.*
2. **`nivel_alerta`** (Format: `Text`): *El nivel de severidad de la alerta (Opciones: INFO, SUCCESS, WARNING, ERROR).*
3. **`destino`** (Format: `Text` - Opcional): *El canal/destino deseado (Opciones: alertas, soporte, ventas).*

### C. Configuración de la API (API Configuration)
* **Method (Método):** `POST`
* **URL:** `https://orbit-api-ewov.onrender.com/google-chat/notify`
* **Headers (Cabeceras):**
  * `Content-Type`: `application/json`
  * `X-Webhook-Secret`: `maxi-secret-2025`
* **JSON Body:**
```json
{
  "message": "$agent.mensaje_notificacion",
  "level": "$agent.nivel_alerta",
  "destino": "$agent.destino"
}
```

*(Nota: Si deseas enviar a un espacio directo de Google Chat sobreescribiendo el destino por defecto, puedes añadir la variable opcional `space_id` en el cuerpo como `"space_id": "$agent.space_id"`)*.

