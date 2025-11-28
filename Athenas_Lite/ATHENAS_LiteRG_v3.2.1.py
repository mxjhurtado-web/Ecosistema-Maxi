#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ATHENAS Lite v3.2.1 MIRI :) — Dept JSON Rubrics LOCAL + Email Auth + GSM + Exports
- Autorización por correo (GS_AUTH_SHEET_ID: A=correo, B=nombre).
- Selección de Departamento (lista fija). Evalúa SOLO con JSON local en ./rubricas/<Departamento>.json
- Prompt dinámico a partir del JSON (rúbrica).
- Sentimiento global y por roles. Modo Gemini real u offline (mocks).
- Scoring: Score Bruto (incluye N/A), Score Final (aplica críticos).
- .gsm → WAV 16k mono (ffmpeg). Export TXT/CSV y subida opcional a Drive (solo exports).
- CSV: una columna por atributo con el valor obtenido: "Cumplido <key>" = <otorgado>.
"""

import os, sys, io, re, json, base64, subprocess, pathlib, mimetypes
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import tkinter.font as tkfont
from datetime import datetime
from collections import Counter, defaultdict

# ===== Opcionales =====
try:
    from PIL import Image, ImageTk
except Exception:
    Image = ImageTk = None

try:
    import pandas as pd
except Exception:
    pd = None

# ===== Google APIs (para exportar a Drive y autorización por Sheet) =====
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
    _GOOGLE_OK = True
except Exception:
    _GOOGLE_OK = False

# ===== Gemini opcional =====
try:
    import google.generativeai as genai
except Exception:
    genai = None

GLOBAL_RULES = {
    "UNIVERSAL_DE_ENFOQUE": """REGLA UNIVERSAL DE ENFOQUE: Toda la evaluación de 'ok' y 'aplicable' se enfoca EXCLUSIVAMENTE en el desempeño del asesor evaluado, ignorando completamente cualquier error, comportamiento o acción de otros asesores o agentes que interactuaron previamente en la llamada.""",

    "etiqueta_qm": """REGLA 'QM': Cualquier item con una 'key' que contenga 'etiqueta_qm' (por ejemplo 'etiqueta_qm_entrada') DEBE SER MARCADO SIEMPRE como 'aplicable: false' cuando la llamada no es una llamada de Calidad/Quality Monitoring (QM).""",

    "CAPACITACION": """REGLA 'Capacitación': Si el departamento es 'Capacitación', debes evaluar la llamada como un role play o sesión de entrenamiento interna. Si se está usando una cédula con secciones de producción y capacitación, cuando estés evaluando la parte de capacitación, cualquier item que pertenezca a la parte de producción (o viceversa) se marca 'aplicable:false' (NA). Nunca mezcles criterios productivos con criterios de capacitación en la misma sección: si la sección está configurada para capacitación, marca TODOS los items de la OTRA sección como 'aplicable: false'.""",

    "ENCUESTA_MAXI": """REGLA 'Encuesta Maxi': Cualquier item con la key 'encuesta_maxi' o similar solo aplica cuando el objetivo de la llamada es aplicar la encuesta Maxi al cliente. Si la llamada es de otro tipo (soporte, reclamo, seguimiento, etc.), o si la encuesta Maxi no se menciona ni se intenta aplicar, entonces el ítem de 'Encuesta Maxi' se marca 'aplicable:false'. También se considera 'aplicable:false' si la llamada no es con el cliente final al que corresponde la encuesta o si el cliente que llama no es el mismo cliente que aparece como titular de la encuesta.""",

    "DERECHOS_DE_CANCELACION": """REGLA 'Derechos de Cancelación' (Crítico Condicional): Este ítem es CRÍTICO solo si el producto o contexto de la llamada requiere que el asesor explique explícitamente los derechos de cancelación. Si el producto o servicio que se ofrece o contrata en la llamada tiene obligación de informar derechos de cancelación y el asesor NO lo hace, o lo hace de forma errónea, se marca 'ok: false' y el score total de la cédula se anula (0%). Si el producto NO requiere informar derechos de cancelación (por regulación o por el tipo de producto), se marca 'aplicable:false' y NO afecta el score.""",

    "INFO_CORRECTA": """REGLA 'Info Correcta' (Administrativo NA=5): Este item SIEMPRE se marca 'aplicable:false' (NA) cuando el asesor no tiene control directo sobre la información que se está validando (por ejemplo sistemas que ya traen datos precargados) o cuando el sistema corrige automáticamente cualquier dato incorrecto. Si el asesor da un dato incorrecto y luego se corrige inmediatamente sin impacto para el cliente, IGNORAR el error completamente.""",

    "DOCUMENTACION_CORPORATE": """REGLA 'Documentación Corporate' (Administrativo NA=5): Este item SIEMPRE se marca como 'aplicable:false' cuando la documentación de corporate no depende de lo que diga el asesor en la llamada, sino de procesos fuera de la interacción telefónica. En estos casos, no se evalúa audio. El sistema otorga automáticamente los 5 puntos.""",

    "NOTAS_CORPORATE": """REGLA 'Notas Corporate' (Administrativo NA=5): Este item SIEMPRE se marca 'aplicable:false' cuando las notas corporate se generan en sistemas internos ajenos a la llamada o por procesos posteriores. No se evalúa audio. El sistema otorga automáticamente los 5 puntos.""",

    "TRANSFERENCIA_WARM": """REGLA BLINDADA 'Transferencia Warm':
    - CONDICIÓN DE ACTIVACIÓN: Evalúa ÚNICAMENTE si el asesor evaluado (la voz principal) realiza una transferencia SALIENTE hacia otro departamento.
    - INMUNIDAD (CASO DE BLOQUEO): Si la llamada INICIA con una transferencia (el asesor recibe la llamada), y el cliente se queja de que lo transfirieron mal o tiene que repetir datos, ESTO NO ES CULPA DEL ASESOR ACTUAL. En este caso, marca 'aplicable: false'.
    - SOLO aplica si el asesor actual intenta conectar al cliente con un tercero. Si el asesor resuelve la llamada él mismo y cuelga, marca 'aplicable: false'.""",

    "SEGUIMIENTO_FRESH": """REGLA 'Seguimiento Fresh' (Administrativo NA=4): Este item SIEMPRE se marca como 'aplicable:false' cuando el seguimiento de tickets o casos en Freshdesk/Freshservice no depende de la llamada en cuestión (por ejemplo, si el ticket se gestiona completamente fuera del canal telefónico). En estos casos, no se evalúa audio. El sistema otorga automáticamente los 4 puntos.""",

    "CONEXION_REMOTA": """REGLA 'Conexión Remota' (Administrativo NA=5): Este item SIEMPRE se marca como 'aplicable:false' cuando la conexión remota no es parte obligatoria del flujo de la llamada (por ejemplo, llamadas informativas sin acceso remoto). Solo se considera 'aplicable:true' si la llamada tiene como parte esencial la conexión remota al equipo del cliente. De lo contrario, el sistema otorga automáticamente los 5 puntos. No se evalúa audio.""",

    "CREACION_TICKET_FRESH": """REGLA 'Creación Ticket Fresh' (Administrativo NA=5): Este item SIEMPRE se marca 'aplicable:false' cuando la creación de tickets en Freshdesk/Freshservice no ocurre durante la llamada o es un proceso completamente automático. En estos casos, no se evalúa audio. El sistema otorga automáticamente los 5 puntos.""",

    "ACTIVACION_DE_USUARIOS": """REGLA 'Activación de Usuarios' (Administrativo NA=5): Este item SIEMPRE se marca 'aplicable:false' cuando la activación de usuarios se realiza fuera de la llamada o mediante procesos automáticos y el asesor no tiene control directo en la interacción de voz. En estos casos, no se evalúa audio. El sistema otorga automáticamente los 5 puntos.""",

    "ADJUNTAR_EVIDENCIA_FRESH": """REGLA 'Adjuntar Evidencia Fresh' (Administrativo NA=5): Este item SIEMPRE se marca 'aplicable:false' cuando el adjuntar evidencias al ticket de Freshdesk/Freshservice no forma parte del flujo de la llamada y se hace fuera de ella. No se evalúa audio. El sistema otorga automáticamente los 5 puntos.""",

    "ACTIVACION_DE_PERMISOS": """REGLA 'Activación de Permisos' (Administrativo NA=5): Este item SIEMPRE se marca 'aplicable:false' cuando la activación de permisos se realiza por procesos administrativos fuera de la llamada. No se evalúa audio. El sistema otorga automáticamente los 5 puntos.""",

    "INTERACCION_VIA_PC": """REGLA 'Interacción vía PC' (Administrativo NA=5): Este item se marca 'aplicable:true' ÚNICAMENTE si hay conexión remota con invitación/aceptación entre el asesor y el cliente (por ejemplo, control remoto de equipo). Si no hay conexión remota, se marca 'aplicable:false' (NA) y el sistema otorga los puntos automáticos.""",

    "CAMBIO_DE_EQUIPO": """REGLA 'Cambio de Equipo' (Administrativo NA=5): Este item se marca 'aplicable:true' únicamente cuando en la llamada se gestiona explícitamente un cambio de equipo del cliente. Si no se habla de cambio de equipo, se marca 'aplicable:false' (NA) y el sistema otorga los puntos automáticos.""",

    "INFO_CORRECTA_AGENTE": """REGLA 'Info Correcta Agente' (Administrativo NA=5, Desactivado): Este item no se utiliza actualmente para afectar el score. Siempre se considera 'aplicable:false' y no se evalúa audio. Al estar desactivado, no afecta el score final.""",

    "CUMPLE_REGULACIONES_KYC": """REGLA 'Cumple Regulaciones KYC' (Administrativo NA=5): Este item SIEMPRE se marca 'aplicable:false' cuando el cumplimiento de regulaciones KYC se realiza mediante procesos internos o sistemas automáticos fuera de la llamada. No se evalúa audio. El sistema otorga automáticamente los 5 puntos.""",

    "REVISION_AGENCIA": """REGLA 'Revisión de Agencia' (Administrativo NA=6): Este item SIEMPRE se marca 'aplicable:false' cuando la revisión de agencia se realiza fuera de la llamada o por áreas especializadas. No se evalúa audio. El sistema otorga automáticamente los 6 puntos.""",

    "CONFIRMACION_AGENCIA": """REGLA 'Confirmación de Agencia' (Inmunidad): Si el asesor o el sistema confirmaron previamente la información de la agencia y el error proviene de una fuente externa (por ejemplo, datos de un tercero), el ítem no debe penalizar al asesor aunque la información sea incorrecta. Si el asesor sigue el procedimiento correcto, incluso si luego se descubre un error externo, el error se ignora y el ítem se marca como CUMPLIDO.""",

    "CONFIRMA_INFO_FICHA_DE_PAGO": """REGLA 'Confirma Info Ficha de Pago' (Condicional): Se marca 'aplicable:true' únicamente cuando la llamada trata sobre fichas de pago, comprobantes o instrucciones de pago a tiendas/agencias. Si la llamada no trata sobre estos temas, se marca 'aplicable:false'. Si aplica y el asesor no confirma correctamente la información de la ficha de pago (monto, fecha, referencia, etc.), se marca 'ok:false'. En otros casos se marca 'aplicable:false' y NO se penaliza.""",

    "PROPORCIONA_BALANCE_CORRECTO": """REGLA 'Proporciona Balance Correcto' (Condicional): Se marca 'aplicable:true' solo cuando el cliente pide explícitamente su balance, saldo, monto adeudado o monto disponible. Si la llamada es por otro tema, se marca 'aplicable:false' y NO se penaliza. Si aplica y el asesor no proporciona un balance correcto, se marca 'ok:false'.""",

    "BRINDA_INFO_COMISIONES": """REGLA 'Brinda Info Comisiones' (Condicional): Se marca 'aplicable:true' cuando el cliente pregunta por comisiones, cargos, tarifas o costos asociados a una transacción. Si el cliente nunca pregunta o la llamada es solo informativa sin detalle de comisiones, se marca 'aplicable:false'. Si aplica y el asesor no brinda información correcta, o la brinda de forma incompleta cuando se requiere desglose, se marca 'ok:false'. Si el cliente pide únicamente el total sin desglose, se marca 'aplicable:false' y NO se penaliza.""",

    "REALIZA_COMPROMISO_DE_PAGO": """REGLA 'Realiza Compromiso de Pago' (Condicional): Se marca 'aplicable:true' cuando en la llamada se busca acordar un compromiso de pago con el cliente. Si la llamada no tiene como objetivo negociar o acordar fechas montos de pago, se marca 'aplicable:false'. Si aplica y el asesor no obtiene un compromiso claro cuando era posible y necesario, se marca 'ok:false'. Si el cliente rechaza cualquier compromiso por falta de liquidez, se marca 'aplicable:false' y NO se penaliza al asesor.""",

    "DOCUMENTA_COMPROMISO_DE_PAGO": """REGLA 'Documenta Compromiso de Pago' (Administrativo NA=5): Este item SIEMPRE se marca 'aplicable:false' cuando el registro y documentación del compromiso de pago se realiza fuera de la llamada, en sistemas administrativos. No se evalúa audio. El sistema otorga automáticamente los 5 puntos.""",

    "NOTAS_CORRECTAS_CORPORATE": """REGLA 'Notas Correctas Corporate' (Administrativo NA=5): Este item SIEMPRE se marca 'aplicable:false' cuando la correcta redacción y almacenamiento de notas corporate se evalúa en sistemas internos y no durante la llamada. No se evalúa audio. El sistema otorga automáticamente los 5 puntos.""",

    "BUSCA_DUENO_U_OFICIAL": """REGLA 'Busca Dueño u Oficial' (Condicional): Se marca 'aplicable:true' cuando el contexto de la llamada requiere que el asesor busque o contacte al dueño u oficial responsable (por ejemplo, cuentas empresariales o casos de cumplimiento). Si el caso no exige contactar a un dueño u oficial, se marca 'aplicable:false' y NO se penaliza.""",

    "SE_AGENDA_AUDIOCONFERENCIA": """REGLA 'Se agenda audioconferencia' (Condicional): Se marca 'aplicable:true' únicamente cuando la llamada tiene como objetivo agendar una audioconferencia, reunión remota o similar. Si la interacción no implica agendar nada o solo es informativa, se marca 'aplicable:false'. Si aplica y el asesor no agenda la audioconferencia correctamente cuando el cliente lo necesita o se ha ofrecido, se marca 'ok:false'. Si la llamada era solo para confirmar datos o enviar diplomas, se marca 'aplicable:false' y NO se penaliza.""",

    "SE_CONFIRMA_ENTRENAMIENTO_FINALIZADO": """REGLA 'Se confirma entrenamiento finalizado' (Condicional): Se marca 'aplicable:true' cuando la llamada es de seguimiento a entrenamientos o capacitaciones y requiere confirmar si el entrenamiento se completó. Si el contexto de la llamada no es de capacitación o no se está verificando el cierre de entrenamiento, se marca 'aplicable:false'. Si aplica y el asesor omite confirmar correctamente, se marca 'ok:false'. Esto puede estar ligado a temas de cumplimiento o AML. Si no aplica, se marca 'aplicable:false' y NO se penaliza.""",

    "SE_ENVIA_O_REENVIA_DIPLOMA": """REGLA 'Se envía o reenvía diploma' (Condicional): Se marca 'aplicable:true' cuando el objetivo de la llamada incluye gestionar el envío o reenvío de un diploma o constancia de capacitación. Si la llamada no tiene nada que ver con diplomas, se marca 'aplicable:false'. Si aplica y el asesor no realiza el envío o reenvío cuando es necesario y acordado con el cliente, se marca 'ok:false'. Si no aplica, se marca 'aplicable:false' y NO se penaliza.""",

    "TRANSFERENCIA_CORRECTA": """REGLA 'Transferencia Correcta' (Condicional): Se marca 'aplicable:true' cuando en la llamada se realiza una transferencia de la llamada a otro asesor o área. Para considerar la transferencia como correcta, el asesor debe seguir buenas prácticas (informar motivo, enlazar con aviso, evitar transferencias en frío). Si no hay transferencia, se marca 'aplicable:false'. Si hay transferencia pero es inadecuada (en frío, sin avisar, sin confirmar), se marca 'ok:false'.""",

    "TIEMPO_DE_RESOLUCION_90_DIAS": """REGLA BLINDADA 'Tiempo de Resolución 90 días' (Crítico):
 - FILTRO DE BLOQUEO INMEDIATO (Si ocurre algo de esto, TU RESPUESTA DEBE SER 'ok: true', 'aplicable: false'):
   1. ¿La llamada es de SALIDA (Outbound)? -> BLOQUEAR (No aplica, aunque digan reporte).
   2. ¿Es un ENVÍO A CUENTA o DEPÓSITO BANCARIO, ESTA RETENIDO, EN VERIFICACIÓN, RECHAZADO, CANCELADO? -> BLOQUEAR (No aplica).
   3. ¿Es una COORDINACIÓN, corrección de folio, corrección de datos del beneficiario, desbloqueo o error de captura? -> BLOQUEAR (No aplica).
   4. ¿El envío está DISPONIBLE (aunque la tienda no quiera pagar o tenga problemas técnicos)? -> BLOQUEAR (No aplica).
   5. ¿Es cierre de caso o notificación de resolución, Notificación de Pagador o ya mandaron comprobante? -> BLOQUEAR (No aplica).
 - IMPORTANTE: En los casos anteriores (puntos 1-5), los asesores pueden usar la frase 'voy a levantar Reporte'. IGNORA esa frase si cae en el filtro de bloqueo.
 - CONDICIONES DE ACTIVACIÓN (EVALÚA SI CUMPLE TODO):
   1) La llamada es de ENTRADA (Inbound) de consumidores, es decir clientes o beneficiarios.
   2) El cliente reporta que el beneficiario NO COBRÓ/RECIBIÓ el dinero.
   3) El asesor indica explícitamente que debe LEVANTAR UN REPORTE o INICIAR INVESTIGACIÓN DE PAGO.
   * Llamada de ENTRADA + Dinero PERDIDO/NO APARECE/NO COBRADO + Se LEVANTA UN REPORTE o INICIA INVESTIGACIÓN DE PAGO.
 - REGLA DE ORO (DEFAULT): Ante cualquier duda entre 'Coordinación' u otros motivos y estos casos, si NO se cumplen las condiciones exactas, ASUME que NO APLICA (ok: true, aplicable: false).
 - SOLO SI APLICA REALMENTE: El asesor debe decir '1 a 90 días'. Si omite el plazo, marca 'ok: false'.""",

    "DUAL_CONSENT": """REGLA BLINDADA 'Dual Consent' (Crítico):
 - CONDICIÓN DE ACTIVACIÓN (Debe cumplir TODO para aplicar):
   1) La llamada es de SALIDA (Outbound) dirigida a un CONSUMIDOR (cliente/beneficiario).
   2) El destinatario es un CONSUMIDOR FINAL (no una empresa o agente).
 - LISTA DE INMUNIDAD (SIEMPRE MARCAR 'ok: true', 'aplicable: false'):
   * Si la llamada es de ENTRADA (Inbound) -> NO APLICA.
   * Si es una transferencia interna -> NO APLICA.
   * Si el destinatario es una AGENCIA, TIENDA, AGENTE -> NO APLICA.
   * Si el asesor lo dice (aunque sea rápido), marca CUMPLIDO (para proteger el score).
 - REGLA DE ORO (DEFAULT): Ante cualquier duda, o si NO se cumplen las condiciones exactas, TU RESPUESTA DEBE SER 'ok: true', 'aplicable: false'.
 - SOLO SI APLICA (y no hay inmunidad): El asesor debe mencionar explícitamente que la llamada puede ser grabada o monitoreada 'para fines de calidad' o similar. Si lo omite, marca 'ok: false'.
