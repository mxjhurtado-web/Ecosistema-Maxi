# Plan de Pruebas de API: Microservicio BFF Checks (Hermes 2)
**Proyecto:** Hermes 2 - Microservicio BFF Checks (`/api/checks/`)  
**Fecha:** Noviembre 2026  

---

## 🎯 1. Propósito y Objetivos de Calidad

El presente documento establece el plan técnico y operativo para evaluar de forma exhaustiva el microservicio **BFF Checks** (`/api/checks/`), componente central que orquesta las operaciones de cambio y cobro de cheques en ventanilla para el sistema **Hermes 2** de Maxi Remesas.

El propósito de este plan de pruebas no se limita a verificar códigos de respuesta exitosos, sino a garantizar que el sistema cumpla con los estándares operativos reales del negocio:

1. **Exactitud Funcional:** Comprobar que el sistema calcule con precisión matemática las comisiones (*fees*) y los montos totales según el tipo de cheque, sin cobrar de más ni de menos.
2. **Resiliencia y Robustez (No Romperse):** Asegurar que cuando el frontend, el cajero o un usuario envíe datos incompletos, montos negativos o valores fuera de rango, el servidor responda con mensajes y códigos de error controlados (`400 Bad Request` o `422 Unprocessable Entity`), **garantizando que jamás ocurra una caída del servidor (`500 Internal Server Error`)**.
3. **Seguridad y Blindaje de Datos:** Validar que los mecanismos de autenticación protejan las operaciones financieras y que exista un **estricto aislamiento entre agencias**, impidiendo que una agencia pueda consultar, modificar o cobrar cheques de otra agencia.
4. **Estabilidad y Tiempos de Respuesta (Performance):** Verificar que la latencia del microservicio permita una atención ágil en ventanilla, sin provocar demoras en las filas de clientes.
5. **Trazabilidad y Demostración de Defectos:** En caso de que se detecte una falla, proporcionar al equipo de desarrollo la evidencia técnica exacta y reproducible (URL, headers, payload enviado y respuesta del servidor) para facilitar su corrección inmediata.

---

## 🗺️ 2. Alcance y Mapeo de Endpoints

El microservicio se compone de **31 endpoints** (29 de lógica de negocio y 2 de monitoreo de infraestructura), organizados en 5 grupos operativos:

| Grupo Operativo | Endpoints Principales | Verbos | Descripción Funcional |
| :--- | :--- | :---: | :--- |
| **00. Sistema & Monitoreo** | `/healthcheck`, `/version` | `GET` | Verificación de disponibilidad del servicio y versión de despliegue. |
| **01. Catálogos de Cheques** | `/check-cashing/types`, `/check-sources`, `/issuer-relationships` | `GET` | Consulta de catálogos base (tipos de cheque, procedencia y relaciones con el librador). |
| **02. Agente, Comisiones y Límites** | `/fees/agent/{id_agent}`, `/agents/{id_agent}/check_limit`, `/configuration/fees/agent` | `GET`, `POST`, `PUT`, `DELETE` | Consulta de comisiones por agencia, límites de licencia y administración de tarifas (`AgCustFees`). |
| **03. Consultas e Historial** | `/batch`, `/progress`, `/{id_check}`, `/receipt/{id_check}`, `/customer/.../history`, `/issuer/.../history` | `GET` | Consulta de cheques individuales, progreso de lotes en DynamoDB, recibos e historial de clientes y libradores. |
| **04. Procesamiento y Ciclo de Vida** | `/totals/calculate`, `/check-cashing/totals`, `/single/validation`, `/single/process`, `/upload_image`, `/giact`, `/status` | `POST`, `PATCH`, `DELETE` | Validación en listas de denegación (OFAC), cálculo de totales, subida de imágenes a S3, verificación GIACT y procesamiento final. |

---

## 🔍 3. Criterios y Dimensiones de Evaluación

Para asegurar una cobertura completa, cada endpoint se evalúa bajo un marco estandarizado de **5 dimensiones de calidad**:

