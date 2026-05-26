# MediConnect-AI 2.0 — Deployment & Setup Guide

**Status**: Production-Ready | May 26, 2026  
**Deployment**: Render (Backend) + Vercel (Frontend) + GitHub Actions CI/CD

---

## 📋 Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Local Development Setup](#local-development-setup)
3. [Environment Configuration](#environment-configuration)
4. [Render Backend Deployment](#render-backend-deployment)
5. [Vercel Frontend Deployment](#vercel-frontend-deployment)
6. [GitHub Actions CI/CD](#github-actions-cicd)
7. [Testing & Validation](#testing--validation)
8. [Monitoring & Logs](#monitoring--logs)
9. [Troubleshooting](#troubleshooting)
10. [Security Checklist](#security-checklist)

---

## Quick Start

### Prerequisites
- Git
- Python 3.10+
- Node.js 18+
- GitHub account
- Render account (free tier available)
- Vercel account (free tier available)

### 5-Minute Local Run

```bash
# 1. Clone repository
git clone https://github.com/Yashaswini-V21/MediConnect-AI.git
cd MediConnect-AI

# 2. Create Python environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Copy environment file
cp .env.example .env
# Edit .env and add your API keys (see Environment Configuration below)

# 5. Run backend (localhost:5000)
cd backend
python app.py

# 6. (In another terminal) Run frontend (localhost:3000)
cd frontend
npm install
npm start
```

**What you'll see:**
- Backend health check: http://localhost:5000/api/health
- Frontend app: http://localhost:3000
- Admin dashboard: http://localhost:3000/admin/login

---

## Local Development Setup

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Create virtual environment (Mac/Linux)
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp ../.env.example .env

# 5. Update .env with minimal config for local dev:
# FLASK_ENV=development
# DEBUG=True
# GROQ_API_KEY=your_groq_key_here (get free at https://console.groq.com)
# BHASHINI_API_KEY=your_bhashini_key_here (optional)

# 6. Run Flask app
python app.py

# Expected output:
# * Running on http://localhost:5000
# ✅ Database tables created successfully
```

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies (first time only)
npm install

# 3. Update .env (if needed)
# REACT_APP_API_URL=http://localhost:5000/api

# 4. Start development server
npm start

# Expected output:
# Compiled successfully!
# On Your Network: http://192.168.x.x:3000
```

### Database Initialization

```bash
# The app auto-creates SQLite database on first run
# To seed sample data:

cd backend
python seed_analytics.py  # Populate hospitals, specialties, doctors
python seed_m3.py         # Populate admin users, sample appointments
```

---

## Environment Configuration

### Complete .env Setup

Copy `.env.example` to `.env` and fill in the following sections:

#### SECTION 1: Flask Core
```env
FLASK_APP=backend/app.py
FLASK_ENV=development          # development | staging | production
DEBUG=True                      # False in production
SECRET_KEY=generate-random-32-char-string-here
JWT_SECRET_KEY=generate-random-32-char-string-here
```

#### SECTION 2: API Keys (Get Free)

**Groq (LLM)** — https://console.groq.com
```env
GROQ_API_KEY=gsk_your_key_here
```

**Bhashini (Translation)** — https://bhashini.gov.in
```env
BHASHINI_API_KEY=your_key_here
```

#### SECTION 3: Email & SMS (Optional)

**SendGrid** (100 free emails/day) — https://sendgrid.com
```env
SENDGRID_API_KEY=SG.your_key_here
SENDGRID_FROM_EMAIL=noreply@mediconnect.health
```

**Twilio** (free trial) — https://www.twilio.com
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_PHONE_NUMBER=+919999999999  # Your verified number
```

#### SECTION 4: Security

**Generate encryption key:**
```bash
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

```env
ENCRYPTION_KEY=your_fernet_key_here
RATE_LIMIT_ENABLED=True
```

#### SECTION 5: Database

**Local (dev):**
```env
DATABASE_URL=sqlite:///instance/mediconnect.db
```

**Production (Render auto-provides):**
```env
DATABASE_URL=postgresql://user:password@host:5432/mediconnect
```

#### SECTION 6: Deployment
```env
ENVIRONMENT=development        # development | staging | production
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend-url.vercel.app
```

---

## Render Backend Deployment

### Step 1: Create Render Account & Service

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Create new Web Service
4. Connect your GitHub repository
5. Select branch: `main`

### Step 2: Configure Service

In Render dashboard:

```
Service Details:
- Name: mediconnect-backend
- Environment: Python 3
- Build Command: pip install -r backend/requirements.txt
- Start Command: gunicorn backend.app:app

Environment Variables: (add all from .env)
- FLASK_ENV=production
- SECRET_KEY=(generate new, strong key)
- DATABASE_URL=(Render auto-generates PostgreSQL)
- GROQ_API_KEY=your_key
- BHASHINI_API_KEY=your_key
- SENDGRID_API_KEY=your_key
- TWILIO_ACCOUNT_SID=your_sid
- TWILIO_AUTH_TOKEN=your_token
- ENCRYPTION_KEY=your_fernet_key
+ All others from .env.example
```

### Step 3: Deploy

```bash
# Option 1: Auto-deploy on push to main
# (Already configured in Render)
git push origin main
# Render automatically builds and deploys

# Option 2: Manual deploy
# Click "Deploy" button in Render dashboard

# Monitor logs:
# Dashboard → Your Service → Logs
```

**Health check:** Visit `https://your-service.render.com/api/health`

---

## Vercel Frontend Deployment

### Step 1: Create Vercel Project

1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Import project
4. Select `MediConnect-AI` repo

### Step 2: Configure Build Settings

In Vercel dashboard:

```
Framework: Create React App
Build Command: npm run build --prefix frontend
Install Command: npm install --prefix frontend
Output Directory: frontend/build
```

### Step 3: Add Environment Variables

```
REACT_APP_API_URL=https://your-render-service.render.com/api
```

### Step 4: Deploy

```bash
# Auto-deploy on push to main
git push origin main
# Vercel automatically builds and deploys

# Manual deploy:
vercel deploy --prod
```

**Visit:** `https://your-project.vercel.app`

---

## GitHub Actions CI/CD

### Prerequisites

1. GitHub repository with `.github/workflows/deploy.yml` (already included)
2. GitHub Secrets (for deployment):
   - `RENDER_DEPLOY_HOOK_URL_PROD` — Render deployment webhook
   - `VERCEL_TOKEN` — Vercel API token
   - `VERCEL_ORG_ID` — Vercel organization ID
   - `VERCEL_PROJECT_ID` — Vercel project ID

### Get Render Deploy Hook

1. Go to Render dashboard → Your service
2. Settings → Deploy hook
3. Copy the URL
4. Add to GitHub:
   - Go to repository Settings → Secrets → New secret
   - Name: `RENDER_DEPLOY_HOOK_URL_PROD`
   - Value: (paste the webhook URL)

### Get Vercel Credentials

1. `VERCEL_TOKEN`: Go to Vercel account → Settings → Tokens → Create
2. `VERCEL_ORG_ID`: `vercel org ls` (in CLI) or check dashboard URL
3. `VERCEL_PROJECT_ID`: `vercel projects list` (in CLI)

### CI/CD Workflow

When you push to `main`:

```
1. GitHub Actions starts
2. Run backend tests (pytest)
3. Build frontend (npm run build)
4. Code quality checks (Black, Flake8, ESLint)
5. Security scan (Safety, npm audit)
6. If all pass:
   → Deploy backend to Render
   → Deploy frontend to Vercel
7. Notify with status summary
```

**View logs:** GitHub → Actions tab → click your workflow

---

## Testing & Validation

### Run Backend Tests Locally

```bash
cd backend
pytest tests/test_m3_m8.py -v --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html  # or start-process on Windows
```

### Test Key Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Admin login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"password123"}'

# List appointments (requires auth)
curl -H "X-Admin-Email: admin@hospital.com" \
     -H "X-Admin-Token: mediconnect-admin-dev-token" \
     http://localhost:5000/api/admin/appointments

# Analyze symptoms
curl -X POST http://localhost:5000/api/analyze-symptoms \
  -H "Content-Type: application/json" \
  -d '{"symptoms":"chest pain and difficulty breathing","language":"en"}'
```

### Test Admin UI

1. Open http://localhost:3000/admin/login
2. Email: `admin@hospital.com` (from seed data)
3. Password: `admin123`
4. Verify dashboard loads with appointments

### Test Mobile Responsiveness

```bash
# Frontend runs on localhost:3000
# Open in mobile browser or use DevTools mobile view
chrome://inspect
```

---

## Monitoring & Logs

### Render Logs

```bash
# View real-time logs
# Render Dashboard → Your Service → Logs

# Or via CLI:
render logs -s mediconnect-backend
```

### Vercel Logs

```bash
# View build logs
# Vercel Dashboard → Your Project → Deployments → click latest

# Or via CLI:
vercel logs [URL]
```

### GitHub Actions Logs

```
GitHub → Actions → click workflow → click job
```

### Local Development Logs

```bash
# Backend logs
# Printed to console (flask app.py)

# Frontend logs
# Browser DevTools Console (F12 → Console)
```

---

## Troubleshooting

### Backend won't start

```bash
# Error: "Address already in use"
# Solution: Kill process on port 5000
lsof -ti:5000 | xargs kill -9  # Mac/Linux
Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess | Stop-Process  # Windows

# Error: "ModuleNotFoundError"
# Solution: Activate venv and reinstall
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Frontend build fails

```bash
# Error: "npm ERR! code EACCES"
# Solution: Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### GitHub Actions failing

```bash
# 1. Check logs in GitHub Actions tab
# 2. Common issues:
#    - Missing secrets → Add to GitHub settings
#    - Python version mismatch → Update .yml file
#    - Dependencies missing → Update requirements.txt

# Test locally:
pytest backend/tests/ -v
cd frontend && npm run build
```

### Database connection error

```bash
# Local (SQLite):
# Solution: Delete mediconnect.db and restart (auto-recreates)
rm backend/instance/mediconnect.db
python backend/app.py

# Production (PostgreSQL):
# Check connection string in Render dashboard
# Verify DATABASE_URL is set correctly
```

### API key errors

```bash
# Error: "Invalid Groq API key"
# Solution: Generate new key at https://console.groq.com

# Error: "Encryption key not found"
# Solution: Generate with:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Add to .env as ENCRYPTION_KEY
```

---

## Security Checklist

### Before Going to Production

```
Development → Staging → Production

☐ Update SECRET_KEY (minimum 32 random characters)
☐ Set FLASK_ENV=production
☐ Update ALLOWED_ORIGINS with your domain
☐ Generate new ENCRYPTION_KEY
☐ Set all API keys (Groq, Bhashini, SendGrid, Twilio)
☐ Enable HTTPS (Render/Vercel auto-do this)
☐ Configure PostgreSQL (not SQLite)
☐ Enable audit logging (AUDIT_LOGGING_ENABLED=True)
☐ Test rate limiting (30 AI req/min)
☐ Verify RBAC is working (test hospital scope isolation)
☐ Run full test suite locally
☐ Check GitHub Actions pipeline passes
☐ Monitor first 24 hours (check logs)
☐ Set up error alerting (Sentry, LogRocket)
☐ Backup database (PostgreSQL automatic on Render)
```

### Security After Launch

```
☐ Rotate API keys quarterly
☐ Review audit logs weekly
☐ Monitor error rates (no more than 1%)
☐ Update dependencies monthly (npm update, pip list --outdated)
☐ Scan for vulnerabilities (Safety, npm audit)
☐ Test RBAC monthly (ensure scope isolation still works)
☐ Backup critical data daily
☐ Test disaster recovery (can you restore from backup?)
```

---

## Performance Optimization (After Launch)

### Backend Optimization

```python
# 1. Add query indexing to frequently searched fields
db.session.query(Appointment).filter_by(hospital_id=1).all()
# → Add index to hospital_id column

# 2. Cache appointments (Redis)
@cache.cached(timeout=300)
def get_appointments():
    ...

# 3. Enable connection pooling
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_POOL_RECYCLE = 3600
```

### Frontend Optimization

```bash
# 1. Analyze bundle size
npm run build -- --analyze

# 2. Code splitting for lazy loading
const AdminDashboard = lazy(() => import('./AdminDashboard'))

# 3. Enable compression in Vercel
# (automatic)
```

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_hospital_id ON appointments(hospital_id);
CREATE INDEX idx_status ON appointments(status);
CREATE INDEX idx_user_id ON appointments(user_id);
CREATE INDEX idx_date ON appointment_analytics(date);
```

---

## Rollback Plan

If deployment fails in production:

```bash
# 1. Revert to last known good commit
git revert HEAD

# 2. Push to main (auto-triggers re-deployment)
git push origin main

# 3. GitHub Actions + Render/Vercel redeploy last known good version

# 4. Check health
curl https://your-service.render.com/api/health

# 5. Verify frontend loads
# Visit https://your-project.vercel.app
```

---

## Support & Documentation

- **API Documentation**: `docs/API_DOCUMENTATION.md`
- **Database Schema**: `backend/models/` (SQLAlchemy models)
- **Contributing Guide**: `CONTRIBUTING.md`
- **GitHub Issues**: Report bugs or request features

---

**Deployment Complete! 🎉**

Your MediConnect-AI 2.0 is now live and production-ready.

Next: Monitor logs, gather user feedback, plan Phase 2 features.
