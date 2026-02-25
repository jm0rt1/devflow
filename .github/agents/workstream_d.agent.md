---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name: workstream_d
description: handles d
---

# My Agent

Reference the document, ./docs/COPILOT_PLAN.md and ./docs/DESIGN_SPEC.md for details...

Your portion of ./docs/COPILOT_PLAN.md:

## Workstream D: Test, Build, and Publish Commands (Owner: test/build/publish commands)
- Implement `devflow test` with pass-through args to configured runner (`pytest` default; allow `unittest`, `tox`, etc.) and venv enforcement; expose common flags (`--pattern`, `--marker`, `--cov`) pass-through.
- Implement `devflow build` defaulting to `python -m build` with configurable backend (`hatchling`, `poetry-build`, etc.) and configurable dist directory cleanup behavior.
- Implement `devflow publish` pipeline respecting config flags: require clean working tree (unless `--allow-dirty`), optional pre-tests, build artifacts, upload via `twine` (repository configurable), optional signing, and tag creation following `tag_format`. Add `--dry-run` to show would-be actions.
- Output: integration tests covering happy-path, failing test/build/upload, tag formatting, and dry-run behavior that does not perform network operations.
- **Ownership boundary:** This stream plugs into task engine and venv/git helpers; it must not redefine config models, task execution, or git helpers.
