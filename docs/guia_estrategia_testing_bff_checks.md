# 🛡️ Guía Maestra: Estrategia de Testing para BFF Checks (Hermes 2)
**Proyecto:** Hermes 2 - Microservicio BFF Checks (Backend For Frontend)  
**Fecha:** Noviembre 2026  

---

## 🧭 1. Visión General y Propósito del Proyecto

En la arquitectura moderna de **Hermes 2**, el frontend (construido en Angular) no se comunica directamente con las decenas de servicios legados de Maxi (servicios SOAP en WCF, APIs en .NET, bases de datos SQL Server o tablas en DynamoDB). En su lugar, existe una capa intermedia llamada **BFF (Backend For Frontend)**.

El microservicio **BFF Checks** (`/api/checks/`) es el orquestador central de todas las operaciones relacionadas con cheques en ventanilla de agencias:
1. **Cobro y cambio de cheques (Check Cashing):** Validación del librador (Issuer), historial del cliente (Customer), consulta de listas negras (OFAC / DenyList).
2. **Validación bancaria:** Verificación de fondos y cuentas vía servicios externos como **GIACT**.
3. **Escaneo y almacenamiento de imágenes:** Subida de cheques escaneados al bucket AWS S3 (`hermes2-dev-temp-encrypt-bucket`) y registros en DynamoDB (`hermes2_batchchecks_dev`).
4. **Tarifas y comisiones:** Cálculo de comisiones por agencia y tipo de cheque (`AgCustFees`).
5. **Emisión de IRD y Recibos:** Generación de recibos de pago y procesamiento IRD (*Image Replacement Document*).

### 🎯 La Meta de Cobertura
En la hoja `Coverage` del documento `Unit Test BFF Checks.xlsx`, el microservicio de Checks se encuentra al **63% de cobertura**, mientras que la meta corporativa de Sistemas es alcanzar al menos el **90%+**.

Esta estrategia define cómo validar el **Happy Path (Status 200/201)** y la **Integridad de Contratos JSON** para los 29 endpoints mapeados, preparando el terreno para las pruebas negativas y de estrés.

---

## 🤝 2. La Cuadrilla Tecnológica (¿Cómo interactúan las herramientas?)

Para llevar a cabo este plan de manera profesional y nivel Senior, cada herramienta cumple una función específica dentro del ciclo de vida del testing:

```
    ┌────────────────────────────────────────────────────────┐
    │              1. CONTRATO ARQUITECTÓNICO               │
    │        Swagger / OpenAPI 3.1.0 (/openapi.json)         │
    └───────────────────────────┬────────────────────────────┘
                                │ (Define rutas, esquemas, tipos y parámetros)
                                ▼
    ┌────────────────────────────────────────────────────────┐
    │                 2. COPILOTO Y GENERADOR                │
    │              Claude / Anty (Pette) / Python             │
    └───────────────────────────┬────────────────────────────┘
                                │ (Genera colecciones, variables y scripts de aserción)
                                ▼
         ┌──────────────────────┴──────────────────────┐
         ▼                                             ▼
┌─────────────────────────────────┐         ┌─────────────────────────────────┐
│     3. BANCO DE PRUEBAS GUI     │         │   4. EJECUTOR CLI AUTOMATIZADO  │
│       Postman Desktop v12       │         │        Newman CLI (Node.js)     │
│  - Depuración manual visual     │         │  - Ejecución desatendida en CI  │
│  - Inspección de payloads/JSON  │         │  - Reportes ejecutivos HTML     │
│  - Ajuste fino de variables     │         │    (newman-reporter-htmlextra)  │
└────────────────┬────────────────┘         └────────────────┬────────────────┘
                 │                                           │
                 └──────────────────────┬────────────────────┘
                                        │ (Envían peticiones HTTP y evalúan respuestas)
                                        ▼
    ┌────────────────────────────────────────────────────────┐
    │                 5. TARGET: BFF CHECKS                  │
    │        https://hermes2-api-dev.mylabs.mx/api/checks    │
    └───────────────────────────┬────────────────────────────┘
                                │ (Orquesta llamadas hacia el backend)
                                ▼
         ┌─────────────────────────────────────────────┐
         │ 6. BACKENDS, LEGACY & BASES DE DATOS        │
         │ - SOAP Front Office V1 / V2 (WCF)           │
         │ - CheckServices & BriskService (.NET REST)  │
         │ - AWS S3 & DynamoDB (batch_dev)             │
         │ - SQL Server MaxiLog (192.168.5.10)         │
         └─────────────────────────────────────────────┘
```

### Roles de Cada Componente:

