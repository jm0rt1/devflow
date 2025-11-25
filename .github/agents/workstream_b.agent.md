---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name: workstream_b
description: handles workstream_b
---

# My Agent

Reference the document, ./docs/COPILOT_PLAN.md and ./docs/DESIGN_SPEC.md for details...

Your portion of ./docs/COPILOT_PLAN.md:

Workstream B: Command Framework & Task Engine (Owner: task/registry)
- Define `Command` base (name/help/run) and registry to map string names to handler classes; integrate with Typer command factory.
- Implement `Task`/`Pipeline` abstractions matching the spec: per-task `use_venv`, env overrides, argument lists, sequencing, and exit code propagation. Support composite `pipeline` tasks and single-command tasks as shown in config examples.
- Provide executor-level logging with phase prefixes (e.g., `[test]`, `[build]`), honor `--dry-run`, verbosity levels (`-q`, `-v`, `-vv`), and consistent non-zero exit code propagation.
- Add `devflow task <name>` to execute custom tasks from config; include clear error messaging for missing tasks and recursive pipeline expansion with cycle detection.
- Output: unit tests covering pipeline expansion, dry-run behavior, env propagation, and exit-code short-circuiting; short “how to define tasks” section in docs.
- **Ownership boundary:** Only this stream defines `Command` base/registry and task execution semantics. Other streams register commands through provided hooks and must not reimplement dispatch or pipeline logic.
