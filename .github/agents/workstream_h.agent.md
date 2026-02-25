---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name: workstream_h
description: handles workstream h
---

# My Agent

Reference the document, ./docs/COPILOT_PLAN.md and ./docs/DESIGN_SPEC.md for details...

Your portion of ./docs/COPILOT_PLAN.md:


## Workstream H: CI, Packaging, and Evidence (Owner: CI/packaging)
- Add `pyproject.toml` with console_scripts entry for `devflow`, runtime deps (typer, pydantic, tomli/tomllib backport if needed), and dev extras (pytest, ruff, build, twine for tests).
- Set up CI workflow: lint (ruff), type-check (if enabled), unit + integration tests. Plan matrix for `ubuntu-latest`, `macos-latest`, `windows-latest` (Git Bash/WSL) per portability NFRs.
- Encode acceptance tests mirroring the scenarios in the white paper (venv/test/build/publish dry-run, ci-check pipeline, git cleanliness failure) and capture logs/artifacts for evidence.
- Output: CI config plus baseline badges/README pointers; ensure deterministic exit codes and log snapshots for regressions.
- **Ownership boundary:** This stream owns packaging and CI configuration; others should not modify CI/workflow files without alignment.