1. **Swagger / OpenAPI (`/api/checks/documentation`):**
   * Es la **fuente de la verdad**. Define qué rutas existen, qué métodos aceptan, qué headers requieren (`authorizer`), y cuál es la estructura exacta de entrada y salida.
2. **Postman Desktop:**
   * Es el **laboratorio interactivo**. Aquí importas la colección estructurada, pruebas peticiones individuales, ves el JSON formateado con colores, revisas los headers y ejecutas carpetas completas con el *Collection Runner*.
3. **Newman CLI:**
   * Es el **motor de automatización**. Corre las mismas colecciones de Postman pero directamente desde la terminal de Windows (`PowerShell`) sin abrir ninguna ventana. Permite generar reportes ejecutivos en HTML ultra detallados para mostrar a los líderes de proyecto.
4. **Claude / Anty (Pette):**
   * Es tu **asesor estratégico y generador técnico**. Anty analiza los contratos OpenAPI, construye los scripts de prueba en JavaScript para Postman, detecta discrepancias en los esquemas, genera datasets sintéticos y te asesora en las juntas técnicas.
5. **SQL Server (`MaxiLog`) y AWS:**
   * Es la **auditoría de persistencia**. Como te enseñó Ignacio en la reunión, una prueba no termina cuando el API responde 200; termina cuando verificamos que la transacción impactó correctamente en base de datos.

---

## 📦 3. Archivos Generados en tu Entorno

Los archivos listos para importar fueron generados en la carpeta `docs` de tu repositorio:

