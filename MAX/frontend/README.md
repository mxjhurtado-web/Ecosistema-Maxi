# MAX Frontend

React frontend for MAX omnichannel inbox platform.

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **Keycloak** - Authentication (SSO)
- **Zustand** - State management
- **React Query** - Server state
- **Axios** - HTTP client
- **Socket.io** - WebSocket (real-time)
- **Lucide React** - Icons

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```bash
VITE_API_URL=http://localhost:8000
VITE_KEYCLOAK_URL=http://localhost:8081
VITE_KEYCLOAK_REALM=maxibot
VITE_KEYCLOAK_CLIENT_ID=maxibot-client
```

### 3. Start Development Server

```bash
npm run dev
```

Open http://localhost:5173

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/           # Page components
│   │   ├── LoginPage.jsx
│   │   ├── InboxPage.jsx
│   │   └── LoadingPage.jsx
│   ├── lib/             # Utilities
│   │   └── keycloak.js  # Keycloak config
│   ├── services/        # API services
│   │   └── api.js       # Axios client
│   ├── store/           # Zustand stores
│   │   └── index.js     # Auth & conversations stores
│   ├── hooks/           # Custom React hooks
│   ├── App.jsx          # Main app component
│   └── main.jsx         # Entry point
├── public/              # Static assets
├── .env.example         # Environment template
├── tailwind.config.js   # Tailwind configuration
├── vite.config.js       # Vite configuration
└── package.json
```

## Features

### ✅ Implemented

- [x] Keycloak SSO authentication
- [x] Protected routes
- [x] Token auto-refresh
- [x] Login page
- [x] Inbox layout with sidebar
- [x] User profile display
- [x] Logout functionality

### ⏭️ Next Steps

- [ ] Conversations list
- [ ] Message view
- [ ] Send messages
- [ ] WebSocket real-time updates
- [ ] Canned responses
- [ ] Customer sidebar
- [ ] Filters and search
- [ ] Admin dashboard

## Available Scripts

```bash
# Development
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

## Authentication Flow

1. User visits app
2. Keycloak checks for existing session
3. If not authenticated → redirect to login page
4. User clicks "Sign in with SSO"
5. Redirect to Keycloak login
6. After login → redirect back to app
7. App fetches user info from backend
8. User can access inbox

## API Integration

All API calls use the configured Axios client (`src/services/api.js`) which:
- Automatically adds Bearer token to requests
- Handles token refresh on 401 errors
- Redirects to login if refresh fails

Example:
```javascript
import apiClient from './services/api';

const response = await apiClient.get('/api/v1/conversations');
```

## State Management

### Auth Store
```javascript
import { useAuthStore } from './store';

const { user, isAuthenticated } = useAuthStore();
```

### Conversations Store
```javascript
import { useConversationsStore } from './store';

const { conversations, selectedConversation } = useConversationsStore();
```

## Styling

Uses Tailwind CSS with custom configuration:
- Primary color: Blue (#2563EB)
- Custom utilities for scrollbar hiding
- Responsive design utilities

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_KEYCLOAK_URL` | Keycloak server URL | `http://localhost:8081` |
| `VITE_KEYCLOAK_REALM` | Keycloak realm | `maxibot` |
| `VITE_KEYCLOAK_CLIENT_ID` | Keycloak client ID | `maxibot-client` |

## Deployment

### Build

```bash
npm run build
```

Output will be in `dist/` directory.

### Deploy to Vercel

```bash
npm install -g vercel
vercel
```

### Deploy to Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod
```

## Troubleshooting

### Keycloak connection error
- Ensure Keycloak is running on the configured URL
- Check CORS settings in Keycloak admin console

### API connection error
- Ensure backend is running
- Check `VITE_API_URL` in `.env`
- Verify CORS settings in backend

### Token refresh issues
- Check Keycloak token lifetime settings
- Verify refresh token is enabled in client settings

## License

Internal use only.
