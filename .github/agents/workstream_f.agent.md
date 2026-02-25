


---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name: workstream_f
description: handles workstream f
---

# My Agent

Reference the document, ./docs/COPILOT_PLAN.md and ./docs/DESIGN_SPEC.md for details...

Your portion of ./docs/COPILOT_PLAN.md:

## Workstream F: Plugins & Extensibility (Owner: plugin interfaces)
- Define plugin discovery via entry points (e.g., `devflow.plugins`) and/or config-provided module paths; allow registration of new commands/tasks at startup.
- Specify a minimal plugin interface (e.g., `register(registry: CommandRegistry, app: AppContext)`) and document lifecycle expectations.
- Provide a sample plugin under `tests/fixtures/plugins` that adds a trivial command/task; ensure help text and execution integrate seamlessly with global flags.
- Output: tests verifying plugin discovery, registration, precedence rules, and failure isolation (bad plugin should not crash core).
- **Ownership boundary:** Plugin interface is defined here; other streams should consume it but not change its shape without coordination.