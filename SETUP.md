# MediConnect-AI Testing & Setup Guide

## Quick Setup

### Local Development

```bash
# Backend Setup
cd backend
cp ../.env.example .env
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run app
python app.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm start  # Development server
npm run build  # Production build
npm test  # Run tests
```

## Environment Variables

Required for local development (copy from `.env.example`):

```bash
FLASK_ENV=development
SECRET_KEY=dev-key-change-in-production
JWT_SECRET_KEY=dev-jwt-key-change-in-production
DATABASE_URL=sqlite:///mediconnect.db
```

## CI/CD Pipeline

The GitHub Actions pipeline:

1. **Backend Tests** - Run pytest on Python 3.10 and 3.11
2. **Frontend Tests** - Build React app and run tests
3. **Code Quality** - Lint Python and JavaScript
4. **Security Scan** - Check dependencies for vulnerabilities
5. **Deploy** - Deploy to Render (backend) and Vercel (frontend) on main branch

## Troubleshooting

### Backend Tests Fail

```bash
# Ensure environment variables are set
export FLASK_ENV=testing
export DATABASE_URL=sqlite:///:memory:
export SECRET_KEY=test-secret
export JWT_SECRET_KEY=test-jwt-secret

# Run tests
pytest tests/ -v
```

### Frontend Build Fails

```bash
cd frontend
npm ci  # Clean install
npm run build
```

### Import Errors

```bash
# Ensure you're in the backend directory
cd backend

# Check Python path
python -c "import sys; print(sys.path)"

# Try importing app
python -c "from app import app; print('✅ App loaded')"
```

## Development Workflow

```bash
# Create feature branch
git checkout -b feat/your-feature

# Make changes and test locally
pytest tests/ -v

# Commit and push
git add .
git commit -m "feat: description"
git push origin feat/your-feature

# Create pull request on GitHub
# CI/CD will automatically run tests
```

## Deployment

### Manual Deploy

```bash
# Backend (Render)
curl -X POST $RENDER_DEPLOY_HOOK_URL

# Frontend (Vercel)
# Automatic on push to main branch
```

### Production Checklist

- [ ] All tests pass
- [ ] Environment variables set in production
- [ ] Database migrations run
- [ ] Security scan clean
- [ ] No hardcoded secrets
