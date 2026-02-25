---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name: workstream_g
description: handles workstream G
---

# My Agent

Reference the document, ./docs/COPILOT_PLAN.md and ./docs/DESIGN_SPEC.md for details...

Your portion of ./docs/COPILOT_PLAN.md:



## Workstream G: UX, Completion, and Documentation (Owner: UX/docs)
- Implement `devflow completion <shell>` generation (bash/zsh/fish) and document usage (`eval "$(devflow completion zsh)"`).
- Ensure `devflow` with no args lists available commands and project-specific tasks (discoverable UX per R-CLI2).
- Enrich help text with examples reflecting config patterns from the design (custom tasks, pipelines, publish dry-run, venv init options).
- Maintain a Quickstart section mirroring the sample TOML from the design white paper and a troubleshooting section for portability issues (macOS/Linux/WSL).
- Output: documentation updates plus snapshot/CLI help tests as feasible.
- **Ownership boundary:** This stream edits docs and help/UX strings but should not modify command semantics or core logic.