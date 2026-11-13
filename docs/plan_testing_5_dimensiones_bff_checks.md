# 🛡️ Plan de Testing Integral: Las 5 Dimensiones de Calidad en BFF Checks (Hermes 2)
**Proyecto:** Hermes 2 - Microservicio BFF Checks (Backend For Frontend)  
**Fecha:** Noviembre 2026  

---

## 🎯 1. Objetivo y Alcance

El presente documento establece el plan técnico y operativo para elevar la cobertura de pruebas del microservicio **BFF Checks** (`/api/checks/`) del actual **63%** a un **90%+**, cumpliendo de forma estricta con las **5 Dimensiones de Calidad de Software para APIs**:

1. **Status y Estructura (Happy Path & Schema Validation)**
2. **Reglas de Negocio (Data-Driven Testing & Tiers de Tarifas)**
3. **Validación de Inputs (Pruebas Negativas y Manejo de Errores)**
4. **Seguridad y Control de Acceso (Autenticación, Tokens y Sanitización)**
5. **Performance (Acuerdos de Nivel de Servicio - SLA de Respuesta)**

El plan se divide en dos fases progresivas:
* **Fase 1 (Inmediata):** Implementación y validación en **Postman Desktop v12** y ejecución automatizada por consola mediante **Newman CLI**, con generación de reportes ejecutivos en HTML (`newman-reporter-htmlextra`).
* **Fase 2 (Evolución):** Migración e integración en el agente **Maxx_C 2.0** en Python utilizando el framework **`pytest`** (`@pytest.mark.parametrize`), habilitando flujos híbridos (API + Web con Playwright).

---

## 🏗️ 2. Arquitectura de las 5 Dimensiones en BFF Checks

```
┌────────────────────────────────────────────────────────────────────────┐
│               MICROSERVICIO BFF CHECKS (/api/checks/)                  │
│       Puente entre Hermes 2 (Angular) y Servicios Legados / BD         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┼───────────────────────────────┐
    ▼                               ▼                               ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│ 1. STATUS Y ESTRUCTURA│ │ 2. REGLAS DE NEGOCIO  │ │ 3. INPUTS & NEGATIVAS │
│ - Happy Path 200/201  │ │ - 6 Tiers de montos   │ │ - Montos negativos    │
│ - Envoltorio base:    │ │ - Cálculo de fees     │ │ - Routing inválido    │
│   { status, message,  │ │ - Data-Driven Testing │ │ - Códigos 400 y 422   │
│     data }            │ │   (data_tiers.json)   │ │ - Cero errores 500    │
└───────────────────────┘ └───────────────────────┘ └───────────────────────┘
    │                                                               │
    └───────────────────────────────┬───────────────────────────────┘
                                    ▼
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
┌───────────────────────┐                               ┌───────────────────────┐
│ 4. SEGURIDAD Y AUTH   │                               │ 5. PERFORMANCE & SLAs │
│ - Header 'authorizer' │                               │ - Catálogos < 300 ms  │
│ - Sin token ➔ 401     │                               │ - Consultas BD < 800ms│
│ - Token falso ➔ 401   │                               │ - Procesos S3 < 1500ms│
│ - Sanitización SQL    │                               │ - Monitoreo latencias │
└───────────────────────┘                               └───────────────────────┘
```

---

## 📋 3. Detalle Técnico de las 5 Dimensiones (Fase 1: Postman & Newman)

### 🔹 Dimensión 1: Status y Estructura (Happy Path)
* **Propósito:** Validar que cada endpoint responda con el código HTTP correspondiente y que el payload de respuesta respete el contrato arquitectónico estándar del BFF (*Envelope Pattern*).
* **Alcance:** Los **31 endpoints** mapeados en la colección (29 de negocio + 2 de monitoreo).
* **Aserciones Estándar en Postman (`Tests`):**
  ```javascript
  // 1. Verificación de Código de Estado
  pm.test("Status code es 200 OK (o 201 Created)", function () {
      pm.expect(pm.response.code).to.be.oneOf([200, 201]);
  });

  // 2. Verificación de Formato
  pm.test("Content-Type es application/json", function () {
      pm.expect(pm.response.headers.get("Content-Type")).to.include("application/json");
  });

  // 3. Verificación de Contrato Envoltorio BFF
  pm.test("Contrato Base BFF: Cumple envoltorio estándar {{ status, message, data }}", function () {
      var jsonData = pm.response.json();
      pm.expect(jsonData).to.be.an("object");
      pm.expect(jsonData).to.have.property("status");
      pm.expect(jsonData).to.have.property("message");
      pm.expect(jsonData).to.have.property("data");
      pm.expect(jsonData.status).to.eql(200);
  });
  ```
  *(Excepción documentada: `/api/checks/version` responde directamente `{ "version": string }`).*

