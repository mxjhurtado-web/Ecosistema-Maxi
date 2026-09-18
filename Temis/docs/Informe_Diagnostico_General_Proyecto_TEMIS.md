# Informe Diagnóstico General y Análisis de Procesos — Proyecto TEMIS

**TEMIS PROCESS SUITE | INFORME DIAGNÓSTICO & ANÁLISIS DE EFICIENCIA OPERATIVA**
- **Iniciativa:** Proyecto TEMIS (BPMN Suite & Governance) | **Código:** TEMIS-GOV-2026-V1
- **Sponsor:** Dirección de Operaciones & Tecnología | **Project Lead:** Ing. Mario Hurtado
- **Periodo Oficial:** 16 Enero 2026 – 04 Diciembre 2026 | **Estatus:** Línea Base Oficial Aprobada

---

## 1. Introducción y Contexto Estratégico
En el marco de la transformación digital y optimización continua de operaciones en **Maxi Send / Ecosistema Orbi**, el Departamento de Innovación y Procesos llevó a cabo una exhaustiva auditoría diagnóstica sobre las prácticas, herramientas y flujos de trabajo empleados para el levantamiento, diagramación y documentación de políticas y procedimientos corporativos.

El detonante principal de esta iniciativa radica en la **insostenibilidad financiera y operativa de mantener licencias SaaS comerciales de terceros (específicamente Lucidchart de Lucid Software Inc.)**, las cuales representan un costo recurrente en dólares por usuario sin ofrecer integración con los sistemas internos de la empresa (*Chronos, Freshdesk, Bria, WhatsApp*), ni sincronización automática con los manuales de procedimientos exigidos por auditoría y cumplimiento.

El presente informe sintetiza los hallazgos del estado actual (AS-IS), cuantifica los puntos de dolor que afectan la productividad de los analistas y define la arquitectura de la solución soberana TEMIS (TO-BE).

---

## 2. Diagnóstico del Estado Actual (AS-IS) y Puntos de Dolor (Pain Points)

1. **Pain Point 1: Drenaje Financiero por Licenciamiento SaaS de Lucidchart:**
   La organización erogaba pagos recurrentes anuales por licencias "per-seat" de Lucidchart. Al ser una herramienta genérica, gran parte de las cuentas se mantenían subutilizadas o se requerían compras adicionales para nuevos analistas, elevando el costo total de propiedad (TCO) sin generar propiedad intelectual interna.
2. **Pain Point 2: Ruptura Operativa y Retrabajo Extremo entre Diagramas y Word:**
   El analista dibuja un diagrama de flujo en Lucidchart o Visio y posteriormente tiene que "volver a redactar" manualmente un documento en Microsoft Word de 15 a 30 páginas para explicar cada paso. Este proceso desconectado consume entre 20 y 40 horas por proceso y genera graves discrepancias entre lo que dice el diagrama y lo que dice el manual.
3. **Pain Point 3: Falta de Estandarización en Simbología y Metadatos de Sistemas:**
   Cada analista empleaba estilos, colores y formas arbitrarias. En los diagramas no se especificaba con precisión técnica en qué sistema de software se realizaba la acción (ej. *Chronos, Freshdesk*) ni por qué canal de comunicación (ej. *WhatsApp, Bria, Correo*), provocando confusiones operativas en los usuarios finales.
4. **Pain Point 4: Barrera de Entrada y Complejidad para Analistas de Negocio:**
   Construir un flujo complejo directamente en un lienzo gráfico en blanco requiere habilidades avanzadas de diseño. Los analistas de negocio prefieren capturar la información en tablas estructuradas (SIPOC), pero carecían de una herramienta que convirtiera esa tabla en un diagrama formal en 1 clic.
5. **Pain Point 5: Ausencia de Control de Calidad y Riesgo de Procesos Inconclusos:**
   En las herramientas tradicionales no existe validación lógica. Con frecuencia, los diagramas aprobados contenían compuertas de decisión (rombos) sin rama de salida "No", actividades huérfanas o procesos sin punto final, los cuales no eran descubiertos hasta auditorías regulatorias o fallas operativas.
6. **Pain Point 6: Fragmentación Documental y Falta de Repositorio Central:**
   Los archivos de diagramas (`.lucid`, `.vsdx`, `.drawio`) quedaban dispersos en carpetas locales o cuentas personales de diseñadores, impidiendo un control centralizado de versiones y dificultando el respaldo corporativo en Google Workspace Shared Drive.

---

