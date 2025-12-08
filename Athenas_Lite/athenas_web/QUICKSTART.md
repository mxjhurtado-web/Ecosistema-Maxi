# ATHENAS Lite Web - Quick Start Guide

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- Keycloak access (`sso.maxilabs.net`)

## Setup Steps

### 1. Keycloak Configuration

Create a new client in Keycloak:

1. Go to `https://sso.maxilabs.net/auth/admin`
2. Select realm: `zeusDev`
3. Clients → Create
4. Client ID: `athenas-lite-web`
5. Client Protocol: `openid-connect`
6. Access Type: `confidential`
7. Valid Redirect URIs: `http://localhost:3000/auth/callback`
8. Web Origins: `http://localhost:3000`
9. Get Client Secret from Credentials tab

Create roles:
- `athenas-admin`
- `athenas-user`

Assign roles to users in Keycloak.

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy ..\.env.example .env

# Edit .env and add:
# - KEYCLOAK_CLIENT_SECRET (from step 1)
# - JWT_SECRET_KEY (generate a random string)

# Copy rubricas (if not already done)
# Copy the rubricas folder from parent directory to backend/rubricas

# Run backend
python main.py
```

Backend will run on `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Backend URL is already configured in code
# (NEXT_PUBLIC_BACKEND_URL=http://localhost:8000)

# Run frontend
npm run dev
```

Frontend will run on `http://localhost:3000`

### 4. Test the Application

1. Open `http://localhost:3000`
2. Click "Sign in with Google"
3. Authenticate via Keycloak
4. You'll be redirected based on your role:
   - Admin → `/admin`
   - User → `/dashboard`

## API Documentation

Once backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.10+)
- Verify all dependencies installed: `pip list`
- Check .env file exists and has correct values

### Frontend won't start
- Check Node version: `node --version` (should be 18+)
- Delete `node_modules` and `package-lock.json`, then `npm install` again
- Clear Next.js cache: `rm -rf .next`

### Authentication fails
- Verify Keycloak client is created correctly
- Check redirect URI matches exactly: `http://localhost:3000/auth/callback`
- Verify client secret in backend `.env` matches Keycloak
- Check user has assigned role (`athenas-admin` or `athenas-user`)

### Database errors
- Database will be created automatically on first run
- Check `data/` directory has write permissions
- Delete `data/athenas_history.db` to reset database

## Next Steps

1. Configure Google Drive integration (optional)
2. Add Gemini API key for analysis
3. Test audio upload and analysis
4. Review results in dashboard

## Support

For issues, check:
- Backend logs in terminal
- Frontend console in browser DevTools
- Keycloak admin console for user/role issues