```
┌────────────────────────────────────────────────────────────────────────┐
│               EVALUACIÓN INTEGRAL DEL MICROSERVICIO                    │
├───────────────────────────────────┬────────────────────────────────────┤
│ 1. FUNCIONALIDAD Y REGLAS         │ Cálculo matemático de comisiones,  │
│                                   │ topes y límites por tipo de cheque.│
├───────────────────────────────────┼────────────────────────────────────┤
│ 2. ESTRUCTURA Y CONTRATO          │ Respuestas uniformes bajo formato: │
│                                   │ { status, message, data }.         │
├───────────────────────────────────┼────────────────────────────────────┤
│ 3. RESILIENCIA Y MANEJO DE ERRORES│ Códigos 400 y 422 controlados ante │
│                                   │ datos malos. CERO caídas 500.      │
├───────────────────────────────────┼────────────────────────────────────┤
│ 4. SEGURIDAD Y MULTI-AGENCIA      │ Aislamiento estricto: la Agencia A │
│                                   │ no puede ver datos de la Agencia B.│
├───────────────────────────────────┼────────────────────────────────────┤
│ 5. TIEMPOS DE RESPUESTA (SLAs)    │ Evaluación estadística p95 sobre   │
│                                   │ 30 muestras continuas.             │
└───────────────────────────────────┴────────────────────────────────────┘
```

### A. Funcionalidad y Reglas de Negocio
* **Objetivo:** Comprobar que las fórmulas financieras se apliquen con total precisión.
* **Criterio de Evaluación:**
  * Se evalúan los 3 tipos de cheques principales: **Nómina (Tipo 1)**, **Personal (Tipo 2)** y **Gobierno (Tipo 3)**.
  * Se prueban valores representativos (desde micro-cheques de `$15.00` hasta montos límite de `$2,800.00`).
  * Se analizan **valores de frontera** donde cambian las tarifas (un centavo antes del umbral `U - 0.01`, en el umbral exacto `U`, y un centavo después `U + 0.01`) para comprobar que los operadores de comparación (`<` vs `<=`) no cobren tarifas incorrectas.
  * Regla base: La comisión (`fee`) debe ser mayor a cero y el total a pagar al cliente debe ser exactamente `monto - comisión`.

### B. Estructura y Contratos de Respuesta
* **Objetivo:** Garantizar que el frontend de Hermes 2 reciba siempre una estructura predecible que no rompa la interfaz gráfica.
* **Criterio de Evaluación:**
  * Todas las respuestas exitosas deben cumplir con el envoltorio estándar:
    ```json
    {
      "status": 200,
      "message": "sucessfull ",
      "data": { ... }
    }
    ```
  * Los campos dentro de `data` deben coincidir en nombre y tipo de dato con la especificación de arquitectura. *(Excepción documentada: `/version` devuelve directamente `{ "version": string }`)*.

### C. Resiliencia y Manejo de Errores (Inputs Negativos)
* **Objetivo:** Poner a prueba la robustez del microservicio ante datos defectuosos o maliciosos.
* **Criterio de Evaluación:**
  * **Montos inválidos:** Envío de montos negativos (`-50.00`), monto cero (`0.00`) o caracteres de texto en campos numéricos en `/totals/calculate` ➔ El sistema debe rechazar la petición con código `422 Unprocessable Entity` o `400 Bad Request`.
  * **Datos incompletos:** Envío de cuerpos JSON vacíos (`{}`) o parámetros requeridos omitidos en `/single/validation` ➔ Rechazo con `422`.
  * **Formatos incorrectos:** Routing number bancario con menos de 9 dígitos ➔ Rechazo con `422`.
  * **Identificadores inexistentes:** Consulta con `id_agent` o `id_check` inexistentes ➔ Respuesta controlada `404 Not Found` o `400`.
  * **Regla estricta:** Ninguna de estas peticiones debe provocar un error `500 Internal Server Error`, ni exponer trazas de código o nombres de tablas de base de datos en la respuesta.

### D. Seguridad y Control de Acceso
* **Objetivo:** Blindar el sistema contra operaciones no autorizadas y fugas de información.
* **Criterio de Evaluación:**
  * **Sin Autenticación:** Peticiones a endpoints transaccionales omitiendo el header `authorizer` ➔ Deben responder inmediatamente con `401 Unauthorized`.
  * **Token Inválido o Expirado:** Envío de firmas corruptas o vencidas ➔ Rechazo con `401 Unauthorized`.
  * **Aislamiento Multi-Agencia (Prueba Crítica):** Se emite una petición con las credenciales de la **Agencia A**, pero solicitando consultar o procesar cheques con el `id_agent` de la **Agencia B** ➔ El sistema debe responder con `403 Forbidden` o `404 Not Found`, **impidiendo bajo cualquier circunstancia el acceso a información de otra agencia**.
  * **Sanitización de Consultas:** Pruebas con secuencias de inyección SQL de lectura (`' OR '1'='1`) en parámetros de búsqueda ➔ El sistema debe parametrizar la consulta sin fallar con error 500 y sin devolver registros indebidos.

