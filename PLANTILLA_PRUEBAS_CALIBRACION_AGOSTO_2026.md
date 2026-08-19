# 📋 PLANTILLA MAESTRA DE PRUEBAS DE CALIBRACIÓN Y AUDITORÍA E2E
**Ecosistema Max + ORBIT Middleware v4.7 (Agosto 2026)**  
**Estructura:** 60 Casos de Prueba Totales (30 Casos Generales + 30 Casos Enfocados en los Nuevos Cambios de Procesos)

---

## 📌 Guía de Evaluación para el Probador

Cada evaluador o probador (QA / Procesos) debe ejecutar secuencialmente los 60 casos de prueba en WhatsApp / Respond.io, marcando el estatus **PASS (Aprobado)** o **FAIL (Fallido)** y anotando las observaciones correspondientes.

---

## 🟢 BLOQUE A: 30 CASOS DE PRUEBA GENERALES (SALUD Y COBERTURA OPERATIVA)

| ID | Módulo / Categoría | Entrada / Acción del Usuario | Resultado Esperado (ORBIT Middleware) | Estatus QA | Observaciones / Evidencia |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **101** | **General** - Saludo CU.A1 | `'Hola buenos días'` | Disparo de `CU.A1` obligatorio en Turno 1 con Aviso de Privacidad. | ☐ PASS<br>☐ FAIL | Turno 1 antepone CU.A1. Turno 2+ no repite. |
| **102** | **General** - Remesa Paid | Consulta clave con estatus Paid (ej. `40001`) | Entregar script `SC.014` (Dinero cobrado exitosamente). | ☐ PASS<br>☐ FAIL | Indicar fecha y sucursal. |
| **103** | **General** - Remesa Unpaid | Consulta clave con estatus Unpaid (ej. `40002`) | Entregar script `SC.015` (Disponible para cobro). | ☐ PASS<br>☐ FAIL | Confirmar vigencia. |
| **104** | **General** - Remesa en Ruta / Proceso | Consulta clave estatus Progress (ej. `40003`) | Entregar script `SC.015.1` o `SC.015.2` según aplique. | ☐ PASS<br>☐ FAIL | Mapear estatus transitorio. |
| **105** | **General** - Remesa Cancelada | Consulta clave estatus Cancelled (ej. `40004`) | Entregar script `SC.017` o `SC.018` e informar opciones. | ☐ PASS<br>☐ FAIL | Reembolso o acudir a agencia. |
| **106** | **General** - Privacidad Beneficiario | Beneficiario consulta estatus Paid | Entregar script `SC.019` (Protección NPI del remitente). | ☐ PASS<br>☐ FAIL | No revelar montos ni remitente. |
| **107** | **General** - Beneficiario en Proceso | Beneficiario consulta estatus Progress | Entregar script `SC.019.1` indicando operación en proceso. | ☐ PASS<br>☐ FAIL | Derivar a SC con `SC.013`. |
| **108** | **General** - Humano Explícito (Asesor) | `'Necesito hablar con un asesor'` | Entregar `SC.013` e iniciar Hand-off a SC (Cola B). | ☐ PASS<br>☐ FAIL | `COL.07` interrumpe flujo inmediatamente. |
| **109** | **General** - Humano Explícito (Persona) | `'Quiero hablar con una persona'` | Entregar `SC.013` e iniciar Hand-off a SC (Cola B). | ☐ PASS<br>☐ FAIL | Término "persona" dispara handoff. |
| **110** | **General** - Bill Payment Paid | Consulta pago de servicio Paid (`TRK...`) | Entregar script `SC.021` (Pago exitoso). | ☐ PASS<br>☐ FAIL | Validar confirmación biller. |
| **111** | **General** - Bill Payment Cancelled | Consulta pago de servicio Cancelled | Entregar script `SC.022` (Pago no procesado). | ☐ PASS<br>☐ FAIL | Ofrecer comunicación con asesor. |
| **112** | **General** - Bill Payment Origin | Consulta pago de servicio Origin | Entregar script `SC.023` y derivar a Servicio al Cliente. | ☐ PASS<br>☐ FAIL | Hand-off obligatorio. |
| **113** | **General** - Recarga Celular Exitosa | Consulta recarga telefónica Paid | Entregar script `SC.024` (Recarga exitosa). | ☐ PASS<br>☐ FAIL | Validar número celular. |
| **114** | **General** - Recarga Celular Fallida | Consulta recarga telefónica Cancelled | Entregar script `SC.025` (Recarga no procesada). | ☐ PASS<br>☐ FAIL | Ofrecer asistencia de asesor. |
| **115** | **General** - Validación Teléfonos Topup | Consulta recarga sin teléfonos | Entregar script `SC.010.2` solicitando ambos números. | ☐ PASS<br>☐ FAIL | Solicitar teléfono cliente y destino. |
| **116** | **General** - Cancelación Money Order | Compartir foto MO con marca VOID | Entregar `SC.024` + `SC.013` y derivar a SC. | ☐ PASS<br>☐ FAIL | RNE.53: Hand-off tras capturar folios. |
| **117** | **General** - Clave No Localizada | Enviar clave inexistente `999999999` | Entregar script `SC.029` solicitando verificar datos. | ☐ PASS<br>☐ FAIL | Permitir reingreso de clave. |
| **118** | **General** - Recibo Térmico/Windows | Solicitar ayuda para ubicar clave | Entregar script `SC.009` (Imagen de recibo). | ☐ PASS<br>☐ FAIL | Respuesta explicativa limpia. |
| **119** | **General** - Exclusión Presencial Sender | Remitente solicita modificación de datos | Entregar script `SC.031` (Atención presencial en agencia). | ☐ PASS<br>☐ FAIL | RNE.44: Bloqueo de cambios por WhatsApp. |
| **120** | **General** - Exclusión Presencial Ben | Beneficiario solicita cambio de datos | Entregar script `SC.031.1` (Pedir al remitente ir a agencia). | ☐ PASS<br>☐ FAIL | RNE.44: Exclusión beneficiario. |
| **121** | **General** - Multilingüismo (Inglés) | `'Hello, good morning'` | Respuesta en inglés con `CU.A1` traducido de forma nativa. | ☐ PASS<br>☐ FAIL | LNG.01: Mantener idioma inglés. |
| **122** | **General** - Control Inactividad | Simular 10 min sin actividad | Disparo de script `SC.032` (Pausa por inactividad). | ☐ PASS<br>☐ FAIL | EVT.05: Registro de pausa. |
| **123** | **General** - Historial Envíos sin Ticket | Solicitar historial sin formato | Entregar script `SC.013` e iniciar levantamiento en SC. | ☐ PASS<br>☐ FAIL | COL.02 Cola B: Récord sin ticket. |
| **124** | **General** - Abono al Balance | Agente consulta abono al balance | Entregar script `SC.003` / `SC.004` de clasificación. | ☐ PASS<br>☐ FAIL | Profiling de Agente. |
| **125** | **General** - Re-verificación Nombres | Ingresar nombre remitente incompleto | Entregar script `SC.006.1` o `SC.007` solicitando confirmación. | ☐ PASS<br>☐ FAIL | Fuzzy matching de nombres. |
| **126** | **General** - Coordinación de Pago | Solicitar detalle de tarifas | Entregar `SC.022` + `SC.013` y derivar a SC. | ☐ PASS<br>☐ FAIL | Derivación limpia a SC. |
| **127** | **General** - Casos Fuera Alcance Sender | Remitente pide investigación pago cash | Entregar script `SC.026` (Teléfono 1-866-216-2852). | ☐ PASS<br>☐ FAIL | Canales directos de seguridad. |
| **128** | **General** - Casos Fuera Alcance Ben | Beneficiario pide investigación cash | Entregar script `SC.026.1` (Pedir al remitente llamar). | ☐ PASS<br>☐ FAIL | Protección NPI. |
| **129** | **General** - Contingencia Horaria SC | Consulta requiriendo SC a las 10 PM | Entregar script `SC.027` (Horarios L-V 9am-9pm). | ☐ PASS<br>☐ FAIL | Mantener ticket en espera activa. |
| **130** | **General** - Restricción Reasignación | Asesor humano interactúa en chat | ORBIT suspende intervenciones automáticas. | ☐ PASS<br>☐ FAIL | COL.03: Prohibida reasignación IA. |

