#!/usr/bin/env bash
# Start the MediConnect-AI stack locally (Unix/macOS)
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "No .env file found. Creating from .env.example..."
  cp .env.example .env
  echo "Please edit .env and set SARVAM_API_KEY and ADMIN_SECRET_TOKEN before continuing."
  ${EDITOR:-vi} .env
  read -p "Press Enter after editing .env to continue or Ctrl+C to cancel"
fi

echo "Starting services with docker-compose..."
docker-compose up --build -d

echo "Services started. Follow backend logs with: docker-compose logs -f backend"
echo "To run the seed script inside the backend container (create demo accounts):"
echo "  docker-compose exec backend python backend/scripts/seed_accounts.py"
