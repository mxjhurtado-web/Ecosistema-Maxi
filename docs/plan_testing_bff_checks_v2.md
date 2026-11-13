# Plan de Testing BFF Checks (Hermes 2) — v2

**Proyecto:** Hermes 2 - Microservicio BFF Checks (`/api/checks/`)
**Fecha:** Noviembre 2026
**Reemplaza a:** `plan_testing_5_dimensiones_bff_checks.md` (v1)

> Todo lo marcado como **POR DEFINIR** es información que este plan necesita y que hoy no está escrita en ningún lado. La lista completa está en la sección 9. Ningún valor de comisión, límite o SLA de este documento debe tomarse como real hasta cerrar esos puntos.

---

## 0. Qué cambia respecto a la v1

| Tema | v1 | v2 |
| :--- | :--- | :--- |
| Meta de cobertura | "63% → 90%" sin definir qué se mide | Fórmula y denominador explícitos (sección 1) |
| Reglas de negocio | `fee > 0` y `total <= monto` | Comisión y total esperados exactos por caso, más valores de frontera |
| Seguridad | Solo autenticación | Se agrega autorización entre agencias y token expirado |
| Inyección SQL | Esperaba 400/422, enviaba `DROP TABLE` | Criterio corregido, payloads no destructivos |
| Casos negativos | Cualquiera de 400/404/422 | Código exacto por caso y contrato del cuerpo de error |
| Performance | Una medición por petición | Percentil 95 sobre 30 muestras, en suite separada |
| Datos de prueba | No mencionado | Clasificación de endpoints por efecto secundario y limpieza |
| Herramientas | Todo en Postman, luego todo migrado a pytest | Postman para D1; D2 a D5 directo en pytest |
| Cronograma | Sin fechas ni responsables | Responsable, fecha y criterio de salida por hito |

---

## 1. Objetivo, alcance y métrica

**Objetivo:** que un fallo en comisiones, límites, permisos o contrato del BFF Checks sea detectado por la suite antes de llegar a ventanilla.

**Alcance:** los 31 endpoints de la colección (29 de negocio + 2 de monitoreo).

### Cómo se mide la cobertura

Postman y pytest contra un servicio desplegado no miden cobertura de código, así que la meta se define sobre escenarios:

```
Cobertura = casos automatizados y en verde / casos de la matriz de trazabilidad
```

La matriz de trazabilidad es una hoja con una fila por endpoint y una columna por dimensión. Cada celda dice cuántos casos aplican y cuántos están automatizados. No todas las dimensiones aplican a todos los endpoints:

| Dimensión | Aplica a |
| :--- | :--- |
| D1 Status y contrato | Los 31 endpoints |
| D2 Reglas de negocio | Endpoints que calculan o aplican límites (`totals/calculate`, `check-cashing/totals`, `check_limit`, y los que se identifiquen al armar la matriz) |
| D3 Inputs negativos | Todo endpoint con body, parámetros de ruta o query |
| D4 Seguridad | Todo endpoint protegido; autorización entre agencias en todo endpoint que reciba un identificador de agencia, cliente o cheque |
| D5 Performance | Los 31 endpoints, con el umbral de su categoría |

**Meta:** 90% de la matriz en verde, con D2 y D4 al 100% (son las que protegen dinero y datos).

El 63% actual hay que recalcularlo con esta fórmula antes de reportar avance (**POR DEFINIR**: cómo se obtuvo ese número).

---

## 2. Herramientas

| Dimensión | Herramienta | Motivo |
| :--- | :--- | :--- |
| D1 | Postman + Newman | Ya está hecho (Hito 1) y sirve para exploración manual |
| D2, D3, D4, D5 | pytest en Maxx_C 2.0 | Necesitan datos esperados, fixtures de limpieza, dos tokens distintos y cálculo de percentiles; en Postman habría que escribirlo y luego reescribirlo |

Esto elimina la migración de la v1: las dimensiones 2 a 5 se escriben una sola vez. Si el equipo prefiere mantener todo en Postman primero, el contenido de las secciones 4.2 a 4.5 sigue siendo válido; solo cambia dónde se implementa.

---

## 3. Prerrequisitos de ambiente y datos

