# 🛡️ ANEXO RNE.62: PROTOCOLO DE DESAMBIGUACIÓN OPERATIVA BSA MONITORING VS. PREVENCIÓN DE FRAUDES

## 📌 OBJETIVO Y ALCANCE
Establecer el criterio oficial e inequívoco para la desambiguación de intenciones entre **BSA Monitoring (Cumplimiento)** y **Prevención de Fraudes**, complementando las hojas de cálculo y documentos de Reglas de Negocio, Reglas Generales y Scripts del Ecosistema Maxi.

---

## 1. CRITERIO CONCEPTUAL DE NEGOCIO

| Criterio | 🔵 BSA Monitoring (Cumplimiento) | 🔴 Prevención de Fraudes |
| :--- | :--- | :--- |
| **Definición** | Reporte de patrones transaccionales inusuales, estructuración de giros, evasión de CTR o solicitudes de sucursal. | Reporte de un evento de estafa/fraude concretado donde el cliente fue víctima o le sustrajeron dinero. |
| **Afectación** | NO existe un robo directos reportado por la víctima. Existe un riesgo/incumplimiento normativo. | SÍ existe una transacción no autorizada o un engaño donde el cliente perdió/entregó dinero. |
| **Iniciador** | Agentes de sucursal, personal interno o sistemas de alerta automática. | Cliente/Remitente (víctima) o familiar directo. |
| **Acción ORBIT** | Alerta a Google Chat BSA + `derivacion = "cerrar"` (en horario) o ruteo a Cumplimiento. | Alerta Crítica Fraudes + Recaudación de 3 datos + `SC.037` + `derivacion = "cerrar"` (RNE.50/60). |

---

## 2. REGLA DE DESAMBIGUACIÓN DE PALABRAS CLAVE

⚠️ **ATENCIÓN:** La presencia de palabras como *"sospechoso"*, *"fraude"* o *"reporte"* no determina por sí sola la ruta. Debe analizarse la naturaleza del hecho:

1. Si el usuario reporta **fraccionamiento de envíos, envíos acumulados sin ID, negativa a presentar SSN/CTR, o solicitud de Deny List**:
   👉 **Clasificación:** 🔵 **BSA Monitoring (`@DerivacionBSA`)**
2. Si el usuario reporta **haber depositado a un falso soporte de Maxi, secuestro virtual, haber recibido notificación de un giro no hecho, o cobro no reconocido**:
   👉 **Clasificación:** 🔴 **Prevención de Fraudes (`RNE.50 / RNE.51`)**

---

## 3. MATRIZ DE RESPUESTA OPERATIVA EN ORBIT Y RESPOND.IO

| Escenario | Horario Laboral | Derivación Respond.io | Script Entregado | Canal de Alerta Notificado |
| :--- | :--- | :--- | :--- | :--- |
| **Fraude con Datos** | Hábil (`RNE.50/60`) | `cerrar` | `SC.037` | Google Chat + Freshdesk |
| **Fraude sin Datos / Timeout** | Hábil (`RNE.50/61`) | `cerrar` | `SC.037.1` | Google Chat + Freshdesk |
| **Fraude Fuera de Horario** | Inhábil (`RNE.51`) | `Servicio al Cliente` | `SC.037` / `SC.037.1` | Google Chat |
| **BSA Evasión CTR / Deny List** | Hábil (`RNE.50`) | `cerrar` | `SC.037` / `SC.011.1` | Google Chat BSA Space |
| **BSA Estatus VERIFY HOLD** | Hábil (`COL.04`) | `Cumplimiento` | `SC.011.1` | Google Chat BSA Space |

---
*Anexo oficial RNE.62 del Ecosistema Maxi - Compatible con ORBIT v2.0.*
