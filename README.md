# MediConnect AI

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Frontend: React](https://img.shields.io/badge/Frontend-React_18-61DAFB?style=for-the-badge&logo=react&logoColor=white)](frontend)
[![Backend: Flask](https://img.shields.io/badge/Backend-Flask_3-000000?style=for-the-badge&logo=flask&logoColor=white)](backend)
[![Auth: Firebase](https://img.shields.io/badge/Auth-Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com/)

AI-powered healthcare navigation platform built for IBM SkillBuild + Edunet AIML internship.

</div>

## Why MediConnect
MediConnect helps users quickly move from symptoms to care.

- Bilingual experience for English and Kannada users
- AI-assisted symptom analysis and guidance
- Fast nearby hospital discovery with map navigation
- Emergency-first UX with one-tap critical paths

## Current Stack

### Frontend
- React 18
- Tailwind CSS
- Framer Motion
- Axios
- Firebase Authentication (Email/Password)

### Backend
- Flask 3
- SQLAlchemy
- JWT-protected routes (migration to Firebase token verification in progress)
- AI and translation service integrations

## Architecture

```text
User -> React Frontend -> Flask API -> Data + AI Services
           |                |
           |                +-> Symptom, hospital, chat routes
           +-> Firebase Auth
```

## Feature Highlights
- Symptom checker with urgency triage hints
- AI chat doctor experience
- Hospital finder with map cards and emergency emphasis
- Health profile, reminders, and appointment utilities
- Voice-ready input flow in EN/KN

## Local Setup

### Prerequisites
- Node.js 18+
- Python 3.10+
- Firebase project with Authentication enabled

### 1. Clone
```bash
git clone https://github.com/Yashaswini-V21/Healthbridge-AI.git
cd Healthbridge-AI
```

### 2. Backend
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Backend default: http://localhost:5000

### 3. Frontend
```bash
cd ../frontend
npm install
npm start
```

Frontend default: http://localhost:3000

## Environment Variables

### Frontend: frontend/.env.development
```env
REACT_APP_API_URL=http://localhost:5000
REACT_APP_FIREBASE_API_KEY=
REACT_APP_FIREBASE_AUTH_DOMAIN=
REACT_APP_FIREBASE_PROJECT_ID=
REACT_APP_FIREBASE_APP_ID=
REACT_APP_GOOGLE_MAPS_API_KEY=
```

### Backend: backend/.env
Use backend/.env.example as reference and set keys for your deployment.

## Firebase Auth Setup (Issue #1)
1. Create/open your Firebase project
2. Add Web app in Project settings
3. Copy Firebase config to frontend .env.development
4. Enable Email/Password in Authentication -> Sign-in method
5. Ensure localhost is in Authentication -> Settings -> Authorized domains
6. Restart frontend server

## Roadmap
- Complete backend verification of Firebase ID tokens on protected APIs
- Add agentic-light triage pipeline (parser -> risk -> navigator)
- Improve bilingual voice workflow and reliability metrics
- Add reliability dashboard and benchmark suite

## Contributing
Please read CONTRIBUTING.md for workflow, branch strategy, and PR quality checklist.

## Disclaimer
MediConnect provides educational and navigation support only. It is not a replacement for licensed medical diagnosis or emergency medical services.
