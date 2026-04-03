# 🚀 Deployment Guide - MediConnect-AI

**IBM SkillBuild & Edunet Foundation AIML Internship Capstone Project**

**Status**: 🔄 M2.5 In Progress - ML Classifier Trained  
**Last Updated**: April 3, 2026  
**Target Launch**: Q2 2026

---

## 📋 Overview

This guide covers local development, testing, and production deployment of MediConnect-AI for the internship capstone evaluation and eventual production launch.

### Architecture Stack

```
┌──────────────────────────────────────────────────────────────────────┐
│                   MEDICONNECT-AI FULL STACK                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Frontend                Backend                  AI/ML Layer         │
│  ├─ localhost:3000       ├─ localhost:5000      ├─ Groq LLaMA       │
│  ├─ React 18             ├─ Flask 3.0           ├─ LangGraph (5-node)├
│  ├─ Tailwind CSS         ├─ SQLAlchemy ORM      ├─ Bhashini API      │
│  └─ Recharts             ├─ Firebase Admin      └─ RandomForest ML   │
│                          └─ Gunicorn                                  │
│                                                                       │
│  Database:  SQLite (dev) / PostgreSQL (prod)                         │
│  ML Models: Scikit-learn (92% accuracy) + LangGraph agent            │
│  Analytics: Real-time metrics pipeline + dashboards                  │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### Frontend Deployment: **Vercel** (Primary) or **Netlify** (Alternative)

**Why Vercel?**
- ✅ Zero-config React deployment
- ✅ Automatic HTTPS
- ✅ Global CDN  
- ✅ CI/CD with GitHub integration
- ✅ Free tier sufficient for early launch
- ✅ Serverless functions support

### Backend Deployment: **Render** (Primary) or **Railway** (Alternative)

**Why Render?**
- ✅ Free tier includes PostgreSQL
- ✅ Automatic deploys from GitHub
- ✅ Built-in SSL certificates
- ✅ Environment variable management
- ✅ Health checks and auto-restart
- ✅ Simple Flask/Gunicorn deployment

---

## 🔧 Part 1: Local Development Setup

### Prerequisites

```bash
# Check versions
python --version          # 3.10+
node --version           # 18+
pip --version            # Latest

# For ML model training
pip install scikit-learn pandas numpy joblib
```

### Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate # macOS/Linux

pip install -r requirements.txt

# Create .env from template
cp .env.example .env
# Edit .env with your API keys (Groq, Firebase, Bhashini)

# Train ML classifier (first time only)
python -c "from models.ml_classifier import train_and_save_model; train_and_save_model()"

# Run server
python app.py  # http://localhost:5000
```

### Frontend Setup

```bash
cd frontend
npm install
npm start      # http://localhost:3000
```

### API Keys Required (for full features, not required for demo)

| Service | Purpose | Get Free | Optional? |
|---------|---------|----------|-----------|
| Groq API | LLaMA inference | https://console.groq.com | ✅ Works without |
| Firebase | User auth + data | https://firebase.google.com | ✅ Works without |
| Bhashini API | EN↔KN translation | https://bhashini.gov.in | ✅ Works without |

---

## 🔧 Part 2: ML Model Training & Validation

### First-Time Setup (M2.5)

```bash
cd backend

# Train classifier on 1,620 samples
python -c "from models.ml_classifier import train_and_save_model; train_and_save_model()"

# Output should show:
# Generating 1,620 training samples...
# Training RandomForest classifier...
# Accuracy: 99.69% | Precision: 99.69% | Recall: 99.69% | F1: 99.69%
# Model saved to backend/models/artifacts/urgent_classifier.pkl
```

### Verify Model Artifacts

```bash
ls -la backend/models/artifacts/
# Should show:
# - urgency_classifier.pkl (646 KB)
# - label_encoder.pkl (495 B)
```

### Use Model in Production

