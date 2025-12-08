# ATHENAS Lite Web Application

Modern web application for audio quality analysis using AI (Gemini) with role-based access control.

## Architecture

- **Frontend**: Next.js 14 with TypeScript and TailwindCSS
- **Backend**: FastAPI (Python)
- **Authentication**: Keycloak SSO with Google OAuth
- **Database**: SQLite
- **Storage**: Temporary audio files + Google Drive exports

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- Access to Keycloak server (`sso.maxilabs.net`)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on `http://localhost:3000`

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python main.py
```

Backend will run on `http://localhost:8000`

### Environment Configuration

1. Copy `.env.example` to `.env` in the root directory
2. Configure Keycloak settings (see Keycloak Setup below)
3. Add Google Drive credentials if using Drive exports

## Keycloak Setup

### Create Client in Keycloak

1. Go to `https://sso.maxilabs.net/auth/admin`
2. Select realm: `zeusDev`
3. Clients → Create
4. Configure:
   - Client ID: `athenas-lite-web`
   - Client Protocol: `openid-connect`
   - Access Type: `confidential`
   - Valid Redirect URIs: `http://localhost:3000/auth/callback`
   - Web Origins: `http://localhost:3000`
5. Get Client Secret from Credentials tab
6. Add to `.env` file

### Create Roles

1. Roles → Add Role
2. Create two roles:
   - `athenas-admin` (full access)
   - `athenas-user` (analysis only)

### Assign Roles to Users

1. Users → [select user] → Role Mappings
2. Assign `athenas-admin` or `athenas-user`

## Project Structure

```
athenas_web/
├── frontend/                 # Next.js application
│   ├── app/                 # App Router pages
│   │   ├── login/          # Login page
│   │   ├── dashboard/      # User dashboard
│   │   ├── admin/          # Admin panel
│   │   └── results/        # Analysis results
│   ├── components/         # React components
│   └── public/             # Static assets (logos)
├── backend/                # FastAPI application
│   ├── api/               # API endpoints
│   │   ├── auth.py       # Authentication
│   │   ├── analysis.py   # Audio analysis
│   │   └── admin.py      # Admin operations
│   ├── services/         # Business logic
│   │   ├── keycloak.py  # Keycloak integration
│   │   └── storage.py   # Database operations
│   ├── models/          # Pydantic models
│   └── main.py         # FastAPI app entry
└── .env.example        # Environment template
```

## Features

### User Role
- Upload audio files (single/multiple)
- Select department and configure analysis
- View analysis results with executive formatting
- Export to PDF
- Access Google Drive exports
- View analysis history

### Admin Role
- All user features
- Manage departments (add/edit/delete)
- Manage rubrics (upload/edit JSON files)
- Manage users and assign roles
- View system activity

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Frontend Development

```bash
cd frontend
npm run dev      # Development server
npm run build    # Production build
npm run lint     # Run ESLint
```

### Backend Development

```bash
cd backend
python main.py   # Development server with auto-reload
```

## Deployment

See `implementation_plan.md` for detailed deployment instructions including:
- Google Cloud Run (recommended)
- Google App Engine
- Docker deployment

## Brand Colors

- Primary: `#e91e63` (Pink)
- Primary Dark: `#c2185b`
- Background: `#fceff1` (Light Pink)

## License

Internal use only - Maxi Labs
