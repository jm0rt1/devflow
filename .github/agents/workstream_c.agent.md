---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name: workstream-c
description: handles workstream c
---

# My Agent

Reference the document, ./docs/COPILOT_PLAN.md and ./docs/DESIGN_SPEC.md for details...

Your portion of ./docs/COPILOT_PLAN.md:

Workstream C: Venv & Dependency Management (Owner: venv/deps helpers)
- Implement `devflow venv init` honoring `default_python`, `venv_dir`, `--python`, and `--recreate`; ensure idempotent creation with clear logs.
- Implement venv-aware command runner helpers (used by other streams) to ensure subprocesses execute inside the configured venv; expose path helpers in `core/paths.py`.
- Implement `devflow deps sync` to install from `requirements.txt`/`pyproject`/`requirements-*.txt` according to config; allow optional extras/groups hooks even if stubbed.
- Implement `devflow deps freeze` writing to configured `freeze_output` path; ensure deterministic ordering and include dry-run preview.
- Output: integration tests with temp projects validating venv creation, sync, freeze output, and path resolution on Linux/macOS/WSL Git Bash where feasible.
- **Ownership boundary:** Other streams call venv/deps helpers rather than spawning their own env logic. Coordinate any needed helper changes with this stream.