```python
from models.ml_classifier import MediConnectMLClassifier

classifier = MediConnectMLClassifier(load_existing=True)

# Prediction
result = classifier.predict({
    'symptom_severity': 0.95,
    'is_cardiac': 1,
    'is_emergency_sign': 1,
    'has_chronic': 1,
    'multiple_symptoms': 1,
    'age_above_60': 0,
    'pregnant': 0,
    'recent_surgery': 0,
    'on_medication': 1,
    'immune_compromised': 0
})

# Returns:
# {
#   'urgency': 'HIGH',
#   'confidence': 0.996,
#   'recommendation': '🚨 EMERGENCY: Call 108 immediately + nearest hospital'
# }
```

---

## 🔧 Part 3: Testing Before Deployment

### Run Unit Tests
# Render.com build script

set -o errexit

pip install --upgrade pip
pip install -r requirements-prod.txt

# Initialize database if needed
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"
```

Make it executable:
```bash
chmod +x backend/build.sh
```

#### 1.4 Update Backend Config

Add to `backend/config.py`:
```python
import os

class ProductionConfig:
    """Production configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # PostgreSQL Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://', 1
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_TOKEN_LOCATION = ['headers']
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # Production settings
    DEBUG = False
    TESTING = False
    PROPAGATE_EXCEPTIONS = True

class Config:
    """Get config based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig
    else:
        return DevelopmentConfig
```

#### 1.5 Update app.py for Production

Modify `backend/app.py`:
```python
import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db
from routes.auth_routes import auth_bp
from routes.symptom_routes import symptom_bp
from routes.hospital_routes import hospital_bp

def create_app():
    app = Flask(__name__)
    
    # Load config based on environment
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        from config import ProductionConfig
        app.config.from_object(ProductionConfig)
    else:
        from config import Config
        app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    
    # Configure CORS for production
    allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(symptom_bp, url_prefix='/api/symptoms')
    app.register_blueprint(hospital_bp, url_prefix='/api/hospitals')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'environment': env}, 200
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

### Step 2: Deploy to Render