Sin esto la suite no es repetible.

### 3.1 Datos de prueba dedicados

| Recurso | Para qué | Estado |
| :--- | :--- | :--- |
| Agencia A (hoy `1242`) con usuario y token | Casos normales | **POR DEFINIR**: confirmar que es exclusiva de pruebas |
| Agencia B con usuario y token | Pruebas de autorización entre agencias | **POR DEFINIR** |
| Token expirado o forma de generarlo | SEC-03 | **POR DEFINIR** |
| Cliente y cheque semilla de cada agencia | Consultas por `id_customer` e `id_check` | **POR DEFINIR** |

Los identificadores van en el archivo de ambiente y en `conftest.py`, nunca escritos dentro de los tests.

### 3.2 Clasificación de endpoints por efecto secundario

Cada uno de los 31 endpoints se etiqueta en la matriz con una de estas clases:

| Clase | Ejemplos | Regla |
| :--- | :--- | :--- |
| Lectura | `/healthcheck`, `/check-cashing/types`, `/fees/agent/{id_agent}` | Se ejecuta sin restricción |
| Cálculo sin persistencia | `/totals/calculate`, `/single/validation` | Se ejecuta sin restricción |
| Escritura interna | `/single/process`, `/batch` | Solo con datos de la agencia de prueba; el test registra lo que crea y lo limpia o lo marca |
| Externa | `/giact`, `/upload_image` | Solo contra sandbox o bucket de pruebas; si no existe, se prueba con el servicio externo simulado y se excluye de la corrida diaria |

**POR DEFINIR:** si GIACT tiene sandbox y si cobra por consulta; a qué bucket de S3 escribe Dev; si existe forma de anular o borrar un cheque procesado.

### 3.3 Encadenamiento

Los endpoints que necesitan un `id_check` lo obtienen de un fixture que crea el cheque (o usa el cheque semilla), no de un valor fijo. En Postman, la petición que crea guarda el id con `pm.collectionVariables.set`.

---

## 4. Las 5 dimensiones

### 4.1 Dimensión 1: Status y contrato (Postman)

Cada petición declara su código esperado en una variable, en vez de aceptar 200 o 201 indistintamente:

```javascript
const esperado = Number(pm.variables.get("expected_status") || 200);

pm.test("Status HTTP es " + esperado, function () {
    pm.response.to.have.status(esperado);
});

pm.test("Content-Type es application/json", function () {
    pm.expect(pm.response.headers.get("Content-Type")).to.include("application/json");
});

pm.test("Envoltorio BFF: status, message, data", function () {
    const body = pm.response.json();
    pm.expect(body).to.have.all.keys("status", "message", "data");
    pm.expect(body.status).to.eql(esperado);
});
```

La última línea asume que `status` del envoltorio replica el código HTTP (**POR DEFINIR**: confirmar qué devuelve en un 201).

Además, cada endpoint valida la forma de `data` con un esquema, que es lo que detecta un campo renombrado o un tipo cambiado:

```javascript
const schemaData = {
    type: "object",
    required: ["fee", "total"],
    properties: {
        fee:   { type: "number" },
        total: { type: "number" }
    }
};

pm.test("data cumple el esquema", function () {
    pm.expect(pm.response.json().data).to.have.jsonSchema(schemaData);
});
```

Excepción documentada: `/api/checks/version` responde `{ "version": string }` sin envoltorio.

**Criterio de salida:** 31 endpoints con status exacto, envoltorio y esquema de `data`.

---

### 4.2 Dimensión 2: Reglas de negocio (pytest)

**Propósito:** verificar que la comisión y el total devueltos son exactamente los que dicta la regla, no solo que son plausibles.

#### Paso previo: escribir las reglas

Esta tabla es la fuente de verdad de la que salen los valores esperados. Hay que llenarla con Producto o Finanzas (**POR DEFINIR** completa):

| Tipo de cheque | Comisión mínima | Porcentaje | Tope | Umbrales donde cambia la regla |
| :--- | :---: | :---: | :---: | :--- |
| 1 Nómina | ? | ? | ? | ? |
| 2 Personal | ? | ? | ? | ? |
| 3 Gobierno | ? | ? | ? | ? |

