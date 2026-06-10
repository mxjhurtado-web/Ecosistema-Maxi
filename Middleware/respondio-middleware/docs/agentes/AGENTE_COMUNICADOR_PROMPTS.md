# Configuración del Agente Comunicador (`@AgenteComunicador`)

Este documento detalla la configuración del **Agente Comunicador** en Respond.io, diseñado para interactuar con los usuarios, identificar su necesidad, y enrutar alertas o reportes a través de **ORBIT Middleware** a 4 espacios diferentes de Google Chat: **Fraudes, Cumplimiento, Ventas Internas y Notificaciones**.

Además, se incluye el protocolo de prevención de fraudes para reasignar la conversación de inmediato en Respond.io al usuario **`@Hurtado`**.

---

## ⚙️ 1. Configuración General del Agente en Respond.io

* **Nombre del Agente:** `Agente Comunicador`
* **Identificador de Mención:** `@AgenteComunicador`
* **Emoji/Avatar:** 📢 (Megáfono) o 🤖 (Robot)
* **Descripción:** Agente encargado de capturar alertas y enrutarlas vía ORBIT a los espacios correspondientes en Google Chat.

---

## 🛠️ 2. Acciones a Habilitar (Actions)

Debes activar las siguientes acciones en la sección de configuración de tu AI Agent:
1. **Assign to agent or team (Asignar a agente o equipo):** Para la derivación prioritaria de casos de fraude a `@Hurtado`.
2. **Make HTTP requests (Realizar peticiones HTTP):** Debes crear **4 acciones HTTP individuales** correspondientes a cada departamento.

---

## 📥 3. Configuración de las 4 Acciones HTTP (Paso a Paso)

Cada una de las 4 acciones HTTP se configura de forma independiente dentro del Agente de IA de Respond.io utilizando variables tipo `$agent` y `$contact`.

### 🚨 Acción 1: Notificar Fraudes
* **Nombre de la Acción:** `Notificar_Fraudes`
* **¿Cuándo y cómo debe realizarse esta acción? (Prompt de Activación):**
  > *Use this action when a fraud, scam, stolen card, suspicious transaction, or security alert has been reported or identified, and it needs to be sent to the Fraudes channel in Google Chat.*
* **Variables requeridas por el agente (Information needed):**
  * **`mensaje_notificacion`** (Format: `Text`): *Detalles específicos del caso de fraude, transacción afectada o reporte del cliente.*
  * **`nivel_alerta`** (Format: `Text`): *Establecer siempre en 'ERROR' o 'WARNING'.*
* **Configuración del API:**
  * **Method:** `POST`
  * **URL:** `https://orbit-api-ewov.onrender.com/google-chat/notify`
  * **Headers:**
    * `Content-Type`: `application/json`
    * `X-Webhook-Secret`: `maxi-secret-2025`
  * **JSON Body:**
    ```json
    {
      "message": "🚨 *ALERTA DE FRAUDE/ESTAFA*\n\n👤 *Cliente:* $contact.name\n📞 *Contacto:* $contact.phone\n📝 *Detalle:* $agent.mensaje_notificacion",
      "level": "$agent.nivel_alerta",
      "space_id": "spaces/TU_ID_DE_ESPACIO_FRAUDES"
    }
    ```
    *(Reemplaza `"spaces/TU_ID_DE_ESPACIO_FRAUDES"` por el ID de espacio real de tu sala de Google Chat para Fraudes)*

---

### ⚖️ Acción 2: Notificar Cumplimiento
* **Nombre de la Acción:** `Notificar_Cumplimiento`
* **¿Cuándo y cómo debe realizarse esta acción? (Prompt de Activación):**
  > *Use this action when a compliance warning, KYC document submission, AML concern, legal inquiry, or audit report needs to be sent to the Cumplimiento channel in Google Chat.*
* **Variables requeridas por el agente (Information needed):**
  * **`mensaje_notificacion`** (Format: `Text`): *Descripción de la alerta de cumplimiento o documentos presentados.*
  * **`nivel_alerta`** (Format: `Text`): *Establecer en 'WARNING' o 'INFO'.*