#### 2.1 Create Render Account
1. Visit [render.com](https://render.com)
2. Sign up with GitHub
3. Authorize Render to access your repository

#### 2.2 Create New Web Service

**Dashboard → New → Web Service**

**Settings:**
```yaml
Name: mediconnect-ai-backend
Environment: Python 3
Region: Oregon (US West) or Singapore (closest to India)
Branch: main
Root Directory: backend
Build Command: ./build.sh
Start Command: gunicorn app:app -c gunicorn_config.py
```

#### 2.3 Configure Environment Variables

Add in Render Dashboard → Environment:

```env
# Required Variables
FLASK_ENV=production
SECRET_KEY=<generate-secure-random-key-64-chars>
JWT_SECRET_KEY=<generate-secure-random-key-64-chars>

# Database (auto-provided by Render PostgreSQL)
DATABASE_URL=<auto-filled-by-render>

# CORS Configuration
ALLOWED_ORIGINS=https://mediconnect-ai.vercel.app,https://mediconnect-ai.com

# Google Maps API (for future features)
GOOGLE_MAPS_API_KEY=<your-api-key>
```

**Generate Secure Keys:**
```python
# Run this in Python to generate keys
import secrets
print("SECRET_KEY:", secrets.token_hex(32))
print("JWT_SECRET_KEY:", secrets.token_hex(32))
```

#### 2.4 Add PostgreSQL Database

**Dashboard → New → PostgreSQL**

```yaml
Name: mediconnect-ai-db
Region: Same as web service
Plan: Free
```

Connect to Web Service:
- Render automatically adds `DATABASE_URL` environment variable
- Database is accessible only from your web service (secure)

#### 2.5 Deploy

1. Click "Create Web Service"
2. Render will:
   - Clone your repository
   - Install dependencies
   - Run build script
   - Start gunicorn server
3. Monitor logs for any errors
4. Deployment URL: `https://mediconnect-ai-backend.onrender.com`

### Step 3: Verify Backend Deployment

Test endpoints:
```bash
# Health check
curl https://mediconnect-ai-backend.onrender.com/health

# Sign up
curl -X POST https://mediconnect-ai-backend.onrender.com/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","name":"Test User"}'

# Symptom analysis
curl -X POST https://mediconnect-ai-backend.onrender.com/api/symptoms/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"I have severe headache and fever","language":"en"}'
```

---

## 🌐 Part 2: Frontend Deployment (Vercel)

### Step 1: Prepare Frontend for Production

#### 1.1 Update API Base URL

Modify `frontend/src/services/api.js`:
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 
                     'https://mediconnect-ai-backend.onrender.com/api';

export default API_BASE_URL;
```

#### 1.2 Create Environment Variables File

Create `frontend/.env.production`:
```env
REACT_APP_API_URL=https://mediconnect-ai-backend.onrender.com/api
REACT_APP_GOOGLE_MAPS_API_KEY=<your-api-key>
REACT_APP_ENV=production
```

#### 1.3 Optimize Build

Update `frontend/package.json`:
```json
{
  "scripts": {
    "build": "react-scripts build",
    "build:prod": "REACT_APP_ENV=production npm run build"
  }
}
```

#### 1.4 Add Vercel Configuration

Create `frontend/vercel.json`:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "devCommand": "npm start",
  "framework": "create-react-app",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" },
        { "key": "Access-Control-Allow-Methods", "value": "GET,POST,PUT,DELETE,OPTIONS" },
        { "key": "Access-Control-Allow-Headers", "value": "Content-Type, Authorization" }
      ]
    }
  ]
}
```

### Step 2: Deploy to Vercel

#### 2.1 Install Vercel CLI (Optional)
```bash
npm install -g vercel
```

#### 2.2 Deploy via Web Dashboard

**Option A: Vercel Dashboard (Recommended)**

1. Visit [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Click "New Project"
4. Import `mediconnect-ai` repository
5. Configure:
   ```
   Framework Preset: Create React App
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: build
   Install Command: npm install
   ```
6. Add Environment Variables:
   ```
   REACT_APP_API_URL=https://mediconnect-ai-backend.onrender.com/api
   REACT_APP_GOOGLE_MAPS_API_KEY=<your-key>
   ```
7. Click "Deploy"

**Option B: Vercel CLI**

```bash
cd frontend
vercel --prod
```

Follow prompts and add environment variables when asked.

#### 2.3 Configure Custom Domain (Optional)

**Vercel Dashboard → Project → Settings → Domains**

1. Add domain: `mediconnect-ai.com`
2. Add DNS records (provided by Vercel):
   ```
   Type: A
   Name: @
   Value: 76.76.21.21
   
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```
3. SSL certificate auto-generated

### Step 3: Verify Frontend Deployment

Visit: `https://mediconnect-ai.vercel.app`

Test:
- ✅ Homepage loads
- ✅ Sign up works
- ✅ Login works
- ✅ Symptom checker connects to backend
- ✅ Hospital finder works
- ✅ Protected routes work

---

## 🔒 Part 3: Security & Configuration

### 3.1 Security Checklist

- [x] HTTPS enabled (automatic on Vercel/Render)
- [x] JWT secrets are strong and secure
- [x] Database credentials not in code
- [x] CORS configured for specific origins
- [x] SQL injection protection (SQLAlchemy)
- [x] Password hashing (bcrypt)
- [x] Rate limiting (consider adding)
- [x] Environment variables secured

### 3.2 Add Rate Limiting (Optional but Recommended)

Install in backend:
```bash
pip install flask-limiter
```

Update `backend/app.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Apply to specific routes
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # existing code
    pass
```

### 3.3 Environment Variables Summary

**Backend (Render):**
```env
FLASK_ENV=production
SECRET_KEY=<64-char-hex>
JWT_SECRET_KEY=<64-char-hex>
DATABASE_URL=<auto-provided>
ALLOWED_ORIGINS=https://mediconnect-ai.vercel.app
GOOGLE_MAPS_API_KEY=<optional>
```

**Frontend (Vercel):**
```env
REACT_APP_API_URL=https://mediconnect-ai-backend.onrender.com/api
REACT_APP_GOOGLE_MAPS_API_KEY=<optional>
REACT_APP_ENV=production
```

---

## 📊 Part 4: Monitoring & Maintenance

### 4.1 Render Monitoring

**Built-in Features:**
- Health checks (automatic)
- Logs (Dashboard → Logs)
- Metrics (CPU, Memory, Network)
- Auto-restart on failure

**Configure Health Check:**
```
Path: /health
Interval: 30 seconds
Timeout: 10 seconds
```

### 4.2 Vercel Analytics

**Enable in Dashboard:**
- Real-time analytics
- Performance metrics
- Error tracking
- Geographic distribution

### 4.3 Database Backups

**Render PostgreSQL:**
- Automatic daily backups (7 days retention on free tier)
- Manual backup: Dashboard → Database → Backups → Create Backup
- Download backup for local storage

### 4.4 Logging Strategy

**Backend Logging:**
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use in routes
logger.info(f"User {user_id} logged in")
logger.error(f"Database error: {str(e)}")
```

**View Logs:**
- Render: Dashboard → Service → Logs (real-time)
- Download logs for analysis

---

## 🚀 Part 5: Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (34/34)
- [ ] Environment variables documented
- [ ] Production config files created
- [ ] Security keys generated
- [ ] CORS origins configured
- [ ] Database migrations ready

### Backend Deployment
- [ ] Render account created
- [ ] PostgreSQL database provisioned
- [ ] Web service configured
- [ ] Environment variables set
- [ ] Build script working
- [ ] Health check passing
- [ ] API endpoints tested

### Frontend Deployment
- [ ] Vercel account created
- [ ] API URL updated
- [ ] Environment variables set
- [ ] Build successful
- [ ] Routing works (SPA)
- [ ] HTTPS enabled
- [ ] All pages load correctly

### Post-Deployment
- [ ] End-to-end testing complete
- [ ] Performance verified
- [ ] Error monitoring configured
- [ ] Backup strategy in place
- [ ] Documentation updated
- [ ] Demo video recorded
- [ ] Submission ready

---

## 🔄 Part 6: CI/CD Pipeline

### Automatic Deployments

**Render:**
- Pushes to `main` branch auto-deploy
- Enable: Dashboard → Service → Settings → Auto-Deploy

**Vercel:**
- Pushes to `main` branch auto-deploy
- Preview deployments for PRs
- Enable: Dashboard → Project → Settings → Git

### Deployment Workflow

```
Developer Push → GitHub → Trigger Deploy → Run Tests → Build → Deploy → Health Check
                    ↓
              Auto-rollback if health check fails
```

---

## 🌍 Part 7: Alternative Platforms

### Alternative 1: Railway

**Backend:**
```yaml
Service: mediconnect-ai-backend
Start Command: gunicorn app:app
Environment: Python 3.11
Database: PostgreSQL plugin
```

**Pros:**
- Generous free tier
- Excellent DX
- Fast deployments

**Deployment:**
1. Visit [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Add PostgreSQL plugin
4. Set environment variables
5. Deploy

### Alternative 2: Netlify (Frontend)

**Configuration:**
Create `frontend/netlify.toml`:
```toml
[build]
  command = "npm run build"
  publish = "build"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

**Deployment:**
1. Visit [netlify.com](https://netlify.com)
2. New site from Git
3. Select repository
4. Configure build settings
5. Deploy

---

## 🎓 Part 8: Competition Submission

### Microsoft Imagine Cup Requirements

**1. Live Demo URL** ✅
- Frontend: `https://mediconnect-ai.vercel.app`
- Backend API: `https://mediconnect-ai-backend.onrender.com`

**2. Source Code** ✅
- GitHub: `https://github.com/Yashaswini-V21/mediconnect-ai`
- Public repository with MIT License

**3. Demo Video** (Record using DEMO_VIDEO_SCRIPT.md)
- 3-5 minutes
- Upload to YouTube
- Unlisted or public link

**4. Presentation Slides** (Create using guidelines)
- Problem statement
- Solution architecture
- Technical implementation
- Social impact
- Business model

**5. Technical Documentation** ✅
- README.md
- API Documentation
- Architecture Guide
- User Guide

### Submission Checklist

- [ ] Application deployed and accessible
- [ ] Demo video recorded (3-5 min)
- [ ] Presentation slides created (10-15 slides)
- [ ] Screenshots captured (5-10 images)
- [ ] GitHub repository public
- [ ] Documentation complete
- [ ] Team information ready
- [ ] Impact metrics documented

---

## 📈 Performance Optimization

### Frontend Optimizations

1. **Code Splitting:**
```javascript
// React lazy loading
const Dashboard = lazy(() => import('./pages/Dashboard'));
const SymptomChecker = lazy(() => import('./pages/SymptomChecker'));
```

2. **Image Optimization:**
- Use WebP format
- Lazy load images
- Implement CDN

3. **Caching:**
```javascript
// Service worker for offline support
// Register in index.js
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}
```

### Backend Optimizations

1. **Database Indexing:**
```python
# Add indexes to frequently queried columns
class User(db.Model):
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
```

2. **Response Compression:**
```python
from flask_compress import Compress
compress = Compress(app)
```

3. **Caching:**
```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=300)
def get_hospitals():
    # expensive operation
    pass
```

---

## 🆘 Troubleshooting

### Common Issues

**1. Build Fails on Render**
```
Error: No module named 'flask'
Solution: Check requirements-prod.txt includes all dependencies
```

**2. CORS Errors**
```
Error: CORS policy blocked
Solution: Add frontend URL to ALLOWED_ORIGINS in backend
```

**3. Database Connection Fails**
```
Error: could not connect to server
Solution: Check DATABASE_URL format (postgresql:// not postgres://)
```

**4. Frontend Can't Reach Backend**
```
Error: Network Error
Solution: Verify REACT_APP_API_URL is correct in Vercel environment variables
```

**5. 404 on Refresh (React Router)**
```
Error: 404 Not Found on /dashboard
Solution: Add rewrites to vercel.json (see Step 1.4)
```

### Debug Commands

**Backend Logs:**
```bash
# Render CLI
render logs mediconnect-ai-backend

# Or use dashboard
```

**Frontend Logs:**
```bash
# Vercel CLI
vercel logs mediconnect-ai-frontend

# Browser console
```

**Test Database Connection:**
```python
from app import app, db
with app.app_context():
    db.create_all()
    print("Database connected!")
```

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Flask Production Best Practices](https://flask.palletsprojects.com/en/3.0.x/deploying/)
- [React Production Build](https://create-react-app.dev/docs/production-build/)
- [Microsoft Imagine Cup Guidelines](https://imaginecup.microsoft.com/en-us/competitions)

---

## ✅ Success Metrics

After successful deployment:

- ✅ Application accessible 24/7
- ✅ 99.9% uptime
- ✅ < 2 second page load time
- ✅ HTTPS enabled
- ✅ Database backups configured
- ✅ Error monitoring active
- ✅ Ready for demo presentation

---

**🎉 Congratulations! MediConnect AI is now live and ready for Microsoft Imagine Cup 2026!**

**Production URLs:**
- **Frontend**: https://mediconnect-ai.vercel.app
- **Backend API**: https://mediconnect-ai-backend.onrender.com/api

**Next Steps:**
1. Record demo video using [DEMO_VIDEO_SCRIPT.md](DEMO_VIDEO_SCRIPT.md)
2. Create presentation slides
3. Submit to Microsoft Imagine Cup 2026
4. Change the world! 🌍💚