---

### 🔹 Dimensión 2: Reglas de Negocio (Data-Driven Testing & Tiers)
* **Propósito:** Probar la lógica financiera de cálculo de comisiones (*Fees*) y límites operativos sobre diferentes rangos de montos, verificando que los algoritmos de tarificación escalonada respondan con exactitud matemática.
* **Endpoints Clave:**
  * `POST /api/checks/checks/totals/calculate`
  * `POST /api/checks/checks/check-cashing/totals`
  * `GET /api/checks/checks/agents/{id_agent}/check_limit`
* **Estructura del Dataset de Prueba (`data_tiers_checks.json`):**
  Se define una matriz de 6 montos representativos que abarcan desde micro-cheques hasta operaciones de límite de ventanilla:

  | Tier | Rango Representativo | Monto (`checkAmount`) | Tipo de Cheque (`idCheckType`) | Objetivo de Negocio |
  | :---: | :--- | :---: | :---: | :--- |
  | **Tier 1** | Micro-transacción | `$15.00` | `1` (Nómina) | Validar comisión mínima fija (*Minimum Fee Rule*). |
  | **Tier 2** | Monto Bajo | `$85.00` | `1` (Nómina) | Validar cobro de porcentaje estándar sin exceder tope. |
  | **Tier 3** | Monto Promedio | `$350.00` | `2` (Personal) | Rango medio más común en ventanillas de agencias. |
  | **Tier 4** | Monto Elevado | `$950.00` | `1` (Nómina) | Umbral previo a requerimiento de doble verificación. |
  | **Tier 5** | Umbral Regulatorio | `$1,500.00`| `3` (Gobierno) | Verificación de comisiones preferenciales gubernamentales. |
  | **Tier 6** | Límite Máximo Agente| `$2,800.00`| `1` (Nómina) | Validación de tope diario por cheque según licencia de agencia. |

* **Aserción en Postman con Variables de Datos (`pm.iterationData`):**
  ```javascript
  pm.test("Cálculo de Comisión Coherente con el Monto", function () {
      var jsonData = pm.response.json();
      var inputMonto = pm.iterationData.get("checkAmount") || pm.variables.get("amount");
      
      pm.expect(jsonData.data).to.have.property("total");
      pm.expect(jsonData.data).to.have.property("fee");
      
      // La comisión debe ser mayor a 0 y menor que el monto del cheque
      pm.expect(jsonData.data.fee).to.be.above(0);
      pm.expect(jsonData.data.total).to.be.at.most(Number(inputMonto));
  });
  ```

---

### 🔹 Dimensión 3: Validación de Inputs (Pruebas Negativas y Casos Borde)
* **Propósito:** Comprobar que el microservicio cuente con defensas robustas ante datos maliciosos, incompletos o fuera de rango, asegurando que devuelva códigos controlados de cliente (`400 Bad Request` o `422 Unprocessable Entity`) y **garantizando que el servidor jamás colapse con un error `500 Internal Server Error`**.
* **Matriz de Casos Negativos a Incorporar en la Colección:**

| ID Caso | Endpoint Objetivo | Verbo | Payload / Entrada Enviada | Código Esperado | Mensaje / Validación Esperada |
| :---: | :--- | :---: | :--- | :---: | :--- |
| **NEG-01** | `/checks/totals/calculate` | `POST` | `{"checkAmount": -50.00, "idAgent": 1242}` | `422 / 400` | Monto no puede ser negativo ni menor a cero. |
| **NEG-02** | `/checks/totals/calculate` | `POST` | `{"checkAmount": 0.00, "idAgent": 1242}` | `422 / 400` | Monto debe ser mayor a cero. |
| **NEG-03** | `/checks/totals/calculate` | `POST` | `{"checkAmount": "MIL_DOLARES", "idAgent": 1242}` | `422` | Tipo de dato inválido (string en campo numérico). |
| **NEG-04** | `/checks/single/validation`| `POST` | Routing number de 4 dígitos (`"routingNumber": "1234"`) | `422` | Routing Number debe contener exactamente 9 dígitos ABA. |
| **NEG-05** | `/checks/single/validation`| `POST` | Body vacío (`{}`) | `422` | Campos obligatorios faltantes (*Field required*). |
| **NEG-06** | `/checks/agents/{id_agent}/check_limit` | `GET` | `id_agent = 99999999` (agencia inexistente) | `404 / 400` | Agencia no encontrada o sin licencia activa. |
| **NEG-07** | `/checks/{id_check}` | `GET` | `id_check = "CHECK_INVALIDO_XYZ"` | `422 / 404` | Identificador de cheque no numérico / no encontrado. |
| **NEG-08** | `/checks/verification/pending` | `POST` | `{"pc_identifier": ""}` (cadena vacía) | `422` | Identificador de estación de trabajo requerido. |