## 3. Perfiles de Usuario Afectados (Personas de Procesos)
- **Perfil A: Analista de Procesos y Métodos:** Profesional responsable de mapear la operación. *Dolor:* Pasa el 70% de su tiempo formateando cajas en herramientas gráficas y redactando textos repetitivos en Word.
- **Perfil B: Líder de Operaciones y Dueño de Proceso (PM/PO):** Responsable de la eficiencia de su área. *Dolor:* Falta de visibilidad sobre los sistemas que soportan cada paso del flujo y demoras de semanas en recibir un manual actualizado.
- **Perfil C: Auditor de Calidad y Cumplimiento:** Encargado de vigilar el apego normativo. *Dolor:* Dificultad para auditar manualmente diagramas gigantescos y encontrar caminos ciegos o inconsistencias lógicas.
- **Perfil D: Asesor de Operaciones / Usuario Final:** Ejecuta la tarea en ventanilla o atención al cliente. *Dolor:* Recibe procedimientos desactualizados o diagramas confusos que no indican qué pantalla de Chronos abrir.

---

## 4. Mapa de Experiencia Actual (Customer Journey Map de Documentación)

| Etapa del Proceso | Objetivo del Usuario | Acción Realizada (AS-IS) | Punto de Contacto | Nivel de Fricción | Oportunidad TEMIS |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **1. Captura de Requerimientos** | Recopilar pasos del proceso con el área operativa. | Entrevistas y notas en Excel o blocs de notas. | Reuniones / Excel | Medio | Plantilla SIPOC estructurada interactiva. |
| **2. Diagramación Visual** | Crear el flujo gráfico de decisión y tareas. | Arrastrar cajas manualmente en Lucidchart. | Lucidchart SaaS | Alto (Licencia) | Generador automático Bézier desde SIPOC. |
| **3. Redacción del Manual** | Generar el documento oficial de políticas. | Redactar 20 páginas en Word desde cero. | MS Word local | Crítico (20-40h) | Redacción automática con Gemini 2.5 Flash. |
| **4. Auditoría de Calidad** | Verificar que el flujo no tenga errores lógicos. | Revisión visual manual regla por regla. | Revisión por pares | Alto (Errores) | Auditor IA en tiempo real (Score 0-100). |
| **5. Aprobación & Firma** | Obtener sign-off del Sponsor y Líder de Área. | Envío de PDFs por correo con firmas manuales. | Correo electrónico | Medio | Módulo de Gobernanza y Actas integrado. |
| **6. Publicación y Respaldo** | Almacenar versión oficial y compartir al equipo. | Guardado en carpetas locales o nubes personales. | Discos locales | Alto (Pérdida) | Respaldo automático en Google Shared Drive con SA. |

---

## 5. Matriz Comparativa: Modelo Tradicional (AS-IS) vs Suite TEMIS (TO-BE)

| Dimensión / Capacidad | Modelo Tradicional (AS-IS) | Suite TEMIS (TO-BE) | Impacto / Beneficio |
| :--- | :--- | :--- | :--- |
| **Costo Financiero de Software** | Pago recurrente anual en USD por licencias de Lucidchart. | Cero costo de licenciamiento. Software propietario soberano. | **Ahorro del 100% en gasto recurrente SaaS.** |
| **Tiempo de Documentación** | 20 a 40 horas por proceso entre diagramar y redactar en Word. | Menos de 2 horas por proceso (Reducción del 80-90%). | **Multiplica x5 la capacidad del equipo.** |
| **Método de Entrada** | Lienzo gráfico en blanco con dibujo manual caja por caja. | Matriz SIPOC Six Sigma con autocompletado inteligente Gemini IA. | Accesible para cualquier perfil de analista. |
| **Generación Gráfica** | Alineación manual propensa a líneas cruzadas y desorden. | Ruteo perimetral automático con curvas cúbicas SVG Bézier. | Estandarización y estética impecable. |
| **Redacción de Políticas** | Transcripción manual en Word sujeta a contradicciones. | Generación automática en texto corrido estructurado (1.0..N). | Consistencia 100% entre diagrama y texto. |
| **Auditoría de Calidad** | Revisión manual subjetiva y tardía tras publicación. | Auditor IA instantáneo con calificación 0-100 y recomendaciones. | Cero procesos inconclusos en producción. |
| **Integración Tecnológica** | Herramientas aisladas sin noción de sistemas de la empresa. | Etiquetas nativas para *Chronos, Freshdesk, Bria, WhatsApp*. | Claridad absoluta para TI y Operaciones. |
| **Almacenamiento & Backup** | Archivos dispersos en discos duros locales sin control. | Catálogo en Menú Archivo y respaldo en Shared Drive con SA. | Seguridad, control de versiones y gobierno. |

---

## 6. Conclusiones y Plan de Habilitación
El diagnóstico confirma que la Suite TEMIS erradica las ineficiencias del modelo tradicional y elimina los costos de licencias de Lucidchart, consolidando una plataforma integral de modelado, redacción y gobierno de procesos corporativos.
