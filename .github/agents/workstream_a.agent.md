---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name: workstream_a
description: handles workstream A
---

# My Agent

Reference the document, ./docs/COPILOT_PLAN.md and ./docs/DESIGN_SPEC.md for details...

Your portion of ./docs/COPILOT_PLAN.md:

Workstream A: Project Bootstrap & App Context (Owner: core config/app)
- Create package layout (`devflow/cli.py`, `app.py`, `config/`, `commands/`, `core/`, `plugins/`, `tests/`) matching the proposed tree.
- Implement project-root detection walking upward until `pyproject.toml` or `devflow.toml` is found; expose override via `--project-root`.
- Implement configuration discovery order: explicit `--config`, `[tool.devflow]` in `pyproject.toml`, `devflow.toml`, user-level default (placeholder hook), then built-in defaults.
- Define typed config schema mirroring the sample TOML: `venv_dir`, `default_python`, `build_backend`, `test_runner`, `package_index`, `[paths]`, `[publish]`, `[deps]`, `[tasks.*]`, pipelines vs single tasks, and boolean flags (`auto_discover_tasks`, `tag_on_publish`, `require_clean_working_tree`, etc.).
- Provide config validation tests and root-detection tests; include default-merging tests that show project overrides taking precedence.
- Deliver `AppContext` encapsulating project root, loaded config, logger, verbosity, dry-run flag, and command registry. Ensure the `__version__` flag prints package version per the design.
- Output: runnable `devflow --help` stub listing top-level commands (even if not fully implemented yet) with placeholder handlers.
- **Ownership boundary:** Other streams import `AppContext` and config models; they must not redefine them. Any schema changes should be coordinated here.