* **Aserción de Control de Excepciones:**
  ```javascript
  pm.test("Respuesta de Error Controlada (400 o 422) - Sin caídas 500", function () {
      pm.expect(pm.response.code).to.be.oneOf([400, 404, 422]);
      pm.expect(pm.response.code).to.not.equal(500);
  });
  ```

---

### 🔹 Dimensión 4: Seguridad y Control de Acceso
* **Propósito:** Validar que los mecanismos de autorización protejan la información financiera y las operaciones de caja contra accesos no autenticados o vectores de inyección básica.
* **Matriz de Pruebas de Seguridad:**

| ID Caso | Escenario | Configuración de Petición | Código Esperado | Criterio de Aceptación |
| :---: | :--- | :--- | :---: | :--- |
| **SEC-01** | **Petición Anónima (Sin Token)** | Omitir por completo el header `authorizer` en endpoints protegidos (ej. `/checks/single/process`). | `401 Unauthorized` | El BFF bloquea la petición antes de tocar los servicios de backend. |
| **SEC-02** | **Token Falso / Malformado** | Enviar `authorizer: "Bearer token_falso_invalido_2026"` en una ruta transaccional. | `401 / 403` | La firma criptográfica o sesión es rechazada inmediatamente. |
| **SEC-03** | **Prueba de Inyección SQL (Sanitización)** | Enviar en parámetros de búsqueda de librador/cliente cadenas tipo: `' OR '1'='1` o `1; DROP TABLE Checks;`. | `422 / 400` | La consulta es parametrizada por el ORM/BFF y **no genera error 500 en SQL Server**. |
| **SEC-04** | **Restricción de Verbo HTTP** | Enviar un `POST` a una ruta que solo acepta `GET` (ej. `POST /checks/check-cashing/types`). | `405 Method Not Allowed` | El enrutador rechaza métodos no permitidos. |

---

### 🔹 Dimensión 5: Performance y Acuerdos de Nivel de Servicio (SLAs)
* **Propósito:** Asegurar que los tiempos de respuesta cumplan con la experiencia de usuario requerida en ventanilla de agencia, donde el cajero no debe esperar demoras excesivas frente al cliente.
* **Escala de SLAs Clasificada por Naturaleza del Endpoint:**

| Categoría de Endpoint | Endpoints de Ejemplo | SLA Máximo | Justificación Técnica |
| :--- | :--- | :---: | :--- |
| 🟢 **Catálogos & Health (Lectura en Memoria/Caché)** | `/healthcheck`, `/version`, `/check-cashing/types`, `/check-sources` | **`< 300 ms`** | Datos casi estáticos con mínimo impacto en base de datos. |
| 🟡 **Consultas Operativas (Lectura en SQL Server / DynamoDB)** | `/fees/agent/{id_agent}`, `/customer/{id_customer}/history`, `/batch` | **`< 800 ms`** | Involucran queries relacionales en SQL Server o lecturas indexadas. |
| 🟠 **Cálculos y Validaciones Ligeras** | `/totals/calculate`, `/check-cashing/totals`, `/single/validation` | **`< 1,000 ms`**| Reglas de negocio y consulta de listas negras (OFAC / DenyList). |
| 🔴 **Procesamiento Pesado & Servicios Externos** | `/single/process`, `/giact`, `/upload_image` (S3) | **`< 1,800 ms`**| Comunicación con servicios externos bancarios (GIACT), subida cifrada a AWS S3 y persistencia transaccional. |

* **Aserción Parametrizada de Performance en Postman:**
  ```javascript
  var expectedSla = pm.variables.get("endpoint_sla") || 1500;
  pm.test("Tiempo de respuesta dentro de SLA (< " + expectedSla + " ms)", function () {
      pm.expect(pm.response.responseTime).to.be.below(Number(expectedSla));
  });
  ```

---

## 💻 4. Flujo de Ejecución y Automatización (Fase 1: Newman CLI)

La suite completa se ejecuta en modo desatendido mediante Newman, permitiendo exportar reportes ejecutivos interactivos para el equipo.

### Estructura de Comandos en Consola (PowerShell):