---

## 🔥 BLOQUE B: 30 CASOS DE PRUEBA ENFOCADOS EN LOS NUEVOS CAMBIOS DE PROCESOS

| ID | Módulo / Categoría | Entrada / Acción del Usuario | Resultado Esperado (ORBIT Middleware) | Estatus QA | Observaciones / Evidencia |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **201** | **NUEVO** - Token Defense (550 chars) | Enviar mensaje de 550 caracteres | Intercepción `AIS.05`: Pedir educadamente resumir consulta. | ☐ PASS<br>☐ FAIL | No procesar NLU si excede 500 chars. |
| **202** | **NUEVO** - Token Defense (800 chars) | Enviar mensaje de 800 caracteres | Intercepción `AIS.05`: Pedir educadamente resumir consulta. | ☐ PASS<br>☐ FAIL | Bloqueo perimetral síncrono. |
| **203** | **NUEVO** - Token Defense (Inglés >500) | Enviar mensaje en inglés de 600 chars | Respuesta en inglés pidiendo resumir la consulta. | ☐ PASS<br>☐ FAIL | Language Sync en Token Defense. |
| **204** | **NUEVO** - Límite Loops (1er intento) | Enviar texto incomprensible 1 vez | Entrega `SC.001` pidiendo reingresar información. | ☐ PASS<br>☐ FAIL | Incrementa contador en Redis. |
| **205** | **NUEVO** - Límite Loops (2º intento) | Enviar texto incomprensible 2ª vez | Al 2º intento entrega `SC.002` e inicia Hand-off a Cola B. | ☐ PASS<br>☐ FAIL | AIS.04: Romper bucle en 2. |
| **206** | **NUEVO** - Límite Loops (Imagen borrosa) | Adjuntar 2 veces foto ilegible de ticket | Al 2º intento entrega `SC.002` e inicia Hand-off a Cola B. | ☐ PASS<br>☐ FAIL | Romper bucle en 2 en OCR. |
| **207** | **NUEVO** - Handoff IRS / Oversight | `'Recibí una carta de auditoría del IRS'` | Alerta a Google Chat (`AAQAJiVCDAU`) + `SC.011` + Pase SC. | ☐ PASS<br>☐ FAIL | `SC.011` literal sin paráfrasis. |
| **208** | **NUEVO** - Handoff Hardware POS | Foto POS + `'Se trabó el escáner'` | Alerta a Google Chat (`AAQAQhx5RTM`) + `SC.011` + Pase SC. | ☐ PASS<br>☐ FAIL | Notificación con resumen forense. |
| **209** | **NUEVO** - Handoff Cumplimiento P-4 | `'Solicitud de envío de la Forma P-4'` | Alerta a Google Chat (`AAQAbvCUAko`) + `SC.011` + Pase SC. | ☐ PASS<br>☐ FAIL | `SC.011` literal. |
| **210** | **NUEVO** - Handoff Cobranza | `'Aclaración de saldo por comisión'` | Alerta a Google Chat (`AAQAcEu8NTc`) + `SC.011` + Pase SC. | ☐ PASS<br>☐ FAIL | Registro en audit trail. |
| **211** | **NUEVO** - Handoff Capacitación | `'Consulta sobre el manual del POS'` | Alerta a Google Chat (`AAQAMKgsazw`) + `SC.011` + Pase SC. | ☐ PASS<br>☐ FAIL | Derivación limpia. |
| **212** | **NUEVO** - Handoff Cheques y Nómina | `'Verificación de depósito de cheque'` | Alerta a Google Chat (`AAQAGZ_m434`) + `SC.011` + Pase SC. | ☐ PASS<br>☐ FAIL | Notificación enviada. |
| **213** | **NUEVO** - Handoff Ventas / Agencia | `'Información para registrar agencia'` | Alerta a Google Chat (`AAQAUghCztE`) + `SC.011` + Pase SC. | ☐ PASS<br>☐ FAIL | Lead de ventas enviado. |
| **214** | **NUEVO** - Fraude Horario Laboral | `'Me hablaron pidiéndome mi PIN'` | Alerta a Google Chat (`AAQAQM9pDpg`) + `SC.030.1` + 4 datos. | ☐ PASS<br>☐ FAIL | Alerta roja en Turno 1. |
| **215** | **NUEVO** - Desborde Crítico Seg | `'Reporte de hackeo de acceso POS'` | Alerta a Google Chat + `SC.030.2` + 4 datos. | ☐ PASS<br>☐ FAIL | Hand-off crítico alta prioridad. |
| **216** | **NUEVO** - COL.02 Cola A (Fraude) | Mensaje de fraude enviado fuera de horario | Entrega `SC.027.1` + Asignación prioritaria a **Cola A**. | ☐ PASS<br>☐ FAIL | Asignación en Cola A. |
| **217** | **NUEVO** - COL.02 Cola B (Fallback) | 2 fallbacks de búsqueda en Chronos | Entrega `SC.002` + Asignación a **Cola B** (Estándar). | ☐ PASS<br>☐ FAIL | Asignación a Cola B con resumen. |
| **218** | **NUEVO** - COL.02 Cola B (Petición) | `'Quiero que me atienda un agente'` | Entrega `SC.013` + Asignación a **Cola B** (Estándar). | ☐ PASS<br>☐ FAIL | Derivación a Cola B. |
| **219** | **NUEVO** - Script `SC.009` Limpio | Solicitar ayuda para ubicar clave | Entrega `SC.009` limpio (sin `'Agente de IA enviaría...'`). | ☐ PASS<br>☐ FAIL | Verificar que NO tenga texto bot. |
| **220** | **NUEVO** - Script `SC.033` Limpio | Concluir consulta exitosa | Entrega `SC.033` limpio: `¿Hay algo más en lo que le pueda ayudar?.` | ☐ PASS<br>☐ FAIL | Sin corchetes `[Nombre]`. |
| **221** | **NUEVO** - Script `SC.031.1` Limpio | Beneficiario solicita cambio de datos | Entrega `SC.031.1` limpio con un solo punto final. | ☐ PASS<br>☐ FAIL | Ortografía y puntuación limpia. |
| **222** | **NUEVO** - CSAT Nota 5 (Excelente) | Finalizar ➔ Seleccionar opción `'5'` | Entrega directamente `SC.036` y cierra la sesión. | ☐ PASS<br>☐ FAIL | Sin pedir feedback adicional. |
| **223** | **NUEVO** - CSAT Nota 4 (Buena) | Finalizar ➔ Seleccionar opción `'4'` | Entrega directamente `SC.036` y cierra la sesión. | ☐ PASS<br>☐ FAIL | Sin pedir feedback adicional. |
| **224** | **NUEVO** - CSAT Nota 3 (Regular) | Finalizar ➔ Seleccionar opción `'3'` | Detona obligatoriamente `SC.035` para capturar feedback. | ☐ PASS<br>☐ FAIL | Disparo de `SC.035`. |
| **225** | **NUEVO** - CSAT Nota 2 (Mala) | Finalizar ➔ Seleccionar opción `'2'` | Detona obligatoriamente `SC.035` para capturar motivo. | ☐ PASS<br>☐ FAIL | Registro de insatisfacción. |
| **226** | **NUEVO** - CSAT Nota 1 (Muy Mala) | Finalizar ➔ Seleccionar opción `'1'` | Detona `SC.035` y registra alerta crítica de insatisfacción. | ☐ PASS<br>☐ FAIL | Bitácora CSAT Baja. |
| **227** | **NUEVO** - Opt-Out (`STOP`) | Enviar comando `'STOP'` | Opt-Out inmediato + Bloqueo de outbound saliente. | ☐ PASS<br>☐ FAIL | COL.05: Bloqueo saliente. |
| **228** | **NUEVO** - Resumen Forense | Simular Hand-off tras consulta | Nota interna con Timestamp, Contact ID, Clave y Motivo. | ☐ PASS<br>☐ FAIL | AUD.03: Visibilidad al asesor. |
| **229** | **NUEVO** - DAT.01 DLP Masking | Enviar SSN: `'Mi SSN es 123-45-6789'` | Enmascaramiento DLP a `XXX-XX-6789` antes de Respond.io. | ☐ PASS<br>☐ FAIL | DAT.01: Protección NPI. |
| **230** | **NUEVO** - HOR.02 Contingencia SC | Consulta requiriendo SC a las 11 PM | Entrega `SC.027` y retiene ticket en espera activa. | ☐ PASS<br>☐ FAIL | HOR.02: Retención en cola. |
