# 🛡️ Protocolo de Clasificación Operativa: BSA Monitoring vs. Prevención de Fraudes (v2.0 - Agosto 2026)

## 📌 OBJETIVO
Distinguir con absoluta precisión entre casos que deben ser derivados a **BSA Monitoring (Cumplimiento)** y casos que deben ser derivados a **Prevención de Fraudes**, evitando derivaciones erróneas provocadas por palabras ambiguas como *"fraude"*, *"sospechoso"*, *"estafa"* o *"robo"*.

---

## 1. REGLA PRINCIPAL DE CLASIFICACIÓN
Antes de derivar o activar una ruta en ORBIT o Respond.io, determine qué está reportando realmente el usuario:

* 🔵 **BSA Monitoring (Cumplimiento):** Existe una conducta, patrón, operación, estructura de giros o situación que resulta **inusual, sospechosa o violatoria de normativas de prevención de lavado de dinero**, pero **NO existe una estafa o robo de dinero concretado a un cliente**.
* 🔴 **Prevención de Fraudes:** Existe un evento de **fraude, estafa o engaño concretado** donde el cliente fue víctima, o el cliente reporta una transacción, envío o actividad que **afirma no haber realizado** (suplantación / uso no autorizado de perfil).

---

## 2. CASOS DE BSA MONITORING (CUMPLIMIENTO)
Derive a **BSA Monitoring** cuando el motivo principal sea:
1. **Actividad Transaccional Inusual:** Envíos frecuentes, por montos elevados o sin justificación económica clara.
2. **Estructuración / Evasión de CTR (> $10,000 USD):** Cliente o agente que intenta fraccionar giros o se niega a presentar identificación / SSN requerida por BSA (`RNE.50`).
3. **Uso de Terceros:** Remitente que utiliza a familiares o terceros para realizar operaciones superando límites permitidos.
4. **Solicitudes de Agentes / Sucursales:** Agente que solicita bloquear o incluir a un cliente en la **Deny List** por patrones inusuales o incumplimiento de procedimientos.
5. **Estatus de Transacción en Retención de Cumplimiento:** Transacción en estado `VERIFY HOLD (KYC)` o `GATEWAY INFO REQUIRED` (`COL.04`).

---

## 3. CASOS DE PREVENCIÓN DE FRAUDES
Derive a **Prevención de Fraudes** cuando exista evidencia o reporte de un evento de fraude concretado:
1. **Transacción No Reconocida:** El cliente afirma que no realizó un envío que aparece asociado a su celular o perfil.
2. **Víctima de Estafa Externa:** El cliente fue engañado telefónicamente o por redes para depositar dinero a un estafador (falso soporte Maxi, secuestro virtual, etc.).
3. **Robo / Suplantación de Identidad:** Alguien utilizó la cuenta o datos del cliente sin su conocimiento ni autorización.
4. **Notificación Sospechosa:** El cliente recibe confirmaciones de envíos que él nunca solicitó.

---

## 4. REGLA DE PRIORIDAD Y PALABRAS CLAVE
⚠️ **NO CLASIFICAR ÚNICAMENTE POR PALABRAS CLAVE ISOLADAS.**
Palabras como *"fraude"*, *"sospechoso"* o *"estafa"* pueden aparecer en ambos escenarios.

| Expresión del Usuario / Agente | Análisis de Contexto | Clasificación Correcta |
| :--- | :--- | :--- |
| *"Quiero reportar una actividad sospechosa porque una clienta hace 5 envíos diarios de $2,000 USD."* | Patrón transaccional / Estructuración BSA. No hay estafa a una víctima. | 🔵 **BSA Monitoring** |
| *"Quiero reportar una actividad sospechosa porque me llegó un cargo de un envío que yo no hice."* | Transacción no autorizada / Víctima. | 🔴 **Prevención de Fraudes** |
| *"Un cliente se negó a dar su ID para el reporte de $10,000 dólares."* | Evasión de reporte CTR BSA. | 🔵 **BSA Monitoring** |
| *"Deposité $500 dólares a una cuenta porque me dijeron que gané un premio de Maxi."* | Estafa concretada / Víctima de fraude. | 🔴 **Prevención de Fraudes** |

---

## 5. PROTOCOLO DE RESPUESTA Y FLUJO TÉCNICO (ACTUALIZADO CON RNE.50 / RNE.51)

Una vez determinada la clasificación, ORBIT / Respond.io ejecuta la ruta correspondiente:

### 🔴 Ruta A: Prevención de Fraudes
1. **Turno 1:**
   * Se entrega script **`CU.A1`** (Bienvenida/Privacidad) + **`SC.030.1`** (Horario) o **`SC.030.2`** (Fuera de horario).
   * Se solicitan los 3 datos clave: **Folio de transacción, Nombre completo y Monto depositado**.
   * Se dispara la alerta crítica inmediata a **Freshdesk** y **Google Chat**.
2. **Turno 2 (Recolección de datos o Timeout 3 min):**
   * **En Horario Hábil de Fraudes (`RNE.50` / `RNE.60` / `RNE.61`):** Se entrega el script de cierre **`SC.037`** (con datos) o **`SC.037.1`** (sin datos) y la conversación se **CIERRA AUTOMÁTICAMENTE (`derivacion = "cerrar"`)** en Respond.io, ya que el equipo de Fraudes contacta por canal oficial externo.
   * **Fuera de Horario Hábil de Fraudes (`RNE.51`):** Se entrega **`SC.037`** / **`SC.037.1`** y se asigna a **`Servicio al Cliente`** para ser atendido a primera hora cuando abra el canal de WhatsApp.

### 🔵 Ruta B: BSA Monitoring (Cumplimiento)
1. **Consultas de Transacción (`COL.04` - `VERIFY HOLD KYC` / `GATEWAY INFO`):**
   * En horario hábil: Se entrega script **`SC.011.1`** y se asigna a `derivacion = "Cumplimiento"`.
   * Fuera de horario: Se notifica al cliente que el área de Cumplimiento no está disponible y se canaliza el caso.
2. **Reportes de Sucursal / Evasión CTR / Deny List (`RNE.50`):**
   * Se genera la Alerta Interna de Cumplimiento BSA a Google Chat (`spaces/AAQAQM9pDpg`).
   * En horario hábil: Se confirma recepción con script oficial y se aplica **`derivacion = "cerrar"`** para evitar saturar las colas de asesores humanos de Servicio al Cliente en Respond.io.

---
*Documento alineado con el motor de decisiones ORBIT v2.0 y las Reglas de Negocio RNE.50, RNE.51, RNE.60, RNE.61, SC.037 y SC.037.1.*