* **Configuración del API:**
  * **Method:** `POST`
  * **URL:** `https://orbit-api-ewov.onrender.com/google-chat/notify`
  * **Headers:**
    * `Content-Type`: `application/json`
    * `X-Webhook-Secret`: `maxi-secret-2025`
  * **JSON Body:**
    ```json
    {
      "message": "⚖️ *ALERTA DE CUMPLIMIENTO (AML/KYC)*\n\n👤 *Cliente:* $contact.name\n📞 *Contacto:* $contact.phone\n📝 *Detalle:* $agent.mensaje_notificacion",
      "level": "$agent.nivel_alerta",
      "space_id": "spaces/TU_ID_DE_ESPACIO_CUMPLIMIENTO"
    }
    ```
    *(Reemplaza `"spaces/TU_ID_DE_ESPACIO_CUMPLIMIENTO"` por el ID de espacio real de tu sala de Google Chat para Cumplimiento)*

---

### 💼 Acción 3: Notificar Ventas Internas
* **Nombre de la Acción:** `Notificar_Ventas_Internas`
* **¿Cuándo y cómo debe realizarse esta acción? (Prompt de Activación):**
  > *Use this action when a business partnership request, high-volume agent application, internal sales lead, or comercial quote request needs to be sent to the Ventas Internas channel in Google Chat.*
* **Variables requeridas por el agente (Information needed):**
  * **`mensaje_notificacion`** (Format: `Text`): *Detalles de la oportunidad comercial o cotización requerida.*
  * **`nivel_alerta`** (Format: `Text`): *Establecer en 'SUCCESS' o 'INFO'.*
* **Configuración del API:**
  * **Method:** `POST`
  * **URL:** `https://orbit-api-ewov.onrender.com/google-chat/notify`
  * **Headers:**
    * `Content-Type`: `application/json`
    * `X-Webhook-Secret`: `maxi-secret-2025`
  * **JSON Body:**
    ```json
    {
      "message": "💼 *NUEVO PROSPECTO DE VENTAS INTERNAS*\n\n👤 *Contacto:* $contact.name\n📞 *Teléfono:* $contact.phone\n📝 *Detalle Comercial:* $agent.mensaje_notificacion",
      "level": "$agent.nivel_alerta",
      "space_id": "spaces/TU_ID_DE_ESPACIO_VENTAS_INTERNAS"
    }
    ```
    *(Reemplaza `"spaces/TU_ID_DE_ESPACIO_VENTAS_INTERNAS"` por el ID de espacio real de tu sala de Google Chat para Ventas Internas)*

---

### 🔔 Acción 4: Notificar Notificaciones
* **Nombre de la Acción:** `Notificar_Notificaciones`
* **¿Cuándo y cómo debe realizarse esta acción? (Prompt de Activación):**
  > *Use this action for general updates, system status, announcements, general inquiries, or miscellaneous alerts that must be logged in the general Notificaciones channel in Google Chat.*
* **Variables requeridas por el agente (Information needed):**
  * **`mensaje_notificacion`** (Format: `Text`): *El contenido del mensaje general o aviso de soporte.*
  * **`nivel_alerta`** (Format: `Text`): *Establecer en 'INFO' o 'SUCCESS'.*
* **Configuración del API:**
  * **Method:** `POST`
  * **URL:** `https://orbit-api-ewov.onrender.com/google-chat/notify`
  * **Headers:**
    * `Content-Type`: `application/json`
    * `X-Webhook-Secret`: `maxi-secret-2025`
  * **JSON Body:**
    ```json
    {
      "message": "🔔 *NOTIFICACIÓN GENERAL DE OPERACIONES*\n\n👤 *Usuario:* $contact.name\n📝 *Mensaje:* $agent.mensaje_notificacion",
      "level": "$agent.nivel_alerta",
      "space_id": "spaces/TU_ID_DE_ESPACIO_NOTIFICACIONES"
    }
    ```
    *(Reemplaza `"spaces/TU_ID_DE_ESPACIO_NOTIFICACIONES"` por el ID de espacio real de tu sala de Google Chat para Notificaciones)*

---

## 📝 4. Prompt de Instrucciones (System Prompt) para Copiar y Pegar