\nCriterios y pesos (para tu referencia):
\nCriterios críticos (para tu referencia):
\nRecuerda: Responde ÚNICAMENTE con el objeto JSON solicitado.""",
}


RULES_BY_DEPT = {
    # Reglas que se aplican a TODOS los departamentos
    "_COMUNES": [
        "UNIVERSAL_DE_ENFOQUE",
    ],

    "Administración de agencias": [
        "SEGUIMIENTO_FRESH",
        "etiqueta_qm",
    ],

    "Agent Oversight": [
        "REVISION_AGENCIA",
        "etiqueta_qm",
   
    ],

    "BSA Monitoring": [
        "BUSCA_DUENO_U_OFICIAL",
        "TRANSFERENCIA_WARM",
        "etiqueta_qm",
    ],

    "Capacitación": [
        "CAPACITACION",
        "etiqueta_qm",      
        "SE_CONFIRMA_ENTRENAMIENTO_FINALIZADO",
        "SE_ENVIA_O_REENVIA_DIPLOMA",
        "SE_AGENDA_AUDIOCONFERENCIA",
    ],

    "Cheques": [
        "etiqueta_qm",  
        "INFO_CORRECTA_AGENTE",
        "NOTAS_CORRECTAS_CORPORATE",
        "CONFIRMACION_AGENCIA",

    ],

    "Cobranza": [
       "CONFIRMACION_AGENCIA",
       "CONFIRMA_INFO_FICHA_DE_PAGO",
       "etiqueta_qm",
       "BRINDA_INFO_COMISIONES",
       "PROPORCIONA_BALANCE_CORRECTO"
       "REALIZA_COMPROMISO_DE_PAGO",
       "DOCUMENTA_COMPROMISO_DE_PAGO",
       "NOTAS_CORRECTAS_CORPORATE",
    ],

    "Cumplimiento": [
        "TRANSFERENCIA_WARM",
        "CUMPLE_REGULACIONES_KYC",
        "INFO_CORRECTA",
        "DOCUMENTACION_CORPORATE",
        "NOTAS_CORPORATE",
        "etiqueta_qm",
    ],

    "Prevención de fraudes": [
        "etiqueta_qm",
        "TRANSFERENCIA_CORRECTA",
        "NOTAS_CORPORATE",
    ],

    "Servicio al cliente": [
        "DUAL_CONSENT",
        "TIEMPO_DE_RESOLUCION_90_DIAS",
        "INFO_CORRECTA",
        "NOTAS_CORPORATE",
        "etiqueta_qm",

    ],

    "Soporte técnico": [
        "CONEXION_REMOTA",
        "INTERACCION_VIA_PC",
        "CAMBIO_DE_EQUIPO",     
        "CREACION_TICKET_FRESH",
        "ADJUNTAR_EVIDENCIA_FRESH",
        "ACTIVACION_DE_USUARIOS",
        "etiqueta_qm",
        "ACTIVACION_DE_PERMISOS",
    ],

    "Ventas internas (Ajustes)": [
        "etiqueta_qm",
    ],

    "Ventas Internas (Bienvenida)": [
        "etiqueta_qm",
    ],

    "Ventas telefónicas": [
        "DERECHOS_DE_CANCELACION",
        "ENCUESTA_MAXI",
        "etiqueta_qm",

    ],
}

# ================= ENV / CONFIG =================
# Service Account embebida por B64 (para Sheets/Drive en exports, NO para rúbricas)
SA_JSON_B64 = os.environ.get("ATHENAS_SA_JSON_B64", "ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAibWF4aWJvdC00NzI0MjMiLAogICJwcml2YXRlX2tleV9pZCI6ICJmOTFkMGRjYWM2ODA4NTYyY2IxOTRlOWM0NmU5ZDM2MGY1ZTNjNTczIiwKICAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUURIN0IrZ0JnTU9ScElmXG50ejJQSWRieXpoUnduSitVcitZN05JT1FsRGpNMWgweEl3dUIrNHZ6M2w4M1J1dWJ5VEQvbUQ1NklDckJONkg2XG50RkNDcTErbytsMWl0T1lHYkNVajdCcnBZM3ZnbHJmUVJFcUdnV1EzT2lxdGR6bHE3b3RhZk11K1d6bVlKODVQXG5QNnl1SUVJbnUyVXFEYW5WV3ZrL2Q1WnlaRkF3UG9IRDVIMldKcGlwblNhTW1HcXhDRG5RWTAxVDAwUWRiaStIXG42NlFscXdCQURFajZXWHhCNm1BdXZIdXRJTG4vaWRsYWpZRU4zVDd3OTJ1Q2JPNVk1dlFuUlI1TGViS1paaE5hXG5ZbTlPanp3TE9SekFPVG9rWCswWXZxUGFhTXplV2lncWY5RDJMZ3NMbE1sZnpBNXpxQkhEV0szaTJGMngvYWNXXG5jVkJIRzI2N0FnTUJBQUVDZ2dFQUNndWVSeThtSmloN25TWmE3SDg1eXJkNkpYSnBQbEpjVWl0QVZScHRoRFZhXG5BQ2NQby9kY3YrTXppNVovcmpNOHlBc0JVS2VmSGxoS1JrdWJKQVd5Wjg0MHRRbjc2T1MwTlFyZkMwMFpZMTZQXG5XK0tpa0FHZVpId0N1dmFicHZqWGZiTjVsVllHSGRRYU5MY3hXUXA3NkgwdEJ5RHFvTExTaFZMZjkxMTgvZjkvXG5RVGlIMk1pMkZNS3crVS93ckVsbmV0SFIrSE1vV2Fia2picGx4cEZQRDNMTkpWU0oybHkwUzBzb2praDV0WEZ5XG5ubDJXVUJPd1FTVmNmQzhvVHNwQXM3SUpXRzZVYldBc2dkZHlWZUU1VDRkZGFoa0JDSEhYQVFBUVYzYjJFTGM2XG54USs5WVFxS2VJNmNTMW5OeHNRUjBlK1V3OG1zT3V1MElSS3Mva2hmQVFLQmdRRHlzUGVGaFJUZ01kd1NsS2dCXG5vVHlnTUxtd3JVUGhzMXJ6d1g1eEVaUWtSRmVjb2F4M0U3WDJFTnRpR1AyRm9oU0R4VVd4TFE3czMyaFFOU0RpXG5tbmh1NWs4SVk1Nmt2VGxjbzlMeDV5TEF5UHEyTFNQWDUrYmowZXkzdEZkVXFaT0dqWlRrV0R3NUh4QlBRMHIyXG5BbFFKT01RUURMRHFPQnFXWUd4YksydHdPd0tCZ1FEUzRyNDkybk92TGhMaHYyMm0yUTlVa3BRcis4RC9udXQ5XG45ajJwSzFQQ1dRRmJhSHRVWit3NFhPUk1pczVqM3ZaTkg3aDd0Z3hvM0FhTGhGMS8wSlJYaTlpS2V2SmpKU0JjXG5zREI2SFE5cFBmNUU0SHNPOE9zejBDNjMzYXNMUFNZakIwNFdUWkVtQ0J2dFoxeGtXZHpQdG1VajZSYThSZUkwXG56TkFDeXpLVGdRS0JnQmZ3enlvVHU4QjJDckNtaTRCRnFKWmcyQ0NPcHhDZndjd2ovVllvRnNZUkc5ZHV0M1d6XG5zeEtJRFN3N0xOOCs0dWt3ejdRdnJyWTlQNndSNGFHWS9XSnJROGFmRlNwSkpGeDRLTG9HUkE1aWhTRHRpUWltXG5ic2R3a1BwNlJ0Y3FOMHhoc1J0cGZOOWhxaGszbVRCMWdGYThpOUxOZmJKTlFJb3ZEdUZiZ2lpN0FvR0FPdGdZXG5PNHdzUVpKNnBGRlZHSHh5NGFkdy93RGxycTQ2aWRCZkRraFB1K2c0RDdpTXlWV2lQV3YyTEVHREs2ejRUemJ0XG50Rjl0QVFsOExnd0dSdmI5blp3aEZTc1BYWWpyaWRHRUJWNzhnT0pTaEFlYmJ1VGN6SDFudTloM3ROQWdSeC92XG5zeHQ3eC8vMVF2NVhjb3o4cDF6K3hkRnhqYUYyYUVOS082MVZkSUVDZ1lFQXovMTRCVnZDQ2MzRGg0elBFOXlBXG4weEp0ZDhzNUw2YUdnT3h5RzRZR3VuKzZ0QTBKOWZvUWV4cHd2azFpWGlOYXZvWTNWN3haRUNSSm1ua2l4TEEzXG53bWZ3YzZFTkVWWjg0b2Y0VU42SVRSdCtHRytGZThTaE05STBFVHpFYWlTcmQvT0VxQ1VQZVlNelNQQVNIakRCXG5PdW1LWHlkU2N5NWhlNUdpNm9rc2MyWT1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsCiAgImNsaWVudF9lbWFpbCI6ICJtYXhpYm90LXNhQG1heGlib3QtNDcyNDIzLmlhbS5nc2VydmljZWFjY291bnQuY29tIiwKICAiY2xpZW50X2lkIjogIjExNjkyMDExNDg3MTgwMTYxMTEzOSIsCiAgImF1dGhfdXJpIjogImh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9hdXRoIiwKICAidG9rZW5fdXJpIjogImh0dHBzOi8vb2F1dGgyLmdvb2dsZWFwaXMuY29tL3Rva2VuIiwKICAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92MS9jZXJ0cyIsCiAgImNsaWVudF94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL3JvYm90L3YxL21ldGFkYXRhL3g1MDkvbWF4aWJvdC1zYSU0MG1heGlib3QtNDcyNDIzLmlhbS5nc2VydmljZWFjY291bnQuY29tIiwKICAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIgp9Cg==").strip()

# Carpeta de Drive solo para exportar CSV (opcional)
DRIVE_EXPORT_FOLDER_ID = os.environ.get("DRIVE_EXPORT_FOLDER_ID", "18I2zDaj_sQbQvBiRyySdwuT2UYRNzaBt").strip()

# Sheet para autorización por correo (A: correo, B: nombre)
GS_AUTH_SHEET_ID = os.environ.get("GS_AUTH_SHEET_ID", "1Ev3i55QTW1TJQ_KQP01TxEiLmZJVkwVFJ1cn_p9Vlr0").strip()

# API key opcional de Gemini (si no, la pide UI)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# Carpeta local de rúbricas (junto al .py)
LOCAL_RUBRICS_DIR = "rubricas"

# Carpeta local de exports
EXPORT_FOLDER = "exports"
os.makedirs(EXPORT_FOLDER, exist_ok=True)

ruta_audio = []
carpeta_guardado = None
nombre_Evaluador_personalizado = ""
nombre_asesor = ""
selected_department = None

API_KEY_GEMINI = None
USE_REAL_MODEL = False

PALETTE = {"bg": "#fceff1", "brand": "#e91e63", "brand_dark": "#c2185b"}

import unicodedata

def _normalize_name(s: str) -> str:
    s = (s or "").strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.casefold()

# ================= Google helpers =================
def _load_sa_info():
    if not SA_JSON_B64:
        return None
    try:
        b64c = "".join(SA_JSON_B64.strip().split())
        b64c += "=" * (-len(b64c) % 4)
        data = base64.b64decode(b64c.encode("utf-8"))
        return json.loads(data.decode("utf-8"))
    except Exception:
        return None

def _creds(scopes):
    if not _GOOGLE_OK:
        return None
    info = _load_sa_info()
    if not info:
        return None
    try:
        return service_account.Credentials.from_service_account_info(info, scopes=scopes)
    except Exception:
        return None

def _drive_service():
    if not _GOOGLE_OK or not DRIVE_EXPORT_FOLDER_ID:
        return None
    creds = _creds(["https://www.googleapis.com/auth/drive"])
    if creds is None:
        return None
    return build("drive", "v3", credentials=creds)

def _sheets_service():
    if not _GOOGLE_OK or not GS_AUTH_SHEET_ID:
        return None
    creds = _creds(["https://www.googleapis.com/auth/spreadsheets.readonly"])
    if creds is None:
        return None
    return build("sheets", "v4", credentials=creds)

# ================= Autorización por correo =================
def verificar_correo_online(correo: str):
    try:
        svc = _sheets_service()
        if not svc:
            messagebox.showerror("Credenciales", "No hay Service Account configurado. Define ATHENAS_SA_JSON_B64.")
            return False, None
        meta = svc.spreadsheets().get(spreadsheetId=GS_AUTH_SHEET_ID).execute()
        for s in meta.get("sheets", []):
            title = s["properties"]["title"]
            rows = svc.spreadsheets().values().get(spreadsheetId=GS_AUTH_SHEET_ID, range=f"'{title}'!A:Z").execute().get("values", [])
            if not rows:
                continue
            header = [str(h).strip().lower() for h in rows[0]]
            if "correo" in header:
                i_c = header.index("correo")
                i_n = header.index("nombre") if "nombre" in header else None
                for r in rows[1:]:
                    if i_c < len(r) and str(r[i_c]).strip().lower() == correo.strip().lower():
                        nombre = str(r[i_n]).strip() if (i_n is not None and i_n < len(r)) else correo
                        return True, nombre
    except Exception as e:
        messagebox.showerror("Sheets", f"Error validando correo:\n{e}")
    return False, None

# ================= ffmpeg / ffprobe =================
def _bin_path(name: str) -> str:
    exe = f"{name}.exe" if os.name == "nt" else name
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        return os.path.join(base, exe)
    return exe

def verificar_ffmpeg():
    try:
        subprocess.run([_bin_path("ffmpeg"), "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except Exception:
        return False

def verificar_ffprobe():
    try:
        subprocess.run([_bin_path("ffprobe"), "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except Exception:
        return False

def guess_mime(path: str) -> str:
    m, _ = mimetypes.guess_type(path)
    return m or "audio/wav"

def ffprobe_duration(path: str):
    try:
        resultado = subprocess.run(
            [_bin_path("ffprobe"), "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        out = (resultado.stdout or "").strip()
        if out:
            return float(out)
    except Exception:
        pass
    try:
        proc = subprocess.run([_bin_path("ffmpeg"), "-i", path],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, check=False)
        m = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)", proc.stderr or "")
        if m:
            h, m_, s = m.groups()
            return int(h) * 3600 + int(m_) * 60 + float(s)
    except Exception:
        pass
    return None

def human_duration(seconds):
    if seconds is None:
        return "N/A"
    seconds = int(round(seconds))
    mm, ss = divmod(seconds, 60)
    hh, mm = divmod(mm, 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d}" if hh else f"{mm:02d}:{ss:02d}"

def extraer_audio(video_path, output_path):
    """Extrae a WAV mono 16k desde cualquier contenedor (incluye .gsm)."""
    try:
        subprocess.run([
            _bin_path("ffmpeg"), "-y", "-i", video_path, "-vn",
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", output_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return output_path
    except Exception:
        return None

# ================= Gemini =================
def configurar_gemini(api_key: str) -> bool:
    global API_KEY_GEMINI, USE_REAL_MODEL
    api_key = (api_key or "").strip()
    if not api_key or not genai:
        USE_REAL_MODEL = False
        API_KEY_GEMINI = None
        return False
    try:
        genai.configure(api_key=api_key)
        API_KEY_GEMINI = api_key
        USE_REAL_MODEL = True
        return True
    except Exception:
        USE_REAL_MODEL = False
        return False

def _gemini_model(name="gemini-2.5-flash"):
    if USE_REAL_MODEL and genai:
        try:
            return genai.GenerativeModel(name)
        except Exception:
            return None
    return None

def llm_json_or_mock(prompt: str, audio_path: str, fallback: dict) -> dict:
    model = _gemini_model()
    if model:
        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            resp = model.generate_content(
                [prompt, {"mime_type": guess_mime(audio_path), "data": audio_bytes}],
                generation_config={"response_mime_type": "application/json"}
            )
            text = getattr(resp, "text", None) or ""
            return json.loads(text)
        except Exception:
            pass
    return fallback

def llm_text_or_mock(prompt: str, audio_path: str, fallback_text: str) -> str:
    model = _gemini_model()
    if model:
        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            resp = model.generate_content([prompt, {"mime_type": guess_mime(audio_path), "data": audio_bytes}])
            return (getattr(resp, "text", None) or "").strip()
        except Exception:
            pass
    return fallback_text

# ================= Rúbricas LOCAL =================
def load_dept_rubric_json_local(dept: str) -> dict | None:
    """
    Busca ./rubricas/<Departamento>.json (tolerante a acentos y mayúsculas).
    - Primero intenta match exacto.
    - Luego intenta match normalizado.
    """
    if not os.path.isdir(LOCAL_RUBRICS_DIR):
        return None

    expected_name = f"{dept}.json"
    expected_path = os.path.join(LOCAL_RUBRICS_DIR, expected_name)
    if os.path.exists(expected_path):
        try:
            with open(expected_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # búsqueda tolerante
    target_norm = _normalize_name(expected_name)
    try:
        for fn in os.listdir(LOCAL_RUBRICS_DIR):
            if not fn.lower().endswith(".json"):
                continue
            if _normalize_name(fn) == target_norm:
                with open(os.path.join(LOCAL_RUBRICS_DIR, fn), "r", encoding="utf-8") as f:
                    return json.load(f)
    except Exception:
        return None

    return None

def rubric_json_to_prompt(dept: str, rubric: dict) -> str:
    """
    Convierte la rúbrica JSON en un prompt "Gemini-ready".
    (Versión con esquema JSON explícito para mayor fiabilidad)
    """
    dep = rubric.get("department") or dept
    sections = rubric.get("sections", [])
    criticos = rubric.get("section_VI", {}).get("criticos", [])

    # incluye críticos marcados en items
    for s in sections:
        for it in s.get("items", []) or []:
            if it.get("critico", False) and it.get("key"):
                criticos.append({"key": it["key"]})

    out = []
    out.append(f"Departamento: {dep}")
    out.append("ESCUCHA Y Analiza el audio y responde SOLO con un objeto JSON que siga este esquema EXACTO (sin comentarios, sin markdown):")
# ----- INICIO DE INSTRUCCIONES  -----
    out.append("\nInstrucciones clave para la evaluación:")
    out.append("1. 'ok: true' significa que el agente CUMPLIÓ exitosamente el criterio.")
    out.append("2. 'ok: false' significa que el agente NO CUMPLIÓ el criterio (sea por omisión o por error).")
    out.append("3. 'aplicable: false' se usa EXCLUSIVAMENTE cuando el contexto de la llamada hizo IMPOSIBLE evaluar el criterio (ej. el cliente colgó antes del saludo).")
    out.append("4. 'evidencia': Si marcas 'ok: false' o 'aplicable: false', justifica brevemente por qué.")
    # ===== Reglas especiales de evaluación =====
    out.append("\nReglas Especiales de Evaluación:")

    # 1) Reglas comunes para todos
    active_rule_keys = list(RULES_BY_DEPT.get("_COMUNES", []))

    # 2) Reglas específicas del departamento actual
    active_rule_keys += RULES_BY_DEPT.get(dep, [])

    # 3) Quitar duplicados respetando el orden
    seen = set()
    active_rule_keys = [k for k in active_rule_keys if not (k in seen or seen.add(k))]

    # 4) Pegamos el texto de cada regla desde GLOBAL_RULES
    for key in active_rule_keys:
        rule_text = GLOBAL_RULES.get(key)
        if rule_text:
            out.append(rule_text)

    # Refuerzo anti-alucinación
    out.append(
        "\nIMPORTANTE:\n"
        "- Aplica estas reglas SOLO si el contenido del audio coincide claramente con lo descrito.\n"
        "- Si la llamada no encaja en un caso especial, IGNORA la regla especial.\n"
        "- En caso de duda, evalúa únicamente con los criterios generales del JSON."
    )
    out.append(
        "- Si la llamada coincide parcialmente con el caso especial, pero el cumplimiento es razonable, "
        "prefiere marcar 'ok: true' o 'aplicable: false' en lugar de 'ok: false'."
    )

    out.append("\nCriterio de TOLERANCIA (muy importante):")
    out.append(
        "- SOLO marca 'ok: false' cuando la falla sea CLARA, IMPORTANTE y tenga impacto real "
        "en la experiencia del cliente, en la operación o en el cumplimiento."
    )
    out.append(
        "- Si la evidencia es dudosa, incompleta o ambigua, prefiere marcar 'ok: true' o "
        "'aplicable: false' en lugar de castigar al asesor."
    )
    out.append(
        "- Errores pequeños de forma (muletillas, frases no perfectas, ligeros cambios en el guion) "
        "NO deben marcarse como 'ok: false' si el objetivo principal del criterio se cumple."
    )
    out.append(
        "- Nunca inventes errores: si no encuentras evidencia clara en el audio, asume que el criterio "
        "se cumplió o que 'no aplica'."
    )

    # ----- FIN-----

    schema_prompt = f"""
{{
  "department": "{dep}",
  "sections": [
    {{
      "name": "(nombre de la sección, ej: Saludo)",
      "items": [
        {{
          "key": "(clave_del_item, ej: tiempo_respuesta)",
          "peso": "(el peso numérico original del item, ej: 4)",
          "ok": (true | false),
          "aplicable": (true | false),
          "evidencia": "(justificación breve o cita del audio si no aplica o falla)"
        }}
      ]
    }}
  ],
  "section_VI": {{
    "criticos": [
      {{
        "key": "(clave_del_critico, ej: actitud_servicio)",
        "ok": (true | false)
      }}
    ]
  }},
  "fortalezas": ["(lista de 1 a 3 fortalezas observadas)"],
  "compromisos": ["(lista de 1 a 3 compromisos o áreas de mejora)"],
  "contenido_evaluador": "(Un resumen detallado en prosa de la llamada, destacando el desempeño del agente y los puntos clave de la interacción)"
}}
"""
    out.append("\n".join([line.strip() for line in schema_prompt.splitlines()]))

    out.append("\nCriterios y pesos (para tu referencia):")
    for s in sections:
        out.append(f"Sección: {s.get('name','(sin nombre)')}")
        for it in s.get("items", []) or []:
            peso = it.get("peso", 10)
            sug = it.get("sugerencias", [])
            suger = f" | sugerencias: {', '.join(sug)}" if sug else ""
            crit = " | CRITICO" if it.get("critico", False) else ""
            out.append(f" - {it.get('key','(sin clave)')} | peso: {peso}{suger}{crit}")

    if criticos:
        out.append("\nCriterios críticos (para tu referencia):")
        for c in criticos:
            out.append(f" - {c.get('key','(sin clave)')}")

    out.append("\nRecuerda: Responde ÚNICAMENTE con el objeto JSON solicitado.")
    return "\n".join(out)

def call_department_eval(dept: str, audio_path: str) -> dict:
    """
    Evalúa SOLO con la rúbrica JSON local (<Depto>.json).
    Si no existe o es inválida, se notifica y devuelve un stub mínimo.
    """
    rubric = load_dept_rubric_json_local(dept)
    if not rubric:
        # Mostrar qué archivos hay disponibles para ayudar a depurar
        listing = []
        if os.path.isdir(LOCAL_RUBRICS_DIR):
            try:
                listing = [fn for fn in os.listdir(LOCAL_RUBRICS_DIR) if fn.lower().endswith(".json")]
            except Exception:
                listing = []
        messagebox.showerror(
            "Rúbrica no encontrada",
            "No se encontró el archivo local de rúbrica:\n"
            f"  {os.path.join(LOCAL_RUBRICS_DIR, dept + '.json')}\n\n"
            + ("Archivos encontrados:\n- " + "\n- ".join(listing) if listing else "No hay JSON en 'rubricas/'")
        )
        return {
            "department": dept,
            "sections": [{"name": "Sin datos", "items": [{"key": "n/a", "peso": 10, "ok": False, "aplicable": True, "evidencia": ""}]}],
            "section_VI": {"criticos": []},
            "fortalezas": [],
            "compromisos": [],
            "contenido_evaluador": "No se pudo cargar la rúbrica del departamento."
        }

    prompt = rubric_json_to_prompt(dept, rubric)
    fallback = {
        "department": dept,
        "sections": rubric.get("sections", []) or [{"name": "Sin datos", "items": [{"key": "n/a", "peso": 10, "ok": False, "aplicable": True, "evidencia": ""}]}],
        "section_VI": rubric.get("section_VI", {"criticos": []}),
        "fortalezas": rubric.get("fortalezas", []),
        "compromisos": rubric.get("compromisos", []),
        "contenido_evaluador": ""
    }
    return llm_json_or_mock(prompt, audio_path, fallback)

# ================= Sentimiento =================
SENTIMENT_PROMPT = r"""
Escucha el audio y devuelve SOLO este texto (sin JSON):
### Resumen Cálido
<texto>

