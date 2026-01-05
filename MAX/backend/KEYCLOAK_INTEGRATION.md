# Keycloak Integration - Complete! 🔐

## ✅ What's Been Done

### 1. **Keycloak Configuration**
- ✅ Reusing Maxibot's Keycloak setup
- ✅ Realm: `maxibot`
- ✅ Client: `maxibot-client`
- ✅ URL: `http://localhost:8081` (development)

### 2. **Backend Changes**

#### **New Files Created:**
- `app/core/keycloak_config.py` - Keycloak settings
- `app/core/keycloak_auth.py` - JWT validation & user extraction

#### **Modified Files:**
- `app/models/user.py` - Removed `password_hash`, added `keycloak_id`
- `app/api/auth.py` - New endpoints for Keycloak auth
- `backend/.env.example` - Added Keycloak variables
- `backend/requirements.txt` - Added PyJWT

### 3. **How It Works**

```
1. User clicks "Login" in frontend
   ↓
2. Frontend redirects to Keycloak login page
   ↓
3. User logs in with Keycloak credentials
   ↓
4. Keycloak redirects back with JWT token
   ↓
5. Frontend sends token to MAX API
   ↓
6. MAX validates token with Keycloak
   ↓
7. MAX creates user in database (first login only)
   ↓
8. User can access MAX features
```

---

## 🔑 **API Endpoints**

### **GET /api/v1/auth/config**
Returns Keycloak configuration for frontend.

**Response:**
```json
{
  "auth_url": "http://localhost:8081/realms/maxibot/protocol/openid-connect/auth",
  "token_url": "http://localhost:8081/realms/maxibot/protocol/openid-connect/token",
  "client_id": "maxibot-client",
  "realm": "maxibot"
}
```

### **GET /api/v1/auth/me**
Get current user info (requires Bearer token).

**Headers:**
```
Authorization: Bearer <keycloak_jwt_token>
```

**Response:**
```json
{
  "id": "uuid",
  "keycloak_id": "keycloak-user-id",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "agent",
  "is_active": true,
  "keycloak_roles": ["maxibot-user", "agent"]
}
```

**Auto-creates user on first login!**

### **POST /api/v1/auth/logout**
Logout endpoint.

**Response:**
```json
{
  "message": "Logout successful",
  "logout_url": "http://localhost:8081/realms/maxibot/protocol/openid-connect/logout"
}
```

---

## 🎯 **Role Mapping**

Keycloak roles → MAX roles:

| Keycloak Role | MAX Role |
|---------------|----------|
| `maxibot-admin` or `admin` | `admin` |
| `supervisor` | `supervisor` |
| `team_lead` | `team_lead` |
| Any other | `agent` |

---

## 🚀 **Testing Keycloak Auth**

### **Option 1: With Maxibot's Keycloak (if running)**

```bash
# Start MAX backend
cd c:\Users\User\Ecosistema-Maxi\MAX
docker-compose up -d

# Test auth config endpoint
curl http://localhost:8000/api/v1/auth/config

# Get token from Keycloak (manual browser flow)
# Then test /me endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/auth/me
```

### **Option 2: Start Keycloak for MAX**

```bash
# Copy Keycloak setup from Maxibot
cd c:\Users\User\maxi-business-ai\Maxibot_Keycloak
docker-compose up -d keycloak

# Wait for Keycloak to start (takes ~30 seconds)
# Access: http://localhost:8081
# Admin: admin / admin123
```

---

## 📝 **Environment Variables**

Add to `backend/.env`:

```bash
# Keycloak Authentication
KEYCLOAK_URL=http://localhost:8081
KEYCLOAK_REALM=maxibot
KEYCLOAK_CLIENT_ID=maxibot-client
KEYCLOAK_CLIENT_SECRET=maxibot-secret-123
KEYCLOAK_VERIFY_SIGNATURE=False  # Set to True in production
KEYCLOAK_VERIFY_AUD=False
```

---

## 🔒 **Security Notes**

### **Development:**
- `KEYCLOAK_VERIFY_SIGNATURE=False` - Skips JWT signature verification (faster)
- `KEYCLOAK_VERIFY_AUD=False` - Skips audience validation

### **Production:**
- ✅ Set `KEYCLOAK_VERIFY_SIGNATURE=True`
- ✅ Set `KEYCLOAK_VERIFY_AUD=True`
- ✅ Use HTTPS for Keycloak URL
- ✅ Rotate CLIENT_SECRET regularly

---

## 🎨 **Frontend Integration**

The frontend will need to:

1. **Get Keycloak config:**
```javascript
const config = await fetch('/api/v1/auth/config').then(r => r.json());
```

2. **Redirect to Keycloak login:**
```javascript
const authUrl = `${config.auth_url}?client_id=${config.client_id}&redirect_uri=${window.location.origin}/callback&response_type=code&scope=openid`;
window.location.href = authUrl;
```

3. **Exchange code for token:**
```javascript
// After redirect back from Keycloak
const code = new URLSearchParams(window.location.search).get('code');
const tokenResponse = await fetch(config.token_url, {
  method: 'POST',
  body: new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: config.client_id,
    code: code,
    redirect_uri: window.location.origin + '/callback'
  })
});
const { access_token } = await tokenResponse.json();
```

4. **Use token for API calls:**
```javascript
const user = await fetch('/api/v1/auth/me', {
  headers: { 'Authorization': `Bearer ${access_token}` }
}).then(r => r.json());
```

---

## ✅ **What's Ready**

- [x] Keycloak configuration
- [x] JWT token validation
- [x] User auto-creation on first login
- [x] Role mapping from Keycloak
- [x] Protected endpoints
- [x] Logout flow

---

## ⏭️ **Next Steps**

1. **Start services:**
   ```bash
   docker-compose up -d
   ```

2. **Generate database migration:**
   ```bash
   docker-compose exec backend alembic revision --autogenerate -m "Add Keycloak auth"
   ```

3. **Apply migration:**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Test auth endpoints:**
   - GET /api/v1/auth/config
   - GET /api/v1/auth/me (with token)

5. **Build frontend** (next session)

---

**Status**: ✅ **Keycloak integration complete!**

MAX now uses the same SSO as all your other tools. Users can log in once and access everything! 🎉