### E. Tiempos de Respuesta y Estabilidad (Performance)
* **Objetivo:** Evitar que demoras del backend impacten la atención en ventanilla.
* **Criterio de Evaluación:**
  * En lugar de mediciones aisladas (que pueden fallar por ruido de red o arranques en frío), se descartan las primeras 3 llamadas de calentamiento y se calculan las métricas sobre **30 muestras consecutivas**, evaluando el **Percentil 95 (p95)**:
    * 🟢 **Catálogos y Monitoreo:** p95 `< 300 ms` (datos ligeros en caché/memoria).
    * 🟡 **Consultas Operativas a Base de Datos:** p95 `< 800 ms` (lecturas relacionales e índices).
    * 🟠 **Cálculos y Reglas de Negocio:** p95 `< 1,000 ms` (validaciones de listas y algoritmos).
    * 🔴 **Procesamiento y Servicios Externos:** p95 `< 1,800 ms` (GIACT, subida de imágenes a S3 y almacenamiento transaccional).

---

## 🛠️ 4. Metodología de Ejecución: ¿Cómo se Realizan las Pruebas?

Para asegurar que las pruebas sean ordenadas y puedan ser ejecutadas o replicadas por cualquier integrante del equipo de calidad, se establece un flujo técnico en cuatro etapas:

```
    ┌────────────────────────────────────────────────────────┐
    │ 1. REFERENCIA: SWAGGER / OPENAPI 3.1.0                │
    │    - Fuente de verdad de rutas, parámetros y contratos.│
    └───────────────────────────┬────────────────────────────┘
                                │
                                ▼
    ┌────────────────────────────────────────────────────────┐
    │ 2. BANCO INTERACTIVO: POSTMAN DESKTOP                  │
    │    - Entorno: BFF_Checks_Dev.postman_environment.json │
    │    - Colección: BFF_Checks.postman_collection.json     │
    │    - Pruebas manuales (Send) y por lotes (Runner)      │
    └───────────────────────────┬────────────────────────────┘
                                │
                                ▼
    ┌────────────────────────────────────────────────────────┐
    │ 3. AUTOMATIZACIÓN CLI: NEWMAN                          │
    │    - Ejecución desatendida en terminal PowerShell      │
    │    - Generación de reportes interactivos HTML          │
    └───────────────────────────┬────────────────────────────┘
                                │
                                ▼
    ┌────────────────────────────────────────────────────────┐
    │ 4. EVIDENCIA DE HALLAZGOS                              │
    │    - Si falla: URL + Payload + Error exacto entregado  │
    │      a desarrollo para corrección inmediata.           │
    └────────────────────────────────────────────────────────┘
```

### Paso 1: Consulta del Contrato en Swagger
Se utiliza la documentación de desarrollo (`https://hermes2-api-dev.mylabs.mx/api/checks/documentation/swagger`) como referencia oficial. De aquí se extraen las rutas exactas, los parámetros requeridos de URL o query, los encabezados de seguridad (`authorizer`) y los esquemas JSON esperados.

### Paso 2: Configuración y Entrada de Datos en Postman Desktop
* **Variables Parametrizadas:** Se utiliza el entorno `BFF_Checks_Dev.postman_environment.json` para gestionar valores dinámicos (`baseUrl`, `id_agent`, `authorizer_token`), evitando quemar direcciones o datos fijos en las peticiones.
* **Ingreso de Payloads:** Para los endpoints de tipo `POST` y `PUT` (cálculos, validaciones y altas), los datos de prueba (montos, números de cheque, datos del librador) se capturan en la pestaña **`Body`** en formato `raw / JSON`.
* **Modos de Ejecución:**
  * **Exploración Individual:** El tester abre una petición, ajusta los valores y presiona **`Send`**, revisando en la pestaña **`Test Results`** que todas las aserciones pasen en verde.
  * **Ejecución por Lotes (Collection Runner):** Se da clic derecho sobre una carpeta operativa completa (por ejemplo, *01. Catálogos*) y se ejecuta en secuencia configurando una pausa (*delay*) de `500 ms` entre peticiones para proteger el servidor de sobrecargas.

### Paso 3: Automatización y Reportería por Consola con Newman CLI
* Las mismas colecciones validadas en Postman se ejecutan desde la terminal de Windows mediante **Newman**.
* Este paso permite corridas desatendidas sin interfaz gráfica y compila automáticamente un **Reporte Ejecutivo Interactivo en HTML** (`htmlextra`). Este reporte incluye gráficos de pastel con porcentaje de éxito, barras de tiempo de respuesta de cada llamada y el desglose de cada aserción evaluada.