También: límite por cheque de la agencia de prueba, regla de redondeo, y si `total` es `monto - comisión`.

#### Dataset `data_tiers_checks.json`

Cada fila lleva el resultado esperado, como texto para evitar errores de punto flotante:

```json
[
  {
    "id": "nomina_minimo_fijo",
    "checkAmount": 15.00,
    "idCheckType": 1,
    "expectedFee": "POR DEFINIR",
    "expectedTotal": "POR DEFINIR"
  }
]
```

Una fila sin valores esperados reales no entra al dataset.

#### Casos

Los 6 montos de la v1 se conservan como casos representativos. Se agregan los de frontera, que es donde fallan los cálculos escalonados:

| Grupo | Casos | Qué detecta |
| :--- | :--- | :--- |
| Representativos | $15, $85, $350, $950, $1,500, $2,800 con su tipo de cheque | Regla general de cada rango |
| Frontera de cada umbral `U` | `U - 0.01`, `U`, `U + 0.01` | Error de `<` contra `<=` |
| Cruce comisión mínima / porcentaje | El monto exacto donde el porcentaje iguala a la mínima, y un centavo a cada lado | Regla de mínimo mal aplicada |
| Tope de comisión | Monto donde se alcanza el tope y uno mayor | Tope ignorado |
| Redondeo | Montos cuyo porcentaje da tercer decimal (ej. $33.33) | Redondeo contra truncado |
| Mismo monto, distinto tipo | Un monto fijo con tipos 1, 2 y 3 | Tarifa preferencial de gobierno |
| Límite de agencia | `límite`, `límite + 0.01` | Que el exceso se rechace, con el código que corresponda |
| Consistencia | `check_limit` de la agencia contra el monto máximo que `totals/calculate` acepta | Que ambos endpoints usen el mismo límite |

#### Test

```python
import json
from decimal import Decimal
from pathlib import Path

import pytest

CASOS = json.loads(
    (Path(__file__).parent / "data" / "data_tiers_checks.json").read_text(encoding="utf-8")
)


@pytest.mark.negocio
@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["id"])
def test_comision_y_total(api_client, base_url, agencia_a, caso):
    payload = {
        "checkAmount": caso["checkAmount"],
        "idCheckType": caso["idCheckType"],
        "idAgent": agencia_a.id,
    }
    r = api_client.post(f"{base_url}/api/checks/checks/totals/calculate", json=payload)

    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert Decimal(str(data["fee"])) == Decimal(caso["expectedFee"])
    assert Decimal(str(data["total"])) == Decimal(caso["expectedTotal"])
```

**POR DEFINIR:** si `totals/calculate` recibe `idCheckType` en el body (la v1 lo ponía en el dataset pero no en el payload).

**Criterio de salida:** tabla de reglas firmada por quien la define; todos los casos de la tabla anterior en verde, o con un defecto abierto por cada uno en rojo.

---

### 4.3 Dimensión 3: Inputs negativos (pytest)

Tres cambios respecto a la v1:

1. Cada caso exige **un** código, no una lista.
2. Se valida el cuerpo del error, no solo el código.
3. El "nunca 500" se verifica en todos los tests de la suite, con un chequeo común en el cliente HTTP.

#### Contrato de error

**POR DEFINIR** con desarrollo: qué forma tiene la respuesta de error. El mensaje "Field required" sugiere el 422 por defecto de FastAPI (`{"detail": [...]}`), que no respeta el envoltorio `{status, message, data}`. Hay que decidir cuál de las dos formas es la correcta y probar esa.

Además, ningún error debe incluir trazas, nombres de tablas ni texto de SQL.

#### Matriz

El código esperado de cada fila es el que se acuerde con desarrollo; donde la v1 daba dos opciones, aquí queda pendiente de elegir una.

