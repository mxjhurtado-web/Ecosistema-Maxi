# Guía Práctica de Ejecución: Pruebas de API BFF Checks (Hermes 2) — Fase 1
**Proyecto:** Hermes 2 - Microservicio BFF Checks (`/api/checks/`)  
**Fecha:** Noviembre 2026  

---

## 🎯 1. Objetivo de la Fase 1

El objetivo de esta fase es validar la **Dimensión 1 de Calidad (Status y Estructura)** del microservicio **BFF Checks**:
1. Verificar que los endpoints respondan con códigos de éxito (`200 OK` o `201 Created`).
2. Validar que los tiempos de respuesta cumplan el SLA base (< 3000 ms).
3. Asegurar que las respuestas cumplan con el **contrato estándar de envoltorio BFF**:
   ```json
   {
     "status": 200,
     "message": "sucessfull ",
     "data": { ... }
   }
   ```
4. Generar reportes ejecutivos interactivos en **HTML** mediante consola (**Newman**) para documentar la evidencia de calidad.

---

## 💻 2. Requerimientos Previos (Prerrequisitos en la máquina)

Antes de iniciar, verificar que la computadora cuente con lo siguiente:

| Requisito | Descripción | ¿Cómo verificarlo? |
| :--- | :--- | :--- |
| **1. VPN de Maxi LLC** | Necesaria para acceder a los servidores de desarrollo si se trabaja en remoto. | Estar conectada al cliente de VPN corporativo (Cisco / FortiClient). |
| **2. Postman Desktop** | Aplicación de escritorio (versión 11 o 12). | Abrir Postman desde el menú de inicio o escritorio. |
| **3. Node.js y npm** | Entorno de ejecución para poder instalar y correr Newman por consola. | Abrir PowerShell y escribir: `node -v` y `npm -v`. Si muestra versión (ej. `v20.x` o `v22.x`), está listo. |
| **4. Archivos de Prueba** | Los 2 archivos JSON compartidos para importar: | 1. `BFF_Checks.postman_collection.json`<br>2. `BFF_Checks_Dev.postman_environment.json` |

---

## ⚙️ 3. Paso 1: Instalación de Newman y Reporter HTML (Solo una vez)

Newman es el motor que ejecuta las colecciones de Postman directamente desde la terminal de Windows sin necesidad de abrir la aplicación visual.

1. Abre **PowerShell** o **Terminal** de Windows (puedes buscarlo en el menú inicio).
2. Ejecuta el siguiente comando para instalar **Newman** y el generador de reportes visuales **`htmlextra`**:

```powershell
npm install -g newman newman-reporter-htmlextra
```

3. Verifica que haya quedado bien instalado ejecutando:

```powershell
newman --version
```
*(Debe responder con una versión como `6.2.x`)*.

---

## 📥 4. Paso 2: Importar la Colección y el Entorno en Postman Desktop

1. Abre **Postman Desktop**.
2. En la esquina superior izquierda, haz clic en el botón **`Import`** (o presiona `Ctrl + O`).
3. Arrastra a la ventana (o selecciona mediante el botón `files`) los dos archivos compartidos:
   * `BFF_Checks.postman_collection.json`
   * `BFF_Checks_Dev.postman_environment.json`
4. Haz clic en **`Import`**.
5. En la barra lateral izquierda, pestaña **`Collections`**, aparecerá la carpeta:
   * **`BFF Checks - Hermes 2 (QA Automation Maxi LLC)`** (con sus 31 peticiones organizadas en 5 carpetas).

### Activar el Entorno de Desarrollo (Paso Crucial):
1. En la esquina superior derecha de Postman, busca el selector desplegable de entornos (por defecto dice `No Environment`).
2. Despliega el menú y selecciona: **`BFF Checks - Dev Environment`**.
3. Haz clic en el ícono del **ojo (👁️)** junto al selector para comprobar que las variables estén activas:
   * `baseUrl`: `https://hermes2-api-dev.mylabs.mx`
   * `id_agent`: `1242`

---

## 🧪 5. Paso 3: Ejecución de Pruebas en Postman Desktop