#### A. Ejecución de la Suite Completa con Reporte HTML:
```powershell
cd C:\Users\User\Ecosistema-Maxi\docs

newman run BFF_Checks.postman_collection.json `
  -e BFF_Checks_Dev.postman_environment.json `
  -r cli -r htmlextra `
  --reporter-htmlextra-export ./Reporte_BFF_Checks_5_Dimensiones.html `
  --reporter-htmlextra-title "Auditoría de Calidad BFF Checks - 5 Dimensiones"
```

#### B. Ejecución Específica de Reglas de Negocio con Dataset de Tiers:
```powershell
newman run BFF_Checks.postman_collection.json `
  -e BFF_Checks_Dev.postman_environment.json `
  --folder "02. Reglas de Negocio (Tiers & Tarifas)" `
  -d data_tiers_checks.json `
  -r cli
```

#### C. Ejecución Focalizada de Pruebas Negativas y Seguridad:
```powershell
newman run BFF_Checks.postman_collection.json `
  -e BFF_Checks_Dev.postman_environment.json `
  --folder "05. Pruebas Negativas (Validación de Inputs)" `
  --folder "06. Pruebas de Seguridad & Control de Acceso" `
  -r cli
```

---

## 🐍 5. Fase 2: Integración en el Agente Maxx_C 2.0 (Python + pytest)

Una vez validadas y estabilizadas las 5 dimensiones en Postman/Newman, la lógica se integrará de forma nativa en el agente **Maxx_C 2.0** en el entorno Python ya existente (`C:\Users\User\Repos\Tools\Maxx_C\.venv`).

### 1. Estructura de la Suite en Maxx_C 2.0:
```
C:\Users\User\Repos\Tools\Maxx_C\
├── tests_api/
│   ├── conftest.py                   # Fixtures de autenticación y cliente HTTP
│   ├── data/
│   │   └── data_tiers_checks.json    # Mismo dataset reutilizado
│   ├── test_status_contrato.py       # Dimensión 1: Status 200 y JSON Schema
│   ├── test_reglas_negocio.py        # Dimensión 2: @pytest.mark.parametrize con 6 montos
│   ├── test_inputs_negativos.py      # Dimensión 3: Casos 400 y 422
│   ├── test_seguridad_auth.py        # Dimensión 4: Validación de tokens 401
│   └── test_performance_sla.py      # Dimensión 5: Benchmarks de tiempo de respuesta
```

### 2. Ejemplo Técnico de Parametrización en Python (`@pytest.mark.parametrize`):
```python
import pytest
import requests

TIERS_MONTOS = [
    (15.00, 1, 200),
    (85.00, 1, 200),
    (350.00, 2, 200),
    (950.00, 1, 200),
    (1500.00, 3, 200),
    (2800.00, 1, 200),
]

@pytest.mark.parametrize("monto, tipo_cheque, status_esperado", TIERS_MONTOS)
def test_calcular_totales_tiers(api_client, base_url, monto, tipo_cheque, status_esperado):
    payload = {
        "checkAmount": monto,
        "idAgent": 1242
    }
    response = api_client.post(f"{base_url}/api/checks/checks/totals/calculate", json=payload)
    
    assert response.status_code == status_esperado
    data = response.json()
    assert data["status"] == 200
    assert "data" in data
    assert data["data"]["fee"] > 0
    assert data["data"]["total"] <= monto
```

### 3. Flujo Híbrido E2E de Maxx_C 2.0:
1. **Pre-condición por API (Milisegundos):** Maxx_C 2.0 ejecuta el test de API de cheques. Si el microservicio responde verde, continúa.
2. **Navegación Web (Playwright):** Maxx_C abre Hermes 2, llena la información del cheque en pantalla y captura la transacción.
3. **Verificación Silenciosa:** Maxx_C consulta por API `/checks/{id_check}` y valida en SQL Server `MaxiLog` que el registro haya quedado asentado correctamente.

---

## 📅 6. Cronograma de Entregables

| Hito | Actividad | Herramientas | Estado |
| :---: | :--- | :--- | :---: |
| **Hito 1** | Mapeo de 31 endpoints, Happy Path (200 OK) y Contrato Base. | Postman / Newman |  **Completado** |
| **Hito 2** | Creación del dataset `data_tiers_checks.json` (6 montos). | JSON / Dataset | 🟡 **Listo para crear** |
| **Hito 3** | Incorporación de Carpetas 05 (Negativas) y 06 (Seguridad) en Postman. | Postman Collection | 🟡 **Listo para crear** |
| **Hito 4** | Ejecución general con Newman y generación de reporte HTML interactivo. | Newman / htmlextra | 🟡 **Listo para ejecutar**|
| **Hito 5** | Migración modular hacia `Maxx_C 2.0` con suite en `pytest`. | Python / Playwright | ⏳ **Fase 2 (Siguiente paso)** |