### Paso 4: Evolución Hacia la Suite Automatizada del Equipo (Python / pytest)
Para las dimensiones que requieren parametrización masiva de datos (los 6 tiers de comisiones y casos de frontera), la suite se integra de forma modular con **Python** utilizando el framework **`pytest`** dentro de las herramientas internas del equipo (`Maxx_C 2.0`). Esto permite:
* Reutilizar los datasets en archivos `.json` mediante `@pytest.mark.parametrize`.
* Habilitar **pruebas híbridas (E2E)**: el agente valida primero la salud de la API en milisegundos y, solo si la API responde correctamente, Playwright procede a interactuar con la interfaz gráfica de Hermes 2.

---

## 📋 5. Prerrequisitos y Datos Necesarios para la Ejecución

Para llevar a cabo las pruebas de forma consistente y sin interrupciones, se requiere contar con los siguientes elementos:

1. **Conectividad:** Acceso activo a la red de desarrollo mediante la **VPN corporativa de Maxi LLC**.
2. **Ambiente de Pruebas:** Disponibilidad y estabilidad del servidor `https://hermes2-api-dev.mylabs.mx`.
3. **Herramientas de Trabajo:**
   * Postman Desktop (versión 11 o superior).
   * Node.js y paquetes globales: `newman` y `newman-reporter-htmlextra`.
   * Entorno virtual de Python con `pytest` y `requests`.
4. **Datos Semilla (Test Data):**
   * **Agencia de Prueba A (Principal):** Agencia asignada para pruebas operativas (ej. `1242` o `0020-TX`).
   * **Agencia de Prueba B (Secundaria):** Requerida exclusivamente para validar que no exista cruce indebido de información entre agencias.
   * **IDs de Referencia:** Identificadores válidos en desarrollo de cliente (`id_customer`) y de cheque (`id_check`) para consultas de historial.
5. **Definiciones del Negocio:**
   * Tabla oficial y confirmada por Producto/Finanzas con las reglas de comisión por tipo de cheque (mínimo fijo, porcentaje, tope máximo y regla de redondeo).
   * Confirmación técnica de que el servicio de validación bancaria **GIACT** y el almacenamiento en **AWS S3** cuenten con entornos de simulación (*sandbox*) que no generen costos ni afecten recursos de producción.

---

## 📊 6. Criterios de Aceptación y Documentación de Defectos

### Criterios de Salida (Aprobación de Pruebas)
Un endpoint o grupo operativo se considera aprobado cuando cumple las siguientes condiciones:
* El **100% de las pruebas funcionales de Happy Path** responden con el código de estado esperado y el contrato de envoltorio `{ status, message, data }`.
* El **100% de las pruebas de seguridad y aislamiento** rechazan peticiones sin token o con intentos de cruce entre agencias.
* Todas las pruebas negativas devuelven códigos de cliente controlados (`400` o `422`), con **cero incidencias de error `500`**.
* Las mediciones de latencia se mantienen dentro de los umbrales p95 establecidos.

### Procedimiento de Documentación de Defectos
Cuando una prueba no cumpla con los criterios esperados, el equipo de calidad no reportará observaciones vagas; se generará un reporte técnico detallado extraído directamente de la evidencia de Newman o pytest:

```
[REPORTE DE DEFECTO TÉCNICO]
- Endpoint Afectado:   POST /api/checks/checks/totals/calculate
- Severidad:           Crítica / Mayor / Menor
- Escenario:           Cálculo de comisión con monto de frontera en Cheque de Nómina
- URL Completa:        https://hermes2-api-dev.mylabs.mx/api/checks/checks/totals/calculate
- Headers Enviados:    Content-Type: application/json | authorizer: [Token de Agencia A]
- Payload Enviado:     { "checkAmount": 999.99, "idAgent": 1242, "idCheckType": 1 }
- Resultado Esperado:  Status 200 OK | data.fee: 15.00 | data.total: 984.99
- Resultado Obtenido:  Status 500 Internal Server Error (o comisión incorrecta de 25.00)
- Evidencia Adjunta:   Reporte HTML interactivo con traza completa y tiempo de respuesta.
```

Este formato garantiza que cualquier desarrollador pueda tomar la petición, replicarla en su propio entorno en menos de un minuto y aplicar el parche correctivo con total claridad sobre la falla detectada.