| ID | Endpoint | Entrada | Código |
| :---: | :--- | :--- | :---: |
| NEG-01 | `POST /checks/totals/calculate` | `checkAmount: -50.00` | 422 o 400, **POR DEFINIR** |
| NEG-02 | `POST /checks/totals/calculate` | `checkAmount: 0` | 422 o 400, **POR DEFINIR** |
| NEG-03 | `POST /checks/totals/calculate` | `checkAmount: "MIL_DOLARES"` | 422 |
| NEG-04 | `POST /checks/single/validation` | `routingNumber: "1234"` | 422 |
| NEG-05 | `POST /checks/single/validation` | Body `{}` | 422 |
| NEG-06 | `GET /checks/agents/{id_agent}/check_limit` | Agencia inexistente | 404 o 400, **POR DEFINIR** |
| NEG-07 | `GET /checks/{id_check}` | `id_check` no numérico | 422 o 404, **POR DEFINIR** |
| NEG-08 | `POST /checks/verification/pending` | `pc_identifier: ""` | 422 |
| NEG-09 | `POST /checks/totals/calculate` | `checkAmount: null` | 422 |
| NEG-10 | `POST /checks/totals/calculate` | Sin el campo `idAgent` | 422 |
| NEG-11 | `POST /checks/totals/calculate` | `checkAmount: 100.999` (tres decimales) | **POR DEFINIR**: rechaza o redondea |
| NEG-12 | `POST /checks/totals/calculate` | `checkAmount: 1e15` | 422 o 400 |
| NEG-13 | `POST /checks/single/validation` | Routing de 9 dígitos con dígito verificador ABA inválido | 422 |
| NEG-14 | `POST /checks/single/validation` | Routing con letras o espacios | 422 |
| NEG-15 | Cualquier `POST` | JSON mal formado | 400 o 422 |
| NEG-16 | Cualquier `POST` | Cadena de 10,000 caracteres en un campo de texto | 422 |
| NEG-17 | `GET /checks/{id_check}` | `id_check` numérico inexistente | 404 |

**Criterio de salida:** cada fila con un único código acordado y en verde; ningún 500 en toda la suite.

---

### 4.4 Dimensión 4: Seguridad y control de acceso (pytest)

| ID | Escenario | Petición | Esperado |
| :---: | :--- | :--- | :--- |
| SEC-01 | Sin token | Omitir el header `authorizer` en cada endpoint protegido | 401 |
| SEC-02 | Token mal formado | `authorizer` con un valor inventado | 401 o 403, **POR DEFINIR** |
| SEC-03 | Token expirado | Token válido ya vencido | 401 |
| SEC-04 | Otra agencia en la ruta | Token de A, `GET /checks/agents/{B}/check_limit` y `/fees/agent/{B}` | 403 o 404, y nunca los datos de B |
| SEC-05 | Otra agencia en el body | Token de A, `POST /checks/totals/calculate` con `idAgent: B` | 403, o se ignora el body y se usa la agencia del token |
| SEC-06 | Cheque de otra agencia | Token de A, `GET /checks/{id_check de B}` | 403 o 404 |
| SEC-07 | Cliente de otra agencia | Token de A, `GET /customer/{id_customer de B}/history` | 403 o 404 |
| SEC-08 | Inyección en búsqueda | `' OR '1'='1` y `'; SELECT 1 --` en parámetros de búsqueda | Sin 500, sin texto de SQL en la respuesta, y no devuelve más registros que una búsqueda sin coincidencias |
| SEC-09 | Verbo no permitido | `POST /checks/check-cashing/types` | 405 |
| SEC-10 | Fuga en errores | Revisar el cuerpo de todos los 4xx de la suite | Sin trazas ni nombres de tablas |

Notas:

- SEC-01 se parametriza sobre la lista completa de endpoints protegidos, no sobre un ejemplo.
- SEC-04 a SEC-07 son las más importantes del plan. Un 200 con datos de la otra agencia es un defecto de severidad crítica. Hay que confirmar con negocio si existe algún rol que sí pueda ver varias agencias (**POR DEFINIR**).
- SEC-08 usa solo payloads de lectura. No se envían sentencias destructivas a ningún ambiente compartido.
- Que el BFF "bloquea antes de tocar el backend" (v1) no se puede comprobar desde fuera; si importa, se verifica en logs con desarrollo.

**Criterio de salida:** todos los casos en verde; cualquier fallo en SEC-04 a SEC-07 se reporta de inmediato, sin esperar al cierre del hito.

---

### 4.5 Dimensión 5: Performance (pytest, suite separada)

