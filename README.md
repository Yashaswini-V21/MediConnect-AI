# MediConnect AI

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Frontend](https://img.shields.io/badge/Frontend-React_18-61DAFB?style=for-the-badge&logo=react&logoColor=white)](frontend)
[![Backend](https://img.shields.io/badge/Backend-Flask_3-000000?style=for-the-badge&logo=flask&logoColor=white)](backend)
[![Auth](https://img.shields.io/badge/Auth-Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com/)
[![Internship](https://img.shields.io/badge/IBM_SkillBuild-Edunet_AIML-0F62FE?style=for-the-badge&logo=ibm&logoColor=white)](https://skillsbuild.org/)

AI-powered healthcare navigation platform for faster, safer, and multilingual access to care.

[Quick Start](#quick-start) | [Architecture](#system-architecture) | [Data Flow](#data-flow-diagram) | [Tech Stack](#tech-stack)

</div>

## About Project
MediConnect AI is a full-stack healthcare assistant that helps users analyze symptoms, discover hospitals, and navigate emergency situations in English and Kannada with an AI-supported experience.

## Internship Capstone Context
- Program: IBM SkillBuild AIML Internship
- Partner: Edunet Foundation
- Project Type: Capstone Project
- Focus: Real-world healthcare accessibility with AI/ML, multilingual UX, and emergency-first workflows

## Table of Contents
- [Key Highlights](#key-highlights)
- [What Is New](#what-is-new)
- [Core Features](#core-features)
- [System Architecture](#system-architecture)
- [Data Flow Diagram](#data-flow-diagram)
- [Agentic Lightning Flow](#agentic-lightning-flow)
- [Security and Privacy](#security-and-privacy)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Firebase Auth Setup](#firebase-auth-setup)
- [API Snapshot](#api-snapshot)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)

## Key Highlights
- Bilingual support for English and Kannada
- Symptom-aware navigation to hospitals and specialists
- Emergency-first flows with map-based decisions
- AI chat assistant for healthcare guidance
- Clean Firebase authentication integration in frontend
- Modular Flask backend with route-based APIs

## What Is New
- Firebase Auth migration for frontend login/signup/session flows
- Cleaner auth context and token forwarding strategy
- Improved auth error messaging for faster troubleshooting
- README modernization with architecture and data-flow diagrams
- Cleanup of obsolete auth client and placeholder link artifacts

## Core Features

### Patient Experience
- Guided symptom entry with voice-ready input path
- AI chat doctor for general health Q and A
- Multi-page health dashboard (profile, reminders, analytics, reports)
- Emergency utility pages and first-aid guidance

### Clinical Navigation
- Hospital discovery with map integration
- Distance and emergency-based prioritization
- Specialist mapping based on symptom patterns
- Quick action pathways for urgent care

### Platform Engineering
- React SPA with route-level protection
- Flask API with modular routes and services
- Data-backed symptom, hospital, and specialty layers
- Extensible architecture for AI and translation providers

## System Architecture

```mermaid
flowchart TD
    U[User Web Client] --> FE[React Frontend]
    FE --> AUTH[Firebase Authentication]
    FE --> API[Flask Backend API]

    API --> R1[Auth Routes]
    API --> R2[Symptom Routes]
    API --> R3[Hospital Routes]
    API --> R4[Chat Routes]
    API --> R5[Appointment Routes]

    R2 --> M1[Symptom Analyzer]
    R3 --> M2[Hospital Matcher]
    R4 --> S1[AI Service Layer]
    R4 --> S2[Translation Service Layer]

    API --> DB[(SQLite)]
    M1 --> D1[(Symptoms Data)]
    M2 --> D2[(Hospitals Data)]
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Firebase
    participant Backend
    participant AI
    participant Data

    User->>Frontend: Enter symptoms / ask health question
    Frontend->>Firebase: Validate session
    Firebase-->>Frontend: ID token
    Frontend->>Backend: API request + Bearer token
    Backend->>Data: Load symptom/hospital context
    Backend->>AI: Request triage/advice
    AI-->>Backend: Structured response
    Backend-->>Frontend: Recommendations + urgency + navigation data
    Frontend-->>User: UI cards, map actions, chat response
```

## Agentic Lightning Flow

MediConnect follows an agentic-light design where each stage has a clear responsibility and safe fallback behavior.

```mermaid
flowchart LR
    A[User Input EN/KN] --> B[Symptom Parser Agent]
    B --> C[Risk and Severity Agent]
    C --> D[Care Navigation Agent]
    D --> E[Response Composer Agent]
    E --> F[User Output: Advice + Hospital + Next Steps]

    C --> G{High Risk?}
    G -- Yes --> H[Emergency Path]
    H --> F

    E --> I{AI Failure?}
    I -- Yes --> J[Rule-based Fallback]
    J --> F
```

Why this helps:
- Better explainability for internship demonstrations
- Easier debugging and evaluation per stage
- Safe degraded behavior when AI providers fail

## Security and Privacy

MediConnect is designed with practical security controls for student-project to production-readiness progression.

### Implemented
- Firebase authentication in frontend flows
- Token forwarding via Authorization header
- Backend route protection framework with JWT checks
- Input validation and guarded request handling
- Environment variable based secret configuration
- CORS policies and deployment-aware API access

### Planned hardening
- Firebase ID token verification on backend protected routes
- Role-based access and stricter endpoint authorization
- Structured audit logging for auth-sensitive actions
- Data minimization for chat and health-event telemetry

### Security model overview

```mermaid
flowchart TD
    U[Authenticated User] --> FE[Frontend App]
    FE --> T[Firebase ID Token]
    T --> API[Backend API]
    API --> V[Token Verification Middleware]
    V --> P[Protected Routes]
    P --> D[(App Data)]
```

## Tech Stack

### Frontend
- React 18
- Tailwind CSS
- Framer Motion
- Axios
- Recharts
- Lucide React
- Firebase Web SDK

### Backend
- Python 3.10+
- Flask 3
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-Bcrypt
- Geopy
- Requests
- OpenAI SDK integration layer

### Data and Integrations
- SQLite for application persistence
- JSON data sources for hospitals, symptoms, specialties
- Firebase Auth for frontend identity
- Google Maps JavaScript API for map experience

## Project Structure

```text
Healthbridge-AI/
|- backend/
|  |- app.py
|  |- routes/
|  |- models/
|  |- utils/
|  |- data/
|  `- requirements.txt
|- frontend/
|  |- src/
|  |  |- components/
|  |  |- pages/
|  |  |- services/
|  |  |- hooks/
|  |  |- context/
|  |  `- styles/
|  |- public/
|  `- package.json
|- docs/
|- public/
`- README.md
```

## Quick Start

### Prerequisites
- Node.js 18+
- npm 9+
- Python 3.10+
- Firebase project (for auth)

### 1) Clone
```bash
git clone https://github.com/Yashaswini-V21/Healthbridge-AI.git
cd Healthbridge-AI
```

### 2) Backend setup
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

Backend runs on: http://localhost:5000

### 3) Frontend setup
```bash
cd ../frontend
npm install
npm start
```

Frontend runs on: http://localhost:3000

## Environment Configuration

### Frontend
Create local runtime config in `frontend/.env.local`:

```env
REACT_APP_API_URL=http://localhost:5000
REACT_APP_FIREBASE_API_KEY=
REACT_APP_FIREBASE_AUTH_DOMAIN=
REACT_APP_FIREBASE_PROJECT_ID=
REACT_APP_FIREBASE_APP_ID=
REACT_APP_GOOGLE_MAPS_API_KEY=
```

Reference template: `frontend/.env.example`

### Backend
Create `backend/.env` using `backend/.env.example` as reference.

## Firebase Auth Setup
1. Open Firebase Console and create/select project.
2. Add a Web App in project settings.
3. Copy config values to `frontend/.env.local`.
4. Enable Email/Password in Authentication -> Sign-in method.
5. Ensure authorized domains include `localhost`.
6. Restart frontend dev server.

## API Snapshot

Common route groups:
- `/api/auth/*`
- `/api/symptoms/*`
- `/api/hospitals/*`
- `/api/chat/*`
- `/api/appointments/*`

Health endpoint:
- `GET /api/health`

## Roadmap
- Backend Firebase ID token verification for protected routes
- Agentic-light triage pipeline (parse -> risk -> navigator)
- Expanded bilingual voice workflow
- Reliability dashboard and model fallback analytics
- More tests across API and critical UI journeys

## Contributing
See `CONTRIBUTING.md` for issue flow, branch naming, commit style, and PR checklist.

## Disclaimer
MediConnect provides educational and navigation assistance and is not a substitute for professional medical diagnosis, treatment, or emergency services.

---

Simple summary: MediConnect AI is a multilingual healthcare navigation assistant that turns symptom input into practical care guidance and faster hospital access.

Maintained by: **@Yashaswini-V21**
