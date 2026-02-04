# 🧪 Testing Guide - Respond.io Middleware

## Mock MCP Server

Para facilitar las pruebas, hemos creado un servidor MCP mock que usa Google News RSS para respuestas reales.

### Iniciar el Mock MCP Server

```bash
# Instalar dependencias
cd tests
pip install -r requirements.txt

# Iniciar servidor
python mock_mcp_server.py
```

El servidor estará disponible en: `http://localhost:8080`

### Funcionalidades del Mock

1. **Noticias en Tiempo Real**
   - Usa Google News RSS
   - Soporta búsquedas específicas
   - Respuestas en español

2. **Endpoints**
   - `POST /query` - Endpoint principal
   - `GET /health` - Health check
   - `GET /` - Info del servidor

### Ejemplos de Queries

```json
{
  "query": "noticias de tecnología",
  "context": {}
}
```

```json
{
  "query": "últimas noticias",
  "context": {}
}
```

```json
{
  "query": "hola",
  "context": {}
}
```

---

## Testing del Middleware

### 1. Iniciar Mock MCP Server

```bash
cd tests
python mock_mcp_server.py
```

### 2. Configurar Middleware

Actualizar `.env`:
```env
MCP_URL=http://localhost:8080/query
```

### 3. Iniciar Middleware API

```bash
cd api
pip install -r requirements.txt
python main.py
```

### 4. Probar con cURL

```bash
# Test webhook
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: change-me-in-production-use-strong-secret" \
  -d '{
    "conversation_id": "test_conv_123",
    "contact_id": "test_contact_456",
    "channel": "whatsapp",
    "user_text": "noticias de tecnología",
    "metadata": {}
  }'
```

### 5. Verificar Dashboard

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

Abrir: `http://localhost:8501`

---

## Escenarios de Prueba

### ✅ Caso 1: Query de Noticias
**Input:** "noticias de tecnología"  
**Esperado:** Lista de 3 noticias recientes  
**Verificar:** 
- Latencia < 3s
- Status: "ok"
- Response contiene noticias formateadas

### ✅ Caso 2: Query General
**Input:** "hola"  
**Esperado:** Mensaje de bienvenida  
**Verificar:**
- Latencia < 1s
- Status: "ok"
- Response es coherente

### ✅ Caso 3: MCP Timeout
**Acción:** Detener mock MCP server  
**Esperado:** Fallback message después de retries  
**Verificar:**
- Circuit breaker se activa después de 5 fallos
- Retry count = 3
- Status: "error"

### ✅ Caso 4: Secret Inválido
**Input:** Header sin secret correcto  
**Esperado:** HTTP 401  
**Verificar:**
- No se llama al MCP
- Error message claro

---

## Verificación del Dashboard

### Página KPIs
- [ ] Métricas se actualizan
- [ ] Gráficos se renderizan
- [ ] Latencias son correctas

### Página History
- [ ] Requests aparecen en la lista
- [ ] Búsqueda funciona
- [ ] Export CSV/JSON funciona

### Página Logs
- [ ] Logs se muestran en tiempo real
- [ ] Filtros funcionan
- [ ] Auto-refresh funciona

### Página Configuration
- [ ] Cambios de config se guardan
- [ ] Test MCP funciona
- [ ] Clear cache funciona

### Página Maintenance
- [ ] Health checks correctos
- [ ] Test query funciona
- [ ] System info se muestra

---

## Troubleshooting

### Mock MCP no inicia
```bash
# Verificar puerto 8080 está libre
netstat -ano | findstr :8080

# Cambiar puerto si es necesario
# En mock_mcp_server.py, cambiar port=8080
```

### Middleware no conecta a MCP
```bash
# Verificar MCP_URL en .env
# Verificar mock MCP está corriendo
curl http://localhost:8080/health
```

### Dashboard no muestra datos
```bash
# Verificar API está corriendo
curl http://localhost:8000/health

# Verificar credenciales en .env
# DASHBOARD_USERNAME=admin
# DASHBOARD_PASSWORD=change-me-in-production
```

---

## Métricas Esperadas

Con el mock MCP server:
- **Latencia promedio:** 500-1500ms (depende de Google News)
- **Success rate:** >95%
- **MCP uptime:** 100% (mientras esté corriendo)
- **Retry count:** 0 (en condiciones normales)

---

## Próximos Pasos

Una vez verificado el funcionamiento:
1. ✅ Dockerizar todo
2. ✅ Crear docker-compose
3. ✅ Desplegar en producción
4. ✅ Conectar con Respond.io real