### Comentario Emocional
<texto>

### Valoración
<número 1-10>
"""

ROLE_SENTIMENT_PROMPT = """
Devuelve SOLO JSON:
{
    "cliente": {"valor": 1-10, "clasificacion": "Positiva|Neutra|Negativa", "comentario": "", "resumen": ""},
    "asesor":  {"valor": 1-10, "clasificacion": "Positiva|Neutra|Negativa", "comentario": "", "resumen": ""}
}
"""

def analizar_sentimiento(audio_path: str):
    text = llm_text_or_mock(SENTIMENT_PROMPT, audio_path,
                             "### Resumen Cálido\nMock\n\n### Comentario Emocional\nMock\n\n### Valoración\n7")
    resumen_match = re.search(r"### Resumen Cálido\s*(.*?)\s*### Comentario Emocional", text, re.DOTALL|re.IGNORECASE)
    comentario_match = re.search(r"### Comentario Emocional\s*(.*?)\s*### Valoración", text, re.DOTALL|re.IGNORECASE)
    valor_match = re.search(r"### Valoración\s*(\d{1,2})", text, re.IGNORECASE)

    resumen = (resumen_match.group(1).strip() if resumen_match else "").strip() or "Resumen no encontrado"
    comentario = (comentario_match.group(1).strip() if comentario_match else "").strip() or "Comentario no encontrado"
    try:
        valor = int(valor_match.group(1)) if valor_match else 7
    except Exception:
        valor = 7
    if valor >= 8:
        clasificacion = "Positiva"
    elif valor == 7:
        clasificacion = "Neutra"
    else:
        clasificacion = "Negativa"
    return valor, clasificacion, comentario, resumen

def analizar_sentimiento_por_roles(audio_path: str):
    fallback = {
        "cliente": {"valor": 6, "clasificacion": "Neutra", "comentario": "Mock", "resumen": "Mock"},
        "asesor":  {"valor": 8, "clasificacion": "Positiva", "comentario": "Mock", "resumen": "Mock"}
    }
    try:
        data = llm_json_or_mock(ROLE_SENTIMENT_PROMPT, audio_path, fallback)
    except Exception:
        data = fallback

    def _norm(d):
        v = d.get("valor", 7)
        try: v = int(v)
        except Exception: v = 7
        c = "Positiva" if v >= 8 else ("Neutra" if v == 7 else "Negativa")
        return {
            "valor": v,
            "clasificacion": d.get("clasificacion", c) or c,
            "comentario": d.get("comentario", ""),
            "resumen": d.get("resumen", "")
        }

    return _norm(data.get("cliente", {})), _norm(data.get("asesor", {}))

# ================= Scoring con N/A y Críticos =================
def aplicar_defaults_items(eval_data: dict) -> dict:
    for sec in (eval_data.get("sections") or []):
        for it in (sec.get("items") or []):
            if "ok" not in it:
                it["ok"] = False
            if "peso" not in it:
                it["peso"] = 10
            if "aplicable" not in it:
                it["aplicable"] = True
            if it.get("evidencia") is None:
                it["evidencia"] = ""
    return eval_data

def atributos_con_calificacion(sections):
    """
    Devuelve lista de dicts por atributo:
      - OK & aplicable=True  -> otorga 'peso'
      - NO & aplicable=True  -> otorga 0
      - aplicable=False (N/A)-> otorga 'peso'
    """
    detalles = []
    for sec in (sections or []):
        for it in (sec.get("items") or []):
            key = it.get("key", "(sin_key)")
            try:
                peso = int(it.get("peso", 0))
            except Exception:
                peso = 0
            aplicable = it.get("aplicable", True)
            ok = it.get("ok", False)

            if not aplicable:
                estado = "NA"
                otorgado = peso
            else:
                if ok:
                    estado = "OK"
                    otorgado = peso
                else:
                    estado = "NO"
                    otorgado = 0

            detalles.append({"key": key, "peso": peso, "estado": estado, "otorgado": otorgado})
    return detalles

def compute_scores_with_na(sections, criticos):
    """
    Retorna: score_bruto (incluye N/A, cap 100), fallo_critico (bool), score_final, detalles
    """
    detalles = atributos_con_calificacion(sections)
    score_bruto = sum(d["otorgado"] for d in detalles)
    try:
        score_bruto = int(max(0, min(100, score_bruto)))
    except Exception:
        score_bruto = 0
    fallo_critico = any(not c.get("ok", False) for c in (criticos or []))
    score_final = 0 if fallo_critico else score_bruto
    return score_bruto, fallo_critico, score_final, detalles

# ======== NUEVO: Helper para columnas "Cumplido <key>" = valor otorgado ========
def _atributos_a_columnas_valor(det_atrib):
    """
    Convierte detalle por atributo en columnas:
      - "Cumplido <key>" = valor 'otorgado' (int o 0/'' si falta)
    Retorna: (dict_columnas, set_base_keys)
    Formato esperado en det_atrib:
      {'key': 'tiempo_respuesta', 'estado': 'OK|NO|NA', 'peso': 4, 'otorgado': 4}
    """
    fila = {}
    base_keys = set()
    for d in det_atrib or []:
        key = (d.get("key") or "").strip()
        if not key:
            continue
        col = f"Cumplido {key}"
        otorg = d.get("otorgado")
        if otorg is None:
            otorg = d.get("ganado", 0)
        try:
            otorg = int(otorg)
        except Exception:
            pass
        fila[col] = otorg
        base_keys.add(key)
    return fila, base_keys

# ================= Drive Upload (CSV) =================
def subir_csv_a_drive(df, filename: str):
    try:
        if not DRIVE_EXPORT_FOLDER_ID or not _GOOGLE_OK:
            return None
        svc = _drive_service()
        if not svc:
            return None
        csv_bytes = df.to_csv(index=False, encoding="utf-8").encode("utf-8")
        media = MediaIoBaseUpload(io.BytesIO(csv_bytes), mimetype="text/csv", resumable=False)
        meta = {"name": filename, "mimeType": "text/csv", "parents": [DRIVE_EXPORT_FOLDER_ID]}
        f = svc.files().create(body=meta, media_body=media, supportsAllDrives=True, fields="id, webViewLink").execute()
        return f.get("webViewLink")
    except Exception:
        return None

# ================= IO / GUI Actions =================
def seleccionar_archivo():
    global ruta_audio
    archivos = filedialog.askopenfilenames(
        filetypes=[("Multimedia", "*.mp3 *.wav *.mp4 *.mov *.mkv *.m4a *.aac *.wma *.ogg *.flac *.gsm *.3gp *.avi")])
    if len(archivos) > 10:
        messagebox.showerror("Límite excedido", "Solo puedes seleccionar hasta 10 archivos.")
    else:
        ruta_audio = archivos
        messagebox.showinfo("🎧 Archivos seleccionados", f"{len(archivos)} archivos listos para analizar.")

def seleccionar_carpeta_guardado():
    global carpeta_guardado
    carpeta = filedialog.askdirectory(title="Selecciona carpeta de guardado")
    if carpeta:
        try:
            os.makedirs(carpeta, exist_ok=True)
            carpeta_guardado = carpeta
            messagebox.showinfo("📂 Carpeta seleccionada", f"Los archivos se guardarán en:\n{carpeta_guardado}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear/usar la carpeta:\n{e}")

def analizar_audio():
    global ruta_audio, nombre_Evaluador_personalizado, nombre_asesor, carpeta_guardado, selected_department

    if not ruta_audio:
        messagebox.showerror("Error", "Primero debes seleccionar al menos un archivo.")
        return
    if not carpeta_guardado:
        messagebox.showerror("Error", "Debes seleccionar la carpeta donde se guardarán los resultados.")
        return
    if not selected_department:
        messagebox.showerror("Departamento", "Selecciona el departamento en el modal antes de iniciar.")
        return
    if pd is None:
        messagebox.showerror("Dependencia", "Pandas no está instalado. Instala con: pip install pandas")
        return

    save_dir = carpeta_guardado
    os.makedirs(save_dir, exist_ok=True)

    resultados, scores_finales, sentiments_glob = [], [], []
    strengths_counter, failed_items = Counter(), Counter()
    dept_counts, dept_score_sum = Counter(), defaultdict(int)
    critical_fail_count = 0

    # ===== AQUI acumularemos todas las columnas "Cumplido <key>" que aparezcan =====
    all_cumplido_cols = set()

    for path in ruta_audio:
        try:
            nombre_archivo = os.path.basename(path)
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            ext = os.path.splitext(path)[1].lower()
            audio_final = path
            if ext not in [".mp3", ".wav"]:
                if not verificar_ffmpeg():
                    messagebox.showerror("FFmpeg", "ffmpeg no está disponible.")
                    return
                audio_final = os.path.join(save_dir, f"{pathlib.Path(nombre_archivo).stem}_extraido.wav")
                extraer_audio(path, audio_final)

            dur_secs = ffprobe_duration(audio_final)
            dur_str = human_duration(dur_secs)

            # Sentimiento
            val, clasif, comentario, resumen_calido = analizar_sentimiento(audio_final)
            sent_cli, sent_ase = analizar_sentimiento_por_roles(audio_final)

            # Evaluación con rúbrica JSON local
            dept = selected_department
            eval_data = call_department_eval(dept, audio_final)
            eval_data = aplicar_defaults_items(eval_data)
            sections = eval_data.get("sections", [])
            criticos = eval_data.get("section_VI", {}).get("criticos", [])
            fortalezas = eval_data.get("fortalezas", [])
            contenido_evaluador = eval_data.get("contenido_evaluador", "")

            # Score con N/A y críticos
            score_bruto, fallo_critico, score_final, det_atrib = compute_scores_with_na(sections, criticos)
            resumen = " • ".join(fortalezas[:2]) if fortalezas else resumen_calido

            # TXT por audio con el bloque solicitado
            txt_path = os.path.join(save_dir, f"{pathlib.Path(nombre_archivo).stem}_ATHENAS_Lite.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"Asesor: {nombre_asesor}\n")
                f.write(f"Evaluador: {nombre_Evaluador_personalizado}\n")
                f.write(f"Archivo: {nombre_archivo}\n")
                f.write(f"Departamento seleccionado: {dept}\n")
                f.write(f"Timestamp: {ts}\n")
                f.write(f"Duración: {dur_str}\n\n")

                f.write("Resumen:\n")
                f.write(resumen or "N/A")
                f.write("\n\nContenido para el evaluador:\n")
                f.write(contenido_evaluador or "N/A")

                f.write("\n--- CALIFICACIÓN FINAL ---\n")
                f.write(f"Score de Atributos (Puntaje Bruto, N/A incluido): {score_bruto}%\n")
                f.write(f"Score Final (Aplicando Críticos): {score_final}%\n")

                f.write("\n--- PUNTOS CRÍTICOS ---\n")
                if not criticos:
                    f.write("(Sin críticos configurados)\n")
                else:
                    for c in criticos:
                        keyc = c.get("key","(sin_key)")
                        okc = c.get("ok", False)
                        f.write(f"{keyc}: {'✅ Cumplido' if okc else '❌ No cumplido'}\n")

                f.write("\n--- Detalle por atributo ---\n")
                for d in det_atrib:
                    key = d["key"]; peso = d["peso"]; otorg = d["otorgado"]; est = d["estado"]
                    if est == "OK":
                        marca = "✅ Cumplido"
                    elif est == "NO":
                        marca = "❌ No cumplido"
                    else:
                        marca = "🟡 N/A"
                    f.write(f"{marca} {key} → {otorg} / {peso}\n")

                f.write("\n--- Sentimiento ---\n")
                f.write(f"Valoración (1-10): {val}\n")
                f.write(f"Clasificación: {clasif}\n")
                f.write(f"Comentario emocional: {comentario}\n")

                f.write("\n--- Sentimiento por roles ---\n")
                f.write(f"Cliente -> {sent_cli['clasificacion']} ({sent_cli['valor']}/10). {sent_cli['comentario']}\n")
                f.write(f"Asesor  -> {sent_ase['clasificacion']} ({sent_ase['valor']}/10). {sent_ase['comentario']}\n")

            # ===== NUEVO: columnas "Cumplido <key>" = valor otorgado
            fila_atrib, _keys = _atributos_a_columnas_valor(det_atrib)
            all_cumplido_cols.update(fila_atrib.keys())

            # Registro base para CSV consolidado
            r = {
                "archivo": nombre_archivo,
                "asesor": nombre_asesor,
                "timestamp": ts,
                "resumen": resumen,
                "sentimiento": val,
                "clasificación": clasif,
                "comentario": comentario,
                "evaluador": nombre_Evaluador_personalizado,
                "duración": dur_str,
                "duracion_seg": (round(dur_secs, 3) if dur_secs is not None else None),
                "contenido_evaluador": contenido_evaluador,
                "porcentaje_evaluacion": score_final,
                "score_bruto": score_bruto,
                "departamento": dept,
                "sentimiento_cliente": sent_cli["valor"],
                "clasificación_cliente": sent_cli["clasificacion"],
                "comentario_cliente": sent_cli["comentario"],
                "sentimiento_asesor": sent_ase["valor"],
                "clasificación_asesor": sent_ase["clasificacion"],
                "comentario_asesor": sent_ase["comentario"]
            }
            # Mezcla columnas dinámicas de atributos
            r.update(fila_atrib)

            resultados.append(r)
            scores_finales.append(score_final)
            sentiments_glob.append(val)

            # Agregados para consolidado
            dept_counts[dept] += 1
            dept_score_sum[dept] += score_final
            if any(not c.get("ok", False) for c in (criticos or [])):
                critical_fail_count += 1
            for sec in (sections or []):
                for it in sec.get("items", []):
                    if it.get("aplicable", True) and not it.get("ok", False):
                        failed_items[it.get("key","(sin_key)")] += 1
            for s in (fortalezas or []):
                strengths_counter[s.strip()] += 1

        except Exception as e:
            messagebox.showerror("Error", f"Fallo al analizar {path}:\n{e}")

    # ===== Normalizar columnas de atributos en todas las filas =====
    if resultados:
        for row in resultados:
            for col in all_cumplido_cols:
                row.setdefault(col, "")

    # CSV consolidado + resumen
    if resultados and pd is not None:
        df = pd.DataFrame(resultados)
        asesor_slug = re.sub(r'[^A-Za-z0-9_-]+', '_', (nombre_asesor or 'asesor').strip()) or 'asesor'
        ts_all = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_path = os.path.join(save_dir, f"ATHENAS_Lite_{asesor_slug}_{ts_all}.csv")
        try:
            df.to_csv(export_path, index=False, encoding="utf-8-sig")
        except Exception as e:
            messagebox.showerror("CSV", f"No se pudo escribir el CSV:\n{e}")
            export_path = None

        if len(resultados) >= 2:
            total = len(resultados)
            avg_score = round(sum(scores_finales)/total, 2) if scores_finales else 0.0
            avg_sent = round(sum(sentiments_glob)/total, 2) if sentiments_glob else 0.0

            lines = []
            lines.append("=== Resumen Consolidado ATHENAS Lite ===")
            lines.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Evaluador: {nombre_Evaluador_personalizado}")
            lines.append(f"Asesor: {nombre_asesor}")
            lines.append("")
            lines.append(f"Total de llamadas: {total}")
            lines.append(f"Promedio Score Final (%): {avg_score}")
            lines.append(f"Promedio Sentimiento (1-10): {avg_sent}")
            lines.append(f"Fallos críticos detectados: {critical_fail_count}")
            lines.append("")
            lines.append("— Distribución por departamento —")
            for d, c in dept_counts.items():
                prom = round(dept_score_sum[d]/c, 2) if c else 0.0
                lines.append(f"  {d}: {c} llamadas | Score prom: {prom}")
            lines.append("")
            lines.append("— Top 5 fallas —")
            for key, cnt in failed_items.most_common(5):
                lines.append(f"  {key}: {cnt} veces")
            lines.append("")
            lines.append("— Top 5 fortalezas —")
            for s, cnt in strengths_counter.most_common(5):
                lines.append(f"  {s}: {cnt} veces")

            resumen_path = os.path.join(save_dir, f"ATHENAS_Lite_Resumen_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt")
            try:
                with open(resumen_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
            except Exception as e:
                messagebox.showerror("TXT", f"No se pudo escribir el resumen:\n{e}")
                resumen_path = None

            messagebox.showinfo("🎉 Resumen consolidado",
                                f"CSV: {export_path or 'N/A'}\nResumen: {resumen_path or 'N/A'}")
        else:
            r = resultados[0]
            messagebox.showinfo(
                "✅ Análisis completado",
                f"{r['archivo']}\nDepto: {r['departamento']} | Score: {r['porcentaje_evaluacion']}%\n"
                f"Sentimiento: {r['clasificación']} ({r['sentimiento']}/10)\nCSV: {export_path or 'N/A'}"
            )

        # Subir CSV a Drive (si está configurado)
        try:
            if DRIVE_EXPORT_FOLDER_ID and export_path and pd is not None:
                df_up = pd.DataFrame(resultados)
                fn = f"ATLite_compilado_{(nombre_asesor or 'asesor').strip().replace(' ','_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                link = subir_csv_a_drive(df_up, fn)
                if link:
                    messagebox.showinfo("📤 Drive", f"Compilado subido a Drive:\n{link}")
        except Exception as e:
            print("Fallo subiendo a Drive:", e)

def solicitar_datos_y_analizar():
    global nombre_Evaluador_personalizado, nombre_asesor, selected_department
    if not ruta_audio:
        messagebox.showerror("Error", "Primero debes seleccionar al menos un archivo.")
        return
    if not carpeta_guardado:
        messagebox.showerror("Error", "Debes seleccionar la carpeta donde se guardarán los resultados.")
        return

    ventana = tk.Toplevel(root)
    ventana.title("Datos del análisis")
    ventana.configure(bg="#fceff1")
    fonts = pick_font(ventana)

    frm = tk.Frame(ventana, bg="#fceff1")
    frm.pack(padx=10, pady=10)

    tk.Label(frm, text="Nombre del Evaluador:", bg="#fceff1", font=fonts["body"]).grid(row=0, column=0, sticky="w", pady=4)
    entry_evaluador = tk.Entry(frm, width=40)
    entry_evaluador.grid(row=0, column=1, padx=8, pady=4)
    try:
        if nombre_Evaluador_personalizado:
            entry_evaluador.insert(0, nombre_Evaluador_personalizado)
            entry_evaluador.config(state="readonly")
    except Exception:
        pass

    tk.Label(frm, text="Nombre del asesor:", bg="#fceff1", font=fonts["body"]).grid(row=1, column=0, sticky="w", pady=4)
    entry_asesor = tk.Entry(frm, width=40)
    entry_asesor.grid(row=1, column=1, padx=8, pady=4)

    tk.Label(frm, text="Departamento:", bg="#fceff1", font=fonts["body"]).grid(row=2, column=0, sticky="w", pady=4)
    cb_dept = ttk.Combobox(frm, values=DEPT_OPTIONS_FIXED, state="readonly", width=37)
    cb_dept.grid(row=2, column=1, padx=8, pady=4)
    cb_dept.current(0)

    def continuar():
        global nombre_Evaluador_personalizado, nombre_asesor, selected_department
        nombre_Evaluador_personalizado = entry_evaluador.get().strip() or nombre_Evaluador_personalizado
        nombre_asesor = entry_asesor.get().strip()
        selected_department = cb_dept.get().strip()
        if not nombre_Evaluador_personalizado or not nombre_asesor or not selected_department:
            messagebox.showerror("Error", "Completa Evaluador, Asesor y Departamento.")
            return
        ventana.destroy()
        analizar_audio()

    tk.Button(ventana, text="Iniciar análisis", command=continuar, bg=PALETTE["brand"], fg="white").pack(pady=10)

# ================= Rúbricas / UI (lista fija) =================
DEPT_OPTIONS_FIXED = [
    "Administración de agencias",
    "Agent Oversight",
    "BSA Monitoring",
    "Capacitación",
    "Cheques",
    "Cobranza",
    "Cumplimiento",
    "Prevención de fraudes",
    "Servicio al cliente",
    "Soporte técnico",
    "Ventas internas (Ajustes)",
    "Ventas Internas (Bienvenida)",
    "Ventas telefónicas",
]

# ================= Estilo/UI helpers =================
def pick_font(root):
    families = set(tkfont.families(root))
    for fam in ["Segoe UI Variable", "Segoe UI", "Calibri", "Inter", "Arial"]:
        if fam in families:
            base = fam
            break
    else:
        base = "TkDefaultFont"
    return {
        "title": tkfont.Font(root, family=base, size=22, weight="bold"),
        "body":  tkfont.Font(root, family=base, size=10),
    }

def _resource_path(filename):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)

# ================= MAIN UI =================
root = tk.Tk()
root.title("ATHENAS Lite v3.2.1")
root.geometry("700x620")
root.configure(bg=PALETTE["bg"])

fonts_main = pick_font(root)

# 🔐 Autorización por correo
try:
    correo_ingresado = simpledialog.askstring("Autorización", "Ingresa tu correo corporativo:", parent=root)
    if not correo_ingresado:
        messagebox.showerror("Autorización", "Debes ingresar un correo para continuar.")
        root.destroy(); sys.exit(1)
    ok_auth, nombre_aut = verificar_correo_online(correo_ingresado.strip().lower())
    if not ok_auth:
        messagebox.showerror("Autorización", "Tu correo no está autorizado. Solicita alta en el Sheet.")
        root.destroy(); sys.exit(1)
    nombre_Evaluador_personalizado = nombre_aut or correo_ingresado
except Exception as e:
    messagebox.showerror("Autorización", f"No fue posible validar acceso:\n{e}")
    root.destroy(); sys.exit(1)

# 🔑 Gemini (opcional)
try:
    key = GEMINI_API_KEY or simpledialog.askstring("Gemini", "Pega tu API Key de Gemini (opcional):", show="*", parent=root)
    if key:
        configurar_gemini(key)
except Exception:
    pass

# Encabezado
header_frame = tk.Frame(root, bg=PALETTE["bg"])
header_frame.pack(pady=20)
try:
    if Image and ImageTk:
        logo_path = _resource_path("athenas2.png")
        if os.path.exists(logo_path):
            logo_img = Image.open(logo_path).resize((40, 55))
            logo_tk = ImageTk.PhotoImage(logo_img)
            tk.Label(header_frame, image=logo_tk, bg=PALETTE["bg"]).pack(side="left", padx=(5,2))
            header_frame.logo_tk = logo_tk
except Exception:
    pass

tk.Label(header_frame,
         text="Athenas Lite: Transforma la Voz en Calidad",
         font=fonts_main["title"], fg="#0D47A1", bg=PALETTE["bg"]).pack(side="left", padx=5)

# Zona de carga
zona_carga = tk.Frame(root, bg="#f9d6d5", bd=2, relief="groove")
zona_carga.pack(pady=20, padx=40, fill="x")
tk.Label(zona_carga, text="Carga tus audios (hasta 10)", font=fonts_main["body"], fg="#333333", bg="#f9d6d5").pack(pady=10)

btn_style = {"bg": PALETTE["brand"], "fg": "white", "font": fonts_main["body"], "width": 32}
tk.Button(root, text="Seleccionar archivo(s)", command=seleccionar_archivo, **btn_style).pack(pady=5)
tk.Button(root, text="Guardar en carpeta...", command=seleccionar_carpeta_guardado, **btn_style).pack(pady=5)
tk.Button(root, text="Analizar (Resumen consolidado)", command=solicitar_datos_y_analizar, **btn_style).pack(pady=5)

root.mainloop()