**Método:** por endpoint, 3 peticiones de calentamiento que se descartan, luego 30 medidas; se compara el percentil 95 contra el umbral. Una medición única falla por ruido de red o arranque en frío y no dice nada del servicio.

```python
import statistics
import time

import pytest


def p95(muestras):
    return statistics.quantiles(muestras, n=20)[-1]


@pytest.mark.performance
@pytest.mark.parametrize("ruta, umbral_ms", [
    ("/api/checks/healthcheck", 300),
    ("/api/checks/checks/check-cashing/types", 300),
])
def test_p95_dentro_de_umbral(api_client, base_url, ruta, umbral_ms):
    for _ in range(3):
        api_client.get(f"{base_url}{ruta}")

    tiempos = []
    for _ in range(30):
        inicio = time.perf_counter()
        api_client.get(f"{base_url}{ruta}")
        tiempos.append((time.perf_counter() - inicio) * 1000)

    assert p95(tiempos) < umbral_ms, f"p95={p95(tiempos):.0f} ms"
```

**Umbrales** (los de la tabla de la v1, unificados; el diagrama de la v1 decía 1,500 ms para S3/GIACT y la tabla 1,800):

| Categoría | Endpoints de ejemplo | p95 máximo |
| :--- | :--- | :---: |
| Catálogos y health | `/healthcheck`, `/version`, `/check-cashing/types`, `/check-sources` | 300 ms |
| Consultas operativas | `/fees/agent/{id_agent}`, `/customer/{id_customer}/history`, `/batch` | 800 ms |
| Cálculos y validaciones | `/totals/calculate`, `/check-cashing/totals`, `/single/validation` | 1,000 ms |
| Procesamiento y externos | `/single/process`, `/giact`, `/upload_image` | 1,800 ms |

**POR DEFINIR:** si estos umbrales están acordados con alguien o son propuestos. Mientras sean propuestos, la primera corrida sirve para establecer la línea base y los fallos se reportan como observaciones, no como defectos.

Reglas:

- Se ejecuta aparte de la suite funcional (`-m performance`) para no volverla inestable.
- Siempre desde la misma máquina o runner; el reporte anota desde dónde y contra qué ambiente.
- Los endpoints de clase "Externa" (sección 3.2) solo se miden contra sandbox.
- Esto mide latencia con un usuario. No es prueba de carga; si se necesita, es un plan aparte (k6 o Locust).

---

## 5. Ejecución

### D1 con Newman

```powershell
cd C:\Users\User\Ecosistema-Maxi\docs

newman run BFF_Checks.postman_collection.json `
  -e BFF_Checks_Dev.postman_environment.json `
  -r cli,htmlextra `
  --reporter-htmlextra-export ./Reporte_BFF_Checks_D1.html `
  --reporter-htmlextra-title "BFF Checks - Status y Contrato"
```

### D2 a D4 con pytest

```powershell
cd C:\Users\User\Repos\Tools\Maxx_C

.\.venv\Scripts\python -m pytest tests_api -m "not performance" `
  --junitxml=reportes\bff_checks.xml `
  --html=reportes\bff_checks.html --self-contained-html
```

(`--html` requiere el paquete `pytest-html`.)

### D5

```powershell
.\.venv\Scripts\python -m pytest tests_api -m performance `
  --junitxml=reportes\bff_checks_performance.xml
