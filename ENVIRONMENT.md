ENVIRONMENT & Secrets Guide
==========================

This project uses environment variables for secrets and configuration. Never commit real secrets to the repository.

Files
-----

- `backend/.env.example` — Example variables for the backend.
- `frontend/.env.example` — Example variables for the frontend.
- `backend/.env` and `frontend/.env.local` — Local files used for development (should be in `.gitignore`).

Key recommendations
-------------------

1. Keep secrets out of git. Add runtime secrets via your host (Render, Vercel, Docker secrets, or CI secrets).
2. Rotate any secrets that were previously exposed in this repository immediately (Firebase API key, GROQ keys, etc.).
3. Use `git filter-repo` or BFG to remove secrets from history if needed — this is destructive and requires force-push.

Quick local setup
-----------------

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
# Edit the files and fill in secrets locally; do NOT commit them.
```

Production checks
-----------------

The backend will refuse to start in production if critical env vars are missing (`SECRET_KEY`, `JWT_SECRET_KEY`, `ADMIN_SECRET_TOKEN`). Ensure your deployment config provides these.

Secrets removal guidance (optional)
----------------------------------

If you need to scrub secrets from git history, consider these steps (replace `<branch>` and `<pattern>`):

```bash
# Recommended: install git-filter-repo
pip install git-filter-repo

# Example: remove a file with secrets
git filter-repo --path backend/.env --invert-paths

# After rewriting history, force-push branches and notify collaborators
git push --force --all
git push --force --tags
```

If you want, I can prepare a non-destructive script and instructions for secret removal and rotation.
