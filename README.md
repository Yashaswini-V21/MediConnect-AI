# MediConnect-AI

A concise, production-oriented README and project structure overview for the MediConnect-AI repository.

## Quick links
- Demo: https://mediconnect-ai-nu.vercel.app
- API docs: docs/API_DOCUMENTATION.md
- Deployment notes: docs/DEPLOYMENT.md

---

## Purpose
MediConnect-AI is a healthcare platform combining symptom triage, hospital matching, and admin tooling with AI-powered assistants. This repository contains the backend (Flask), frontend (React), and supporting utilities, models, and integration scripts.

---

## Quick start (local development)
1. Create a Python virtual environment and install backend requirements:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r backend/requirements.txt
```

2. Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

3. Copy example env files and fill secrets locally (do not commit real secrets):

```bash
cp backend/.env.example backend/.env
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

4. Run backend (development):

```bash
export FLASK_ENV=development
python -m backend.app
# or use: flask --app backend.app run
```

5. Run frontend (development):

```bash
cd frontend
npm start
```

---

## Files & Folder structure
Short overview of the repository layout:

- `backend/` — Flask backend: `app.py`, `routes/`, `models/`, `utils/`, `requirements.txt`.
- `frontend/` — React frontend: `src/`, `public/`, `package.json`.
- `instance/` — Local instance data for development.
- `scripts/` — Setup and helper scripts.
- `docs/` — legacy docs (removed); core documentation now lives in this `README.md` and `ENVIRONMENT.md`.

Keep the tree minimal and avoid committing secrets; see `ENVIRONMENT.md` for environment variable guidance.

---

## Environment variables
- `backend/.env.example` contains variables required by the backend.
- `frontend/.env.example` contains variables required by the frontend.

Do NOT commit real secrets. Use a secrets manager or CI-provided secrets for production.

---

## Contributing
- Open an issue for major changes. Use feature branches and create pull requests.
- Add unit tests for new functionality and run linters before PR.

---

## License
This project is licensed under the MIT License. See `LICENSE` for details.
