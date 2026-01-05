# MAX - UI/UX Design & Wireframes

## 🎨 Inspiración de Plataformas Líderes

### **1. Respond.io**
- **Fortalezas**: Inbox unificado muy limpio, excelente manejo de múltiples canales
- **Características clave**:
  - Vista de 3 columnas (navegación, lista conversaciones, chat)
  - Filtros inteligentes por canal, estado, equipo
  - Información del cliente siempre visible
  - Canned responses integradas

### **2. Intercom**
- **Fortalezas**: UX intuitiva, diseño moderno, excelente para equipos
- **Características clave**:
  - Búsqueda poderosa
  - Asignación rápida de conversaciones
  - Notas internas destacadas
  - Métricas en tiempo real

### **3. Zendesk**
- **Fortalezas**: Robusto, escalable, excelente para grandes equipos
- **Características clave**:
  - Vistas personalizables
  - Macros (canned responses avanzadas)
  - SLA tracking visible
  - Reportes detallados

### **4. Front**
- **Fortalezas**: Colaboración en equipo, comentarios internos
- **Características clave**:
  - Asignación colaborativa
  - Comentarios en conversaciones
  - Integraciones visibles
  - Workflow automation

---

## 📱 Wireframes de MAX

### **Pantalla 1: Login (SSO con Keycloak)**

![Login Screen](C:/Users/User/.gemini/antigravity/brain/a4a484fd-0e8b-44e8-a997-9703d08691e9/max_login_screen_1767642386882.png)

**Elementos**:
- Logo MAX centrado
- Título: "Omnichannel Inbox Platform"
- Botón grande: "Iniciar sesión con SSO"
- Redirect automático a Keycloak
- Callback y guardado de token

---

### **Pantalla 2: Inbox Principal**

![Inbox Wireframe](C:/Users/User/.gemini/antigravity/brain/a4a484fd-0e8b-44e8-a997-9703d08691e9/max_inbox_wireframe_1767642358628.png)

**Layout de 3 Columnas**:

#### **Columna 1: Navegación (250px)**
- 🏠 Inbox
- 👤 Asignadas a mí
- 📋 Todas las conversaciones
- 👥 Por equipo
  - Sales
  - Support
  - Customer Service
- ⚙️ Configuración (Admin)

#### **Columna 2: Lista de Conversaciones (350px)**
- **Filtros superiores**:
  - Estado (Nuevas, Asignadas, Pendientes, Cerradas)
  - Canal (WhatsApp, Chat App)
  - Búsqueda
- **Cada conversación muestra**:
  - Avatar del cliente
  - Nombre del cliente
  - Último mensaje (preview)
  - Timestamp
  - Badge de estado (color)
  - Badge de canal (ícono)
  - Indicador de SLA (si aplica)

#### **Columna 3: Vista de Conversación (resto del espacio)**
- Ver siguiente sección

---

### **Pantalla 3: Vista de Conversación**

![Conversation View](C:/Users/User/.gemini/antigravity/brain/a4a484fd-0e8b-44e8-a997-9703d08691e9/max_conversation_view_1767642373157.png)

**Estructura**:

#### **Top Bar**
- Nombre del cliente
- Canal (ícono)
- Estado (dropdown)
- Botones de acción:
  - Asignar
  - Transferir
  - Cerrar

#### **Área de Mensajes (centro)**
- Mensajes del cliente (izquierda, gris)
- Mensajes del agente (derecha, azul)
- Mensajes del sistema (centro, italic)
- Timestamps
- Estados de entrega (WhatsApp: enviado/entregado/leído)

#### **Composer (abajo)**
- Campo de texto
- Botones:
  - 💬 Canned responses
  - 😊 Emoji
  - 📎 Adjuntar archivo
  - ➤ Enviar

#### **Sidebar Derecho (300px)**
- **Información del Cliente**:
  - Nombre
  - Email
  - Teléfono
  - Canal(es)
  - Tags
- **Conversaciones Previas** (últimas 5)
- **Transacciones Recientes**
- **Tickets Abiertos**
- **Notas Internas**

---

## 🎨 Paleta de Colores

### **Colores Principales**
- **Primary Blue**: `#2563EB` - Botones, acciones principales
- **Success Green**: `#10B981` - Estados positivos, mensajes enviados
- **Warning Orange**: `#F59E0B` - SLA warnings, pendientes
- **Error Red**: `#EF4444` - Errores, SLA violations
- **Gray Scale**:
  - `#F9FAFB` - Background
  - `#E5E7EB` - Borders
  - `#6B7280` - Text secondary
  - `#111827` - Text primary

### **Estados de Conversación**
- **Nueva**: Badge azul `#3B82F6`
- **Asignada**: Badge verde `#10B981`
- **Pendiente**: Badge naranja `#F59E0B`
- **Cerrada**: Badge gris `#6B7280`

---

## 🔔 Notificaciones en Tiempo Real

### **WebSocket Events**
- Nuevo mensaje → Notificación + sonido
- Conversación asignada → Notificación
- SLA violation → Alerta roja
- Transferencia recibida → Notificación

### **UI Updates**
- Badge de contador en navegación
- Highlight de conversación nueva
- Scroll automático a nuevo mensaje
- Indicador de "escribiendo..."

---

## 📊 Dashboard de Métricas (Admin/Supervisor)

### **Widgets Principales**
1. **Conversaciones Activas** (número grande)
2. **FRT Promedio** (con gráfica de tendencia)
3. **Tiempo de Resolución** (con gráfica)
4. **Backlog por Equipo** (gráfica de barras)
5. **Agentes Online** (lista con status)
6. **SLA Compliance** (porcentaje con indicador)

