# Guía Técnica de Configuración: AI Prompts para Asesores Humanos en Respond.io (Ajustados a Límites Exactos de la UI)

Esta guía detalla los textos exactos para configurar la opción **Añadir solicitud de IA / Nuevo mensaje** en **Workspace Settings ➔ AI Prompts / AI Assist** en Respond.io, ajustados a las restricciones de la interfaz:
* **Nombre del mensaje:** Máximo **20 caracteres**.
* **Acción de mensaje:** Máximo **300 caracteres**.

---

## 📋 Las 3 Plantillas Ajustadas para Copiar y Pegar

### 1️⃣ Plantilla 1: Resumen de Caso
* **Nombre del mensaje:** `Resumen de Caso` (15 caracteres - ✅ OK)
* **Acción de mensaje:** (241 caracteres - ✅ OK)
  ```text
  Analiza la conversación previa entre el cliente y los agentes virtuales. Genera un resumen ejecutivo breve de 3 puntos: 1. Clave o folio detectado (o N/A), 2. Motivo exacto de transferencia al asesor, 3. Idioma detectado del cliente.
  ```

---

### 2️⃣ Plantilla 2: Traducir al Cliente
* **Nombre del mensaje:** `Traducir al Cliente` (19 caracteres - ✅ OK)
* **Acción de mensaje:** (221 caracteres - ✅ OK)
  ```text
  Traduce el borrador del asesor en español al idioma en el que escribe el cliente. Mantén intactos sin traducir los códigos de envío (CE... / TRK...), folios y montos numéricos. Usa siempre el trato formal de Usted.
  ```

---

### 3️⃣ Plantilla 3: Tono Oficial Maxi
* **Nombre del mensaje:** `Tono Oficial Maxi` (17 caracteres - ✅ OK)
* **Acción de mensaje:** (205 caracteres - ✅ OK)
  ```text
  Reescribe el borrador del asesor al tono oficial de Maxitransfers: altamente profesional, empático y formal (trato de Usted). Corrige ortografía manteniendo intactos folios, claves y datos técnicos.
  ```
