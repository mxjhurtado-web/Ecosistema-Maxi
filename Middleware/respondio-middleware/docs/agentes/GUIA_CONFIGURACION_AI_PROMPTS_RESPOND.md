# Guía Técnica de Configuración: AI Prompts para Asesores Humanos en Respond.io (Workspace Settings)

Esta guía detalla paso a paso cómo configurar los **AI Prompts de 1 Clic** en la plataforma Respond.io para los equipos de asesores humanos (`Servicio al Cliente`, `Cancelación Money Order`, `Modificación de Datos`, `Historial de Envíos`, `Fraudes`, `BSA`) cuando atienden conversaciones asignadas dentro del Inbox de Respond.io.

---

## 🛠️ Paso a Paso para Configurar en Respond.io

1. Inicia sesión en **Respond.io** con tu cuenta de Administrador.
2. En el menú lateral izquierdo, ve a **Settings ⚙️ (Ajustes)** ➔ **Workspace Settings (Ajustes de Espacio de Trabajo)**.
3. Haz clic en la pestaña **AI Prompts** (Prompts de Inteligencia Artificial).
4. Haz clic en el botón azul **+ Add Prompt** (Añadir Prompt).
5. Configura cada una de las 3 plantillas oficiales que se muestran a continuación.

---

## 📋 Las 3 Plantillas Oficiales de 1 Clic para Asesores Humanos

### 1️⃣ AI Prompt: "Resumen de Caso para Asesor" (Comando `/resumen`)

* **Prompt Name:** `Resumen de Caso para Asesor`
* **Shortcut (Atajo):** `/resumen`
* **Icon / Icono:** 📝 Resumen
* **Prompt Instruction (Copiar y Pegar exactamente):**
  ```text
  Analiza toda la conversación previa entre el cliente y los agentes virtuales (@Max / especialistas). Genera un resumen ejecutivo de 3 viñetas para el asesor humano que incluya:
  1. Clave o folio de transacción detectado (o N/A si no proporcionó).
  2. Motivo exacto por el cual fue transferido a un asesor humano.
  3. Idioma detectado del cliente y estado de su solicitud.
  ```

---

### 2️⃣ AI Prompt: "Traducir al Idioma del Cliente" (Comando `/traducir`)

* **Prompt Name:** `Traducir al Idioma del Cliente`
* **Shortcut (Atajo):** `/traducir`
* **Icon / Icono:** 🌐 Traducción
* **Prompt Instruction (Copiar y Pegar exactamente):**
  ```text
  Toma el borrador de respuesta redactado por el asesor humano en español y tradúcelo con total fidelidad y elegancia al idioma en el que el cliente está escribiendo (Inglés, Portugués, etc.).
  REGLAS:
  - Mantén intactos sin traducir los nombres propios de personas, códigos de envío (CE... / TRK...) y montos numéricos.
  - Dirígete al usuario manteniendo el tratamiento formal de "Usted".
  ```

---

### 3️⃣ AI Prompt: "Formatear a Tono Oficial Maxi" (Comando `/formalizar`)

* **Prompt Name:** `Formatear a Tono Oficial Maxi`
* **Shortcut (Atajo):** `/formalizar`
* **Icon / Icono:** 👔 Tono Oficial
* **Prompt Instruction (Copiar y Pegar exactamente):**
  ```text
  Reescribe el mensaje borrador del asesor humano ajustándolo al tono de comunicación institucional de Maxitransfers:
  - Tono altamente profesional, empático y formal (tratamiento de "Usted").
  - Corrige errores de ortografía o puntuación.
  - Conserva íntegramente las instrucciones técnicas, folios o números de teléfono brindados por el asesor.
  ```

---

## 💡 ¿Cómo lo utiliza el Asesor Humano en el Inbox de Respond.io?

Cuando un asesor humano abre una conversación asignada a su cola en el Inbox de Respond.io:
1. Hace clic en el **botón de AI Prompts ✨** situado en la barra de herramientas del chat (o escribe el atajo `/resumen`, `/traducir` o `/formalizar`).
2. Al seleccionar `/resumen`, Respond.io analiza todo el chat de `@Max` y le muestra al asesor el resumen ejecutivo instantáneo de 3 puntos.
3. Al escribir un borrador en español y seleccionar `/traducir`, Respond.io traduce la respuesta al idioma del cliente antes de enviarla.
