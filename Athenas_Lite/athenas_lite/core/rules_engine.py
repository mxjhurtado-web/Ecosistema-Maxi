
GLOBAL_RULES = {
   "UNIVERSAL_DE_ENFOQUE": """REGLA DE FOCO 'LASER': IDENTIFICACIÓN POR ROL
    1. TU OBJETIVO (EL EVALUADO):
       - Es la persona que SE HACE CARGO de resolver la solicitud principal del departamento: {department}.
       - Es la voz que interactúa por más tiempo con el cliente buscando una solución.
    2. FILTRO DE VOCES (IGNORAR A OTROS):
       - Si escuchas a un primer agente que contesta y luego transfiere: IGNÓRALO COMPLETAMENTE. Ese es el "Agente Anterior".
       - Si escuchas a un tercer agente al final (porque tu asesor transfirió la llamada): IGNÓRALO COMPLETAMENTE. Ese es el "Agente Siguiente".
       - TU OBJETIVO es el agente intermedio (o final) que gestiona la solicitud específica de este departamento.
    3. REGLA DE TRANSFERENCIAS MÚLTIPLES:
       - No importa si hubo 1, 2 o 3 transferencias antes. Tu evaluación comienza EXACTAMENTE en el momento en que la voz del 'Departamento {department}' toma la llamada.
    4. PROHIBIDO 'N/A' EN HABILIDADES BLANDAS:
       - Aunque la llamada venga transferida, el Asesor Evaluado TIENE LA OBLIGACIÓN de saludar, tener buen tono y buena dicción.
       - Si el cliente llega enojado por culpa del agente anterior, NO penalices la 'Empatía' o 'Control' de tu asesor, a menos que él/ella también pierda el control.
       - Si el agente anterior no saludó bien, eso NO afecta la calificación de tu asesor EVALUADO. Evalúa solo el saludo de tu asesor cuando toma la llamada.
       - SIGUE EL ORDEN DE EVALUACION QUE MARCA EL JSON
       - Evalúa SU desempeño (aunque sea breve) y marca 'Cumplido' o 'No Cumplido'. NUNCA uses 'aplicable: false' (N/A) para excusar un mal saludo o tono.""",
    
     "etiqueta_qm": """REGLA 'QM': Cualquier item con una 'key' que contenga 'etiqueta_qm' (por ejemplo 'etiqueta_qm_entrada') DEBE SER MARCADO SIEMPRE como 'aplicable: false' cuando la llamada no es una llamada de Calidad/Quality Monitoring (QM).""",
   
    "tiempo_respuesta": """REGLA DE BLOQUEO 'Tiempo de Respuesta' (Entrada vs Salida):
    1. ANALIZA EL ORIGEN DE LA LLAMADA:
       - ¿Es llamada de SALIDA (el asesor marca al cliente, se escucha tono de llamada)? -> BLOQUEO POSITIVO.
       - ¿Es llamada de ENTRADA (el cliente marca y el asesor contesta)? -> ENTONCES APLICA la medición de 5 segundos.
    2. INSTRUCCIÓN OBLIGATORIA:
       - Si es SALIDA: Tu respuesta DEBE SER 'ok': true y 'aplicable': true.
         (IMPORTANTE: Marca 'aplicable': true para que aparezca como CUMPLIDO/VERDE. En evidencia escribe: 'Llamada de salida - Cumplimiento automático').
       - Si es ENTRADA: Evalúa rigurosamente los 5 segundos.""",

     "CAPACITACION": """REGLA BLINDADA 'Capacitación - Entrada vs Salida':
    1. DETERMINA EL TIPO DE LLAMADA:
       - Si el CLIENTE llama al asesor -> Es ENTRADA (Inbound).
       - Si el ASESOR llama al cliente -> Es SALIDA (Outbound).
    2. SI ES LLAMADA DE ENTRADA:
       - Evalúa la sección 'Dominio y manejo de la información - Entrada'. MANTÉN los pesos originales (incluyendo etiqueta_qm = 5)
       - ANULA la sección 'Dominio y manejo de la información - Salida': Para TODOS los items de esta sección de salida, DEBES responder: 'aplicable': false Y 'peso': 0.
    3. SI ES LLAMADA DE SALIDA:
       - Evalúa la sección 'Dominio y manejo de la información - Salida'. MANTÉN los pesos originales (incluyendo etiqueta_qm = 5)
       - ANULA la sección 'Dominio y manejo de la información - Entrada': Para TODOS los items de esta sección de entrada, DEBES responder: 'aplicable': false Y 'peso': 0.
    IMPORTANTE: Es obligatorio poner 'peso': 0 en la sección ANULADA para que no sume puntos al score final. La sección activa SÍ debe sumar puntos (mantener pesos).""",

    "SE_CONFIRMA_SEGUIMIENTO_CHAT": """REGLA BLINDADA 'Seguimiento Chat' (Administrativo NA=4):
    Este item es EXCLUSIVAMENTE ADMINISTRATIVO.
    1. NO busques evidencia en el audio.
    2. TU RESPUESTA OBLIGATORIA ES: 'aplicable': false.
    3. MANTÉN el peso original (ej. 'peso': 4).""",

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

     "INFO_CORRECTA_AGENTE": """REGLA BLINDADA 'Info Correcta Agente': Este ítem está DESACTIVADO administrativamente. TU RESPUESTA OBLIGATORIA ES: 'ok': true, 'aplicable': false. (IMPORTANTE: Debes marcar 'ok': true para evitar que el sistema anule la calificación por error). No evalúes el audio para este punto.""",

     "CUMPLE_REGULACIONES_KYC": """REGLA BLINDADA 'Cumple Regulaciones KYC': Este ítem está DESACTIVADO administrativamente. TU RESPUESTA OBLIGATORIA ES: 'ok': true, 'aplicable': false. (IMPORTANTE: Debes marcar 'ok': true para no anular el score por error). No evalúes el audio para este punto.""",

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

     "SE_DAN_LINEAMIENTOS_FRAUDE": """REGLA DE CONTEXTO 'Lineamientos de Fraude':
    1. FILTRO DE TEMA:
       - ¿La llamada es solo operativa (cancelar folio, liberar envío, verificar estatus) sin que se mencione o trate un riesgo activo -> ENTONCES NO APLICA ('aplicable': false).
    2. CONDICIÓN DE ACTIVACIÓN (SOLO SI):
       -EN la llamada se está tratando un tema de POSIBLE FRAUDE, EXTORSIÓN, SOSPECHA, SEGURIDAD o se detecta vulnerabilidad en el cliente.
    Si no se cumplen estas condiciones exactas, marca 'aplicable': false para proteger el score.""",

     "TIEMPO_DE_RESOLUCION_90_DIAS": """REGLA BLINDADA 'Tiempo de Resolución 90 días' (Crítico):
  - FILTRO DE BLOQUEO INMEDIATO (Si ocurre algo de esto, TU RESPUESTA DEBE SER 'ok: true', 'aplicable: false'):
    1. ¿La llamada es de SALIDA (Outbound)? -> BLOQUEAR (No aplica, aunque digan reporte).
    2. ¿Es un ENVÍO A CUENTA o DEPÓSITO BANCARIO, ESTA RETENIDO, EN VERIFICACIÓN, RECHAZADO, CANCELADO? -> BLOQUEAR (No aplica), En depósitos a cuenta NUNCA aplica el plazo de 90 días.
    3. ¿Es una COORDINACIÓN, corrección de folio, corrección de datos del beneficiario, desbloqueo o error de captura? -> BLOQUEAR (No aplica).
    4. ¿El envío está DISPONIBLE (aunque la tienda no quiera pagar o tenga problemas técnicos)? -> BLOQUEAR (No aplica).
    5. ¿Es cierre de caso o notificación de resolución, Notificación de Pagador o ya mandaron comprobante? -> BLOQUEAR (No aplica).
    6. ¿Es un CAMBIO DE ESTATUS, solicitud de cancelación, rechazo, envío retenido o no liberado? -> BLOQUEAR (No aplica).
    7. ¿El asesor ofrece un 'REPORTE DE VERIFICACIÓN', 'REPORTE DE ESTATUS' o 'SOLICITUD DE RASTREO'? -> BLOQUEAR (NA). Esto es distinto a una investigación de pago.
  - IMPORTANTE: En los casos anteriores (puntos 1-7), los asesores pueden usar la frase 'voy a levantar Reporte'. IGNORA esa frase si cae en el filtro de bloqueo.
  - CONDICIONES DE ACTIVACIÓN (EVALÚA SI CUMPLE TODO):
    1) La llamada es de ENTRADA (Inbound) de consumidores, es decir clientes o beneficiarios.
    2) El cliente reporta que el beneficiario NO COBRÓ/RECIBIÓ el dinero.
    3) El asesor indica explícitamente que debe LEVANTAR UN REPORTE o INICIAR INVESTIGACIÓN DE PAGO.
    * Llamada de ENTRADA + Dinero PERDIDO/NO APARECE/NO COBRADO + Se LEVANTA UN REPORTE o INICIA INVESTIGACIÓN DE PAGO.
  - REGLA DE ORO (DEFAULT): Ante cualquier duda entre 'Coordinación' u otros motivos y estos casos, si NO se cumplen las condiciones exactas, ASUME que NO APLICA (ok: true, aplicable: false). Si escuchas "Depósito", "Cuenta", "Banco", "BBVA" o similar, la regla se desactiva AUTOMÁTICAMENTE.
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
        "tiempo_respuesta",
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
        "SE_DAN_LINEAMIENTOS_FRAUDE",
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
        "SE_CONFIRMA_SEGUIMIENTO_CHAT"
        "etiqueta_qm",
    ],

    "Ventas telefónicas": [
        "DERECHOS_DE_CANCELACION",
        "ENCUESTA_MAXI",
        "etiqueta_qm",

    ],
}

KEYS_ADMINISTRATIVAS = [
    # --- Comunes / Transversales ---
    "etiqueta_qm",
    "notas_correctas_corporate",
    "notas_corporate",
    "info_correcta_agente",      # Cheques, Cobranza
    "cumple_regulaciones_kyc",   # Cumplimiento
    "info_correcta",             # Cumplimiento, Servicio al cliente

    # --- Administración de agencias ---
    "actualizacion_formas_pago",
    "actualizacion_direccion",
    "envio_copia_contratos",
    "revision_contrato_cheques",
    "aumento_limite_escaner",
    "validacion_fincen",
    "actualizacion_w9",
    "activacion_tdd",
    "status_subcuentas",
    "seguimiento_fresh",

    # --- Cobranza ---
    "documenta_compromiso_pago",

    # --- Cheques ---
    "ajuste_cheque_exitoso",
    "gestion_ticket_fresh",
    "liberacion_cheque_correcta",
    "envio_carta_rechazo",

    # --- Cumplimiento ---
    "documentacion_corporate",

    # --- BSA Monitoring ---
    "se_da_seguimiento_consumidor",

    # --- Agent Oversight ---
    "revision_agencia",
    
    # --- Ventas Internas (Bienvenida) ---
    "se_carga_info_corporate",
    "se_confirma_seguimiento_chat",

    # --- Ventas Internas (Ajustes) ---
    "se_realiza_ajuste_agencias_adicionales",
    "se_comparte_info_chat_busqueda",
    "se_llena_formato_prospecto_completo",

    # --- Soporte técnico ---
    "creacion_ticket_fresh",
    "activacion_usuarios",
    "adjuntar_evidencia_fresh",
    "activacion_permisos",

    # --- Prevención de fraudes ---
    "se_llena_reporte_fraude",
    "se_adjunta_evidencia",
    "se_agrega_a_lista_restrictiva",

    # --- Servicio al cliente ---
    "genera_ticket_fresh",
    "seguimiento_ticket",
    "escala_entidad_correcta",
    "llamadas_seguimiento",
    "nota_ticket_fresh"
]