### A. Prueba Individual (Petición por Petición)
1. En la barra lateral izquierda, expande la colección **`BFF Checks - Hermes 2`**.
2. Abre la carpeta **`00. Sistema & Health (Monitoreo)`**.
3. Selecciona la petición **`[GET] Get Healthcheck`**.
4. Haz clic en el botón azul **`Send`** (esquina superior derecha).
5. En la parte inferior de la pantalla, haz clic en la pestaña **`Test Results`**:
   * Debes ver **4 pruebas aprobadas en verde (PASS)**:
     * `PASS: Status code es 200 OK (o 201 Created)`
     * `PASS: Tiempo de respuesta dentro de SLA (< 3000ms)`
     * `PASS: Content-Type es application/json`
     * `PASS: Contrato Base BFF: Cumple envoltorio estándar {{ status, message, data }}`
6. Repite la misma prueba con **`[GET] Get Version`** (debe dar 4 pruebas en verde).

### B. Prueba Masiva de Carpeta con Collection Runner
1. Haz clic derecho sobre la carpeta **`01. Catálogos & Check Cashing (GET)`**.
2. Selecciona la opción **`Run folder`**.
3. En la pantalla del Runner:
   * Verifica que en *Environment* esté seleccionado **`BFF Checks - Dev Environment`**.
   * Establece un **Delay** de `500 ms` (para dar medio segundo entre cada llamada y no saturar el servidor).
4. Haz clic en el botón azul **`Run BFF Checks...`**.
5. Verás en tiempo real cómo Postman ejecuta todas las peticiones de esa carpeta en secuencia y muestra el resumen con 100% de aserciones aprobadas.

---

## 📊 6. Paso 4: Ejecución Automatizada por Consola (Newman CLI)

Para ejecutar las mismas pruebas desde la terminal y generar un reporte interactivo en HTML con gráficas:

1. Abre **PowerShell**.
2. Navega con el comando `cd` hacia la carpeta donde tengas guardados los dos archivos `.json`. Por ejemplo:
```powershell
cd C:\Ruta\Donde\Guardaste\Los\Archivos
```

### Comando 1: Ver resultados rápidos en la consola
```powershell
newman run BFF_Checks.postman_collection.json -e BFF_Checks_Dev.postman_environment.json --folder "00. Sistema & Health (Monitoreo)" -r cli
```

### Comando 2: Generar Reporte HTML Ejecutivo interactivo
```powershell
newman run BFF_Checks.postman_collection.json -e BFF_Checks_Dev.postman_environment.json --folder "00. Sistema & Health (Monitoreo)" -r cli -r htmlextra --reporter-htmlextra-export ./Reporte_Health_Checks.html --reporter-htmlextra-title "Reporte de Salud BFF Checks"
```

3. Abre el archivo **`Reporte_Health_Checks.html`** generado haciéndole doble clic: se abrirá en Chrome o Edge mostrando barras de éxito, tiempos de respuesta exactos y detalle de cada prueba.

---

## 🛡️ 7. Semáforo de Seguridad en el Entorno DEV

Para cuidar el ambiente compartido de desarrollo y no interferir con otros compañeros:

* 🟢 **Zona Verde (Segura para ejecutar libremente):**
  * Carpetas `00. Sistema & Health` y `01. Catálogos`.
  * Son peticiones de solo lectura (`GET`). No modifican nada en la base de datos ni crean registros basura.
* 🟡 **Zona Amarilla (Escrituras controladas):**
  * Creación y proceso de cheques (`POST /single/process`).
  * Solo deben ejecutarse utilizando la agencia de pruebas asignada (`1242` o `0020`). Jamás usar agencias de otros compañeros.
* 🔴 **Zona Roja (Detenida por ahora):**
  * Endpoints como `/giact`. Se encuentran en pausa hasta que desarrollo confirme si cuenta con ambiente simulado (*sandbox*).

---

## ❓ 8. Solución a Problemas Comunes (Troubleshooting)

| Error en Postman / Newman | Causa Probable | Solución |
| :--- | :--- | :--- |
| **`ENOTFOUND hermes2-api-dev.mylabs.mx`** | No hay conexión con el servidor. | Verificar que la **VPN de Maxi** esté encendida y conectada. |
| **`401 Unauthorized`** | El endpoint requiere token de seguridad. | En endpoints protegidos, se debe colocar el token activo en la variable `authorizer_token` del Environment. (Los de salud y catálogos no lo requieren). |
| **`newman: El término 'newman' no se reconoce...`** | La terminal no ha refrescado las rutas del sistema. | Cerrar PowerShell y volverlo a abrir después de haber hecho el `npm install -g newman`. |
| **`No environment selected` en Postman** | Las variables `{{baseUrl}}` no se reemplazan. | Asegurarse de que en la esquina superior derecha esté seleccionado **`BFF Checks - Dev Environment`**. |