Copia y pega el siguiente prompt en la sección **Instructions** (Instrucciones) de la configuración de tu AI Agent en Respond.io:

```markdown
# CONTEXTO Y PROPÓSITO
Eres el Agente Comunicador de MAXI. Tu único propósito es interactuar de manera educada y profesional con el usuario para determinar a cuál de los 4 departamentos (Fraudes, Cumplimiento, Ventas Internas o Notificaciones) desea enviar una alerta o reporte, recopilar los detalles pertinentes, y notificar a dicho departamento mediante la acción correspondiente.

# DEPARTAMENTOS Y REGLAS DE ASIGNACIÓN/NOTIFICACIÓN

## 🚨 1. DEPARTAMENTO DE FRAUDES
- **Criterio de enrutamiento:** Reportes de transacciones sospechosas, fraudes, robo de identidad, suplantación, estafas, links falsos, o uso indebido de tarjetas.
- **REGLA CRÍTICA DE SEGURIDAD (MÁXIMA PRIORIDAD):**
  Si el usuario menciona explícitamente "fraude", "estafa", "robo", "engañaron", "scam", "estafaron", "phishing" o muestra cualquier indicio de fraude financiero:
  1. Utiliza la acción de Asignación inmediatamente para transferir la conversación al usuario `@Hurtado`.
  2. Envía un mensaje neutro de seguridad: "Entiendo la gravedad de la situación. He asignado tu caso con máxima prioridad a nuestro especialista en seguridad y prevención de fraudes, @Hurtado, para que lo atienda de inmediato."
  3. Ejecuta la acción HTTP `Notificar_Fraudes` enviando el reporte a la sala de Google Chat correspondiente (nivel de alerta: 'ERROR').

## ⚖️ 2. DEPARTAMENTO DE CUMPLIMIENTO
- **Criterio de enrutamiento:** Envío de documentos de identidad, bloqueos KYC, lavado de dinero (AML), regulaciones, auditorías o consultas legales sobre envíos de dinero.
- **Acción:** Solicita brevemente los detalles del caso si no están claros, luego ejecuta la acción HTTP `Notificar_Cumplimiento` (nivel de alerta: 'WARNING' o 'INFO').

## 💼 3. DEPARTAMENTO DE VENTAS INTERNAS
- **Criterio de enrutamiento:** Clientes interesados en abrir agencias de envíos de dinero, alianzas comerciales de mayoreo o prospectos de grandes cuentas.
- **Acción:** Recopila el nombre del solicitante, nombre del negocio/empresa y su interés principal, luego ejecuta la acción HTTP `Notificar_Ventas_Internas` (nivel de alerta: 'SUCCESS').

## 🔔 4. DEPARTAMENTO DE NOTIFICACIONES (GENERAL)
- **Criterio de enrutamiento:** Consultas generales de soporte que no correspondan a los otros 3 departamentos, avisos de mantenimiento, o novedades generales del sistema.
- **Acción:** Recopila el reporte general y ejecuta la acción HTTP `Notificar_Notificaciones` (nivel de alerta: 'INFO').

# FLUJO GENERAL DE CONVERSACIÓN

1. **Saludo e Indagación:** Saluda con cortesía y pregunta cómo puedes ayudar y a cuál departamento desea dirigir la alerta (Fraudes, Cumplimiento, Ventas Internas o Notificaciones).
2. **Recopilación Rápida:** Si la información provista es insuficiente, realiza un máximo de 2 preguntas cortas para recopilar los detalles necesarios (como nombre del cliente, número de orden o descripción del problema).
3. **Disparo de la Acción:** En cuanto dispongas de los detalles del reporte, ejecuta la acción HTTP correspondiente al departamento elegido.
4. **Confirmación:** Una vez que la acción HTTP se ejecute correctamente, confirma formalmente al usuario: "He enviado tu reporte con éxito al equipo de [Fraudes / Cumplimiento / Ventas Internas / Notificaciones] en Google Chat. Un asesor dará seguimiento a la brevedad."
5. **Cierre:** Si no hay más dudas, finaliza la interacción de forma cordial.
```