```

### Integración continua

| Cuándo | Qué corre |
| :--- | :--- |
| En cada cambio del BFF Checks desplegado a Dev | D1 a D4, sin endpoints de clase "Externa" |
| Cada noche | D1 a D5 completas |

**POR DEFINIR:** en qué herramienta de CI y quién recibe el aviso cuando falla. Mientras la suite corra solo desde una laptop, nadie se entera de una regresión hasta que alguien la ejecuta a mano.

---

## 6. Estructura en Maxx_C 2.0

```
C:\Users\User\Repos\Tools\Maxx_C\
├── pytest.ini                        # Marcadores: negocio, negativos, seguridad, performance
├── tests_api/
│   ├── conftest.py                   # base_url, api_client, agencia_a, agencia_b,
│   │                                 # token_expirado, cheque_semilla, limpieza
│   ├── data/
│   │   ├── data_tiers_checks.json    # Casos de D2 con valores esperados
│   │   ├── casos_negativos.json      # Matriz de D3
│   │   └── endpoints.json            # Los 31 endpoints: método, clase, categoría de SLA, protegido
│   ├── test_reglas_negocio.py        # D2
│   ├── test_inputs_negativos.py      # D3
│   ├── test_seguridad_auth.py        # D4
│   └── test_performance_sla.py       # D5
```

`endpoints.json` es la misma lista que la matriz de trazabilidad; de ahí se parametrizan SEC-01 y D5, de modo que un endpoint nuevo queda cubierto al agregarlo una vez.

---

## 7. Flujo híbrido E2E (sin cambios de fondo)

1. **Precondición por API:** se ejecuta D1 a D4 del BFF. Si falla, no se abre el navegador.
2. **Navegación web (Playwright):** Maxx_C captura el cheque en Hermes 2 con la agencia de prueba.
3. **Verificación:** se consulta `/checks/{id_check}` y el registro en SQL Server `MaxiLog`, y se compara la comisión mostrada en pantalla con la del dataset de D2.
4. **Limpieza:** el cheque creado se anula o se registra para limpieza (sección 3.2).

---

## 8. Cronograma

| Hito | Actividad | Criterio de salida | Responsable | Fecha |
| :---: | :--- | :--- | :--- | :--- |
| 1 | Mapeo de 31 endpoints y happy path | Hecho | | Completado |
| 2 | Cerrar los puntos de la sección 9 | Cada punto con respuesta escrita y nombre de quien la dio | | |
| 3 | Matriz de trazabilidad y recálculo de la cobertura actual | Hoja con las 31 filas y el porcentaje real de partida | | |
| 4 | Ambiente: agencias A y B, tokens, datos semilla, sandbox | Fixtures de `conftest.py` funcionando | | |
| 5 | D1 completa: status exacto y esquemas | 31 endpoints con esquema de `data` | | |
| 6 | D4 Seguridad | Sección 4.4 | | |
| 7 | D2 Reglas de negocio | Sección 4.2 | | |
| 8 | D3 Inputs negativos | Sección 4.3 | | |
| 9 | D5 Performance: línea base | Reporte de p95 por endpoint | | |
| 10 | Integración continua y reporte | Corrida nocturna con aviso de fallos | | |
| 11 | Flujo híbrido con Playwright | Sección 7 | | |

D4 va antes que D2 porque no depende de las reglas de comisión y un hallazgo ahí es el más grave. El hito 2 bloquea a los hitos 4, 7 y 8.

---

## 9. Puntos por definir

| # | Pregunta | A quién | Bloquea |
| :---: | :--- | :--- | :--- |
| 1 | Reglas de comisión por tipo de cheque: mínima, porcentaje, tope, umbrales, redondeo | Producto / Finanzas | D2 |
| 2 | ¿`total` es `monto - comisión`? | Producto / Desarrollo | D2 |
| 3 | Límite por cheque de la agencia de prueba y qué código devuelve el exceso | Producto / Desarrollo | D2 |
| 4 | ¿`totals/calculate` recibe `idCheckType`? | Desarrollo | D2 |
| 5 | Forma del cuerpo de error (envoltorio o `detail`) y código exacto de NEG-01, 02, 06, 07, 11 | Desarrollo | D3 |
| 6 | Valor de `status` del envoltorio en respuestas 201 | Desarrollo | D1 |
| 7 | Segunda agencia de prueba con su token, y forma de obtener un token expirado | Desarrollo / Infraestructura | D4 |
| 8 | ¿Algún rol puede ver datos de varias agencias? | Producto | D4 |
| 9 | Sandbox de GIACT, costo por consulta, bucket de S3 de pruebas | Desarrollo / Infraestructura | D1, D5 |
| 10 | Forma de anular o limpiar cheques creados por las pruebas | Desarrollo | Sección 3.2 |
| 11 | ¿Los SLAs están acordados o son propuestos? | Producto / Arquitectura | D5 |
| 12 | Cómo se calculó el 63% actual | QA | Sección 1 |
| 13 | Herramienta de CI y destinatarios de avisos | Infraestructura | Hito 10 |