| Archivo | Ruta Completa | Descripción |
| :--- | :--- | :--- |
| **Colección Postman** | [BFF_Checks.postman_collection.json](file:///C:/Users/User/Ecosistema-Maxi/docs/BFF_Checks.postman_collection.json) | Colección con los 31 endpoints agrupados en 5 carpetas con pruebas automáticas integradas. |
| **Entorno Dev** | [BFF_Checks_Dev.postman_environment.json](file:///C:/Users/User/Ecosistema-Maxi/docs/BFF_Checks_Dev.postman_environment.json) | Variables de entorno (`baseUrl`, `authorizer_token`, `id_agent`, etc.). |
| **Especificación OpenAPI** | [openapi_bff_checks.json](file:///C:/Users/User/Ecosistema-Maxi/docs/openapi_bff_checks.json) | Especificación OpenAPI 3.1.0 completa descargada del servidor de desarrollo. |

---

## 🚀 4. Paso a Paso: Cómo Importar y Ejecutar en Postman Desktop

### Paso 1: Abrir Postman Desktop
1. Abre **Postman** desde tu acceso directo en el escritorio.
2. Asegúrate de estar en tu Workspace: **`Jose Hurtado's Workspace`**.

### Paso 2: Importar la Colección y el Entorno
1. En la esquina superior izquierda de Postman, haz clic en el botón **`Import`** (o presiona `Ctrl + O`).
2. Haz clic en **`files`** o arrastra los siguientes dos archivos directamente a la ventana de Postman:
   * `C:\Users\User\Ecosistema-Maxi\docs\BFF_Checks.postman_collection.json`
   * `C:\Users\User\Ecosistema-Maxi\docs\BFF_Checks_Dev.postman_environment.json`
3. Haz clic en **`Import`**.

### Paso 3: Activar el Entorno de Desarrollo
1. En la esquina superior derecha de Postman, ubica el selector de entornos (por defecto dice `No Environment`).
2. Haz clic en el menú desplegable y selecciona **`BFF Checks - Dev Environment`**.
3. Haz clic en el ícono del ojo (👁️) junto al selector para revisar que las variables estén activas:
   * `baseUrl`: `https://hermes2-api-dev.mylabs.mx`
   * `id_agent`: `1242`
   * `authorizer_token`: (Vacío o con el token JWT si la API lo requiere)

### Paso 4: Probar los Primeros Endpoints (Happy Path)
1. En la barra lateral izquierda, expande la colección **`BFF Checks - Hermes 2 (QA Automation Maxi LLC)`**.
2. Abre la carpeta **`00. Sistema & Health (Monitoreo)`**.
3. Selecciona **`[GET] Get Healthcheck`** y haz clic en el botón azul **`Send`**.
4. En la parte inferior, pestaña **`Test Results`**, verás que las 4 pruebas pasan en verde:
   * `PASS: Status code es 200 OK (o 201 Created)`
   * `PASS: Tiempo de respuesta dentro de SLA (< 3000ms)`
   * `PASS: Content-Type es application/json`
   * `PASS: Contrato Base BFF: Cumple envoltorio estándar {{ status, message, data }}`
5. Repite con **`[GET] Get Version`**.

### Paso 5: Correr una Carpeta Completa con Collection Runner
1. Haz clic derecho sobre la carpeta **`01. Catálogos & Check Cashing (GET)`**.
2. Selecciona **`Run folder`**.
3. En la pantalla del Runner:
   * Asegúrate de que el entorno sea **`BFF Checks - Dev Environment`**.
   * Establece un **Delay** de `500 ms` o `1000 ms` (para no saturar el servidor de desarrollo).
4. Haz clic en **`Run BFF Checks...`**.
5. Observa cómo todos los endpoints se ejecutan en secuencia y el panel muestra el resumen con 100% de aserciones aprobadas.

---

## 💻 5. Automatización con Newman CLI (Terminal de Comandos)

Newman permite ejecutar la misma colección desde la consola y generar reportes ejecutivos.

### Instalación de Newman y Reporter HTML Extra (Una sola vez)
Abre PowerShell o terminal y ejecuta:
```powershell
npm install -g newman newman-reporter-htmlextra
```

### Comando para Ejecutar las Pruebas en Consola
```powershell
cd C:\Users\User\Ecosistema-Maxi\docs
newman run BFF_Checks.postman_collection.json -e BFF_Checks_Dev.postman_environment.json --folder "01. Catálogos & Check Cashing (GET)" --reporters cli
```

### Comando para Generar el Reporte HTML Ejecutivo (`htmlextra`)
```powershell
cd C:\Users\User\Ecosistema-Maxi\docs
newman run BFF_Checks.postman_collection.json -e BFF_Checks_Dev.postman_environment.json --reporters cli,htmlextra --reporter-htmlextra-export ./Reporte_BFF_Checks.html --reporter-htmlextra-title "Reporte de Pruebas BFF Checks - QA Automation"
```
Este comando generará el archivo `Reporte_BFF_Checks.html` con gráficos interactivos, tiempos de respuesta de cada llamada y evidencia de contratos validados.

---

## 📈 6. Las 4 Etapas del Testing de APIs en Maxi LLC

Para llevar este proyecto al estándar Senior, avanzaremos en 4 etapas progresivas:

```
┌────────────────────────────────────────────────────────┐
│ ETAPA 1: HAPPY PATH (STATUS 200 / 201)                 │ ◄── [ACTUAL]
│ - Todas las rutas responden 200 OK con datos válidos   │
│ - Parámetros básicos y respuesta en SLA (< 3000ms)    │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ ETAPA 2: VALIDACIÓN DE CONTRATOS (SCHEMA VALIDATION)   │
│ - El envoltorio cumple { status, message, data }       │
│ - Cada campo de 'data' respeta tipos de OpenAPI        │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ ETAPA 3: PRUEBAS NEGATIVAS Y CASOS LÍMITE              │
│ - Enviar IDs inexistentes (404)                        │
│ - Enviar payloads con tipos erróneos (422)             │
│ - Peticiones sin autorización o token caducado (401)   │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ ETAPA 4: PRUEBAS DE ESTRÉS Y PERSISTENCIA (MAXILOG)    │
│ - Correr 50 iteraciones seguidas en Collection Runner  │
│ - Validar inserción en SQL Server MaxiLog (192.168.5.10)│
│ - Validar almacenamiento en S3 y DynamoDB              │
└────────────────────────────────────────────────────────┘
```

---

## 📋 7. Mapeo Completo de los 29 Endpoints de BFF Checks

A continuación se detalla la matriz de trazabilidad extraída de `Unit Test BFF Checks.xlsx` cruzada con la especificación OpenAPI:

| # | Verbo | Ruta (BFF Checks) | Servicio Legacy Subyacente | Objeto / Tabla | Desarrollador Resp. |
| :-: | :---: | :--- | :--- | :--- | :---: |
| **1** | `GET` | `/checks/fees/agent/{id_agent}` | Front Office V1 (SOAP) | `GetFeeChecks` | Gadiel |
| **2** | `GET` | `/checks/receipt/{id_check}` | Front Office V2 (SOAP) | `GetCheckReceipt` | Gadiel |
| **3** | `GET` | `/checks/process_ird` | CheckServices (REST) + AWS S3 | `ProcessIRD` / S3 bucket | Gadiel |
| **4** | `GET` | `/checks/progress` | DynamoDB | `batch_dev` / `hermes2_batchchecks_dev` | - |
| **5** | `GET` | `/checks/{id_check}` | CheckServices (REST) | `GetCheckById` | Gadiel |
| **6** | `POST` | `/checks/verification/pending` | CheckServices + DynamoDB | `SetIdcheckImagePending` | Gadiel |
| **7** | `POST` | `/checks/single/validation` | CheckServices + OFAC + SQL | `AccountCautionNotes`, `DenyList` | Gadiel / Esteban |
| **8** | `DELETE`| `/checks/{id_check}` | DynamoDB | `hermes2_batchchecks_dev` | - |
| **9** | `DELETE`| `/checks/batch/{id_batch}` | DynamoDB | `hermes2_batchchecks_dev` | - |
| **10**| `GET` | `/checks/issuer/{id_issuer}/history`| CheckServices (REST) | `RecentChecksBy` | Esteban |
| **11**| `GET` | `/checks/batch` | DynamoDB | `hermes2_batchchecks_dev` | - |
| **12**| `GET` | `/checks/agents/{id_agent}/check_limit` | Front Office V1 (SOAP) | `GetLimitChecksBatchByAgent` | Esteban |
| **13**| `POST`| `/checks/giact` | CheckServices (REST) | `ValidateCheckGiact` | Esteban |
| **14**| `POST`| `/checks/upload_image` | CheckServices + AWS S3 + OFAC | `ValidateCheckImage` / S3 bucket | Esteban |
| **15**| `PUT` | `/checks/{id_check}` | SearchOFAC V1 + DynamoDB | `hermes2_batchchecks_dev` | - |
| **16**| `POST`| `/checks/totals/calculate` | Front Office V1 (SOAP) | `GetFeeChecks` | David |
| **17**| `GET` | `/checks/customer/{id_customer}/history` | CheckServices (REST) | `RecentChecksBy` | David |
| **18**| `GET` | `/checks/configuration/fees/agent/{id_agent}` | CheckServices (REST) | `/api/AgCustFees` | Román |
| **19**| `GET` | `/checks/agents/{id_agent}/transaction_limits`| Front Office V1 (SOAP) | `GetInfoMaxiLicense` | Román |
| **20**| `POST`| `/checks/single/process` | Front Office V1 + Brisk + S3 + SQL | `SaveCheck`, `st_InsertCustomerByTransfer` | Román / Eduardo |
| **21**| `POST`| `/checks/batch` | Front Office V1 + OFAC + DynamoDB | `SaveChecks`, `batch_dev` | Eduardo |
| **22**| `POST`| `/checks/configuration/fees/agent` | CheckServices (REST) | `/api/AgCustFees` | Hinojo |
| **23**| `PUT` | `/checks/configuration/fees/agent` | CheckServices (REST) | `/api/AgCustFees` | Hinojo |
| **24**| `DELETE`| `/checks/configuration/fees/agent` | CheckServices (REST) | `/api/AgCustFees` | Hinojo |
| **25**| `PATCH`| `/checks/status` | Front Office V2 (SOAP) | `ChangeCurrentCheckStatus` | Hinojo |
| **26**| `GET` | `/checks/check-cashing/types` | CheckServices (REST) | `GetCheckCashingTypes` | Hinojo |
| **27**| `POST`| `/checks/check-cashing/totals` | SQL Repository | `st_GetFeeChecksByTypeDetail` | - |
| **28**| `GET` | `/checks/check-cashing/check-sources` | SQL Repository | `GetCheckSourcesRepository` | - |
| **29**| `GET` | `/checks/check-cashing/issuer-relationships` | SQL Repository | `GetIssuerRelationshipsRepository` | - |

*(Adicionalmente, se incluyen `/healthcheck` y `/version` para monitoreo del microservicio).*

---

## 🎓 8. Consejos Prácticos de Anty para Toño

1. **Empieza siempre por los Catálogos y Health:**
   * Los endpoints de la carpeta `00. Sistema & Health` y `01. Catálogos` son de solo lectura (`GET`) y no requieren datos previos complejos. Son ideales para validar que la conexión y el `baseUrl` funcionan al 100%.
2. **Atento al Header `authorizer`:**
   * Si alguno de los endpoints de negocio responde `401 Unauthorized` o `403 Forbidden`, simplemente pídele al equipo de desarrollo (o copia de la sesión web de Hermes 2) el token de sesión y colócalo en la variable `authorizer_token` del entorno.
3. **El Patrón de Envoltorio BFF:**
   * Observa que todos los endpoints devuelven siempre:
     ```json
     {
       "status": 200,
       "message": "sucessfull ",
       "data": { ... }
     }
     ```
   * Todas las pruebas de la colección ya vienen pre-configuradas para verificar que esta estructura se cumpla al pie de la letra.
4. **Documentación en NotebookLM:**
   * Puedes subir este documento directamente a tu libreta de NotebookLM (`Fundamentos de QA Automation Jr.`) para que el asistente de audio y estudio también conozca la arquitectura exacta de BFF Checks.