### **Filtros**
- Rango de fechas
- Equipo
- Agente
- Canal

---

## 🎯 Flujo de Usuario Completo

### **Caso 1: Agente responde conversación nueva**

```
1. Agente hace login con SSO
   ↓
2. Ve inbox con conversaciones nuevas
   ↓
3. Click en conversación → se abre en panel derecho
   ↓
4. Lee mensaje del cliente
   ↓
5. Ve información del cliente en sidebar
   ↓
6. Escribe respuesta (o usa canned response)
   ↓
7. Click "Enviar"
   ↓
8. Mensaje se marca como "entregado"
   ↓
9. Conversación cambia a estado "Asignada"
```

### **Caso 2: Supervisor asigna conversación**

```
1. Supervisor ve lista de conversaciones en queue
   ↓
2. Click en conversación
   ↓
3. Click botón "Asignar"
   ↓
4. Dropdown muestra agentes disponibles
   ↓
5. Selecciona agente
   ↓
6. Conversación desaparece de queue
   ↓
7. Agente recibe notificación
```

### **Caso 3: Agente cierra conversación**

```
1. Agente termina de resolver issue
   ↓
2. Click botón "Cerrar"
   ↓
3. Modal pide razón de cierre
   ↓
4. Selecciona razón (resuelto, spam, etc.)
   ↓
5. Opcional: agregar nota final
   ↓
6. Click "Confirmar"
   ↓
7. Conversación se marca como cerrada
   ↓
8. Métricas se actualizan (FRT, resolution time)
```

---

## 🚀 Características Clave de UX

### **1. Búsqueda Inteligente**
- Buscar por:
  - Nombre del cliente
  - Email
  - Teléfono
  - Contenido del mensaje
  - ID de conversación
- Resultados en tiempo real
- Highlight de términos encontrados

### **2. Canned Responses**
- Atajo de teclado: `/`
- Autocomplete al escribir
- Variables: `{{customer_name}}`, `{{order_id}}`
- Categorías: Saludos, Despedidas, FAQ
- Contador de uso

### **3. Atajos de Teclado**
- `Ctrl + K`: Búsqueda rápida
- `Ctrl + Enter`: Enviar mensaje
- `Esc`: Cerrar modal
- `↑/↓`: Navegar conversaciones
- `/`: Abrir canned responses

### **4. Drag & Drop**
- Arrastrar archivos al composer
- Preview antes de enviar
- Soporte para imágenes, PDFs, docs

### **5. Indicadores Visuales**
- Dot verde: Agente online
- Dot gris: Agente offline
- Typing indicator: "Cliente escribiendo..."
- Read receipts: ✓✓ (WhatsApp)

---

## 📱 Responsive Design

### **Desktop (1920x1080)**
- 3 columnas completas
- Sidebar de cliente siempre visible

### **Tablet (1024x768)**
- 2 columnas (lista + conversación)
- Sidebar de cliente en modal

### **Mobile (375x667)**
- 1 columna
- Navegación en bottom bar
- Conversación fullscreen

---

## 🎨 Componentes Reutilizables

### **1. ConversationCard**
```jsx
<ConversationCard
  customer={customer}
  lastMessage={message}
  status="new"
  channel="whatsapp"
  timestamp={timestamp}
  onClick={handleClick}
/>
```

### **2. MessageBubble**
```jsx
<MessageBubble
  content={text}
  sender="customer"
  timestamp={timestamp}
  status="delivered"
/>
```

### **3. CustomerSidebar**
```jsx
<CustomerSidebar
  customer={customer}
  conversations={previousConversations}
  transactions={transactions}
  tickets={tickets}
/>
```

### **4. CannedResponsePicker**
```jsx
<CannedResponsePicker
  onSelect={handleSelect}
  category={category}
/>
```

---

## 🔧 Tech Stack Recomendado

### **Frontend**
- **Framework**: React 18 + Vite
- **UI Library**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand o Redux Toolkit
- **WebSocket**: Socket.io-client
- **Forms**: React Hook Form
- **HTTP**: Axios
- **Routing**: React Router v6

### **Componentes UI**
- **shadcn/ui**: Componentes accesibles y customizables
- **Radix UI**: Primitivos sin estilo
- **Lucide Icons**: Íconos modernos
- **date-fns**: Manejo de fechas

---

## ✅ Checklist de Implementación

### **Fase 1: Setup**
- [ ] Crear proyecto React con Vite
- [ ] Configurar Tailwind CSS
- [ ] Instalar shadcn/ui
- [ ] Configurar routing
- [ ] Setup Keycloak auth

### **Fase 2: Autenticación**
- [ ] Pantalla de login
- [ ] Integración con Keycloak
- [ ] Callback handler
- [ ] Protected routes
- [ ] Token refresh

### **Fase 3: Inbox**
- [ ] Layout de 3 columnas
- [ ] Lista de conversaciones
- [ ] Filtros y búsqueda
- [ ] WebSocket connection
- [ ] Notificaciones

### **Fase 4: Conversación**
- [ ] Vista de mensajes
- [ ] Composer
- [ ] Canned responses
- [ ] Customer sidebar
- [ ] Acciones (asignar, transferir, cerrar)

### **Fase 5: Admin**
- [ ] Dashboard de métricas
- [ ] Gestión de usuarios
- [ ] Configuración de SLA
- [ ] Reportes

---

**Next**: ¿Quieres que empiece a crear la estructura del proyecto React?
