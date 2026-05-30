#!/bin/bash
# Non-destructive instructions to remove secrets from git history.
# Read and follow carefully — rewriting history is destructive and requires force-push.

set -euo pipefail

echo "This script prints recommended commands to remove secrets from Git history."
echo "It will NOT run destructive commands automatically. Review before executing."

cat <<'EOF'
1) Install git-filter-repo (preferred):

   pip install git-filter-repo

2) Back up your current repo (always):

   git bundle create repo-backup.bundle --all

3) Example: remove files that contained secrets (e.g. backend/.env):

   git filter-repo --invert-paths --paths backend/.env

   # or remove any file matching a pattern:
   # git filter-repo --path-glob 'backend/*.env' --invert-paths

4) After rewriting history, force-push all branches and tags:

   git push --force --all
   git push --force --tags

5) Inform all collaborators to re-clone the repository.

Notes:
- Use these commands only if you are the repository owner or have coordinated with the team.
- Alternatively, rotate the exposed secrets and keep the history (less destructive).
EOF

echo "Instructions written above. If you'd like, I can prepare a PR with a sample git-filter-repo config." 
