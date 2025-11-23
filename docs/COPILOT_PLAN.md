# Devflow Multi-Agent Implementation Plan

This document packages the design white paper into actionable, parallelizable tracks that can be handed to multiple GitHub Copilot agents. Each track produces mergeable, testable increments that converge into a usable `devflow` CLI. The goal is to preserve as much fidelity to the original design spec as possible while enabling fast, concurrent implementation.

## Reference Pointers for Agents (Do Not Skip)
- Read the “Design White Paper” (`docs/DESIGN_SPEC.md`); the plan below maps directly to FR/NFR/UX requirements called out there.
- Use Typer for CLI scaffolding, Pydantic (or dataclasses) for config schema, TOML parsing via `tomllib`/`tomli`.
- Preserve the default config surface proposed in the white paper (e.g., `venv_dir`, `default_python`, `build_backend`, `test_runner`, `paths`, `publish`, `deps`, `tasks`).
- Respect global flags everywhere: `--config`, `--project-root`, `--dry-run`, `--verbose/-v`, `--quiet/-q`, `--version`.
- All subprocesses must be executed with explicit arg lists (`shell=False`), and all commands must honor `--dry-run` and verbosity.

## Cross-Stream Traceability Matrix (Design Spec → Workstreams)
- FR1–FR3 (Unified CLI & custom tasks): primarily Workstreams A/B/G.
- FR4–FR6 (Configuration discovery & schema): Workstream A with tests; consulted by all others.
- FR7–FR10 (Venv/deps): Workstream C.
- FR11–FR13 (Test/build/publish): Workstream D.
- FR14–FR15 (Git integration/versioning): Workstream E.
- FR16–FR17 (Plugins/extensibility): Workstream F.
- NFRs/UX (logging, help, portability, completion): Workstreams B/G with shared helpers from A.
- Evidence strategy & CI matrix: Workstream H.

## Operating Principles for All Agents
- Keep logic Python-native—no shell-specific assumptions.
- Prefer Typer for CLI ergonomics (subcommands, help, completion).
- Centralize configuration under `[tool.devflow]` in `pyproject.toml`, with `devflow.toml` fallback.
- Use structured logging with verbosity flags and a `--dry-run` switch respected by every command.
- Ensure task execution uses explicit argument lists for subprocesses (no shell=True).
- Provide unit tests for new modules and integration tests for user-visible flows.

## Workstream A: Project Bootstrap & App Context
- Create package layout (`devflow/cli.py`, `app.py`, `config/`, `commands/`, `core/`, `plugins/`, `tests/`) matching the proposed tree.
- Implement project-root detection walking upward until `pyproject.toml` or `devflow.toml` is found; expose override via `--project-root`.
- Implement configuration discovery order: explicit `--config`, `[tool.devflow]` in `pyproject.toml`, `devflow.toml`, user-level default (placeholder hook), then built-in defaults.
- Define typed config schema mirroring the sample TOML: `venv_dir`, `default_python`, `build_backend`, `test_runner`, `package_index`, `[paths]`, `[publish]`, `[deps]`, `[tasks.*]`, pipelines vs single tasks, and boolean flags (`auto_discover_tasks`, `tag_on_publish`, `require_clean_working_tree`, etc.).
- Provide config validation tests and root-detection tests; include default-merging tests that show project overrides taking precedence.
- Deliver `AppContext` encapsulating project root, loaded config, logger, verbosity, dry-run flag, and command registry. Ensure the `__version__` flag prints package version per the design.
- Output: runnable `devflow --help` stub listing top-level commands (even if not fully implemented yet) with placeholder handlers.

## Workstream B: Command Framework & Task Engine
- Define `Command` base (name/help/run) and registry to map string names to handler classes; integrate with Typer command factory.
- Implement `Task`/`Pipeline` abstractions matching the spec: per-task `use_venv`, env overrides, argument lists, sequencing, and exit code propagation. Support composite `pipeline` tasks and single-command tasks as shown in config examples.
- Provide executor-level logging with phase prefixes (e.g., `[test]`, `[build]`), honor `--dry-run`, verbosity levels (`-q`, `-v`, `-vv`), and consistent non-zero exit code propagation.
- Add `devflow task <name>` to execute custom tasks from config; include clear error messaging for missing tasks and recursive pipeline expansion with cycle detection.
- Output: unit tests covering pipeline expansion, dry-run behavior, env propagation, and exit-code short-circuiting; short “how to define tasks” section in docs.

## Workstream C: Venv & Dependency Management
- Implement `devflow venv init` honoring `default_python`, `venv_dir`, `--python`, and `--recreate`; ensure idempotent creation with clear logs.
- Implement venv-aware command runner helpers (used by other streams) to ensure subprocesses execute inside the configured venv; expose path helpers in `core/paths.py`.
- Implement `devflow deps sync` to install from `requirements.txt`/`pyproject`/`requirements-*.txt` according to config; allow optional extras/groups hooks even if stubbed.
- Implement `devflow deps freeze` writing to configured `freeze_output` path; ensure deterministic ordering and include dry-run preview.
- Output: integration tests with temp projects validating venv creation, sync, freeze output, and path resolution on Linux/macOS/WSL Git Bash where feasible.

## Workstream D: Test, Build, and Publish Commands
- Implement `devflow test` with pass-through args to configured runner (`pytest` default; allow `unittest`, `tox`, etc.) and venv enforcement; expose common flags (`--pattern`, `--marker`, `--cov`) pass-through.
- Implement `devflow build` defaulting to `python -m build` with configurable backend (`hatchling`, `poetry-build`, etc.) and configurable dist directory cleanup behavior.
- Implement `devflow publish` pipeline respecting config flags: require clean working tree (unless `--allow-dirty`), optional pre-tests, build artifacts, upload via `twine` (repository configurable), optional signing, and tag creation following `tag_format`. Add `--dry-run` to show would-be actions.
- Output: integration tests covering happy-path, failing test/build/upload, tag formatting, and dry-run behavior that does not perform network operations.

## Workstream E: Git Integration & Safety Rails
- Implement git helper module for status checks, tag existence/creation, and version reporting (e.g., from `setuptools_scm` or config fallback) aligned with FR14–FR15.
- Support config flags: `require_clean_working_tree`, `tag_on_publish`, `tag_format`, `tag_prefix`, and optional `version_source`. Provide clear error messages when the working tree is dirty.
- Add reusable pre-flight checks for publish and optional CI guardrails; consider `devflow git status`/`devflow version` utility commands if feasible.
- Output: tests using temp git repos to validate blocking behavior, tag formatting, idempotent tagging, and version surfacing.

## Workstream F: Plugins & Extensibility
- Define plugin discovery via entry points (e.g., `devflow.plugins`) and/or config-provided module paths; allow registration of new commands/tasks at startup.
- Specify a minimal plugin interface (e.g., `register(registry: CommandRegistry, app: AppContext)`) and document lifecycle expectations.
- Provide a sample plugin under `tests/fixtures/plugins` that adds a trivial command/task; ensure help text and execution integrate seamlessly with global flags.
- Output: tests verifying plugin discovery, registration, precedence rules, and failure isolation (bad plugin should not crash core).

## Workstream G: UX, Completion, and Documentation
- Implement `devflow completion <shell>` generation (bash/zsh/fish) and document usage (`eval "$(devflow completion zsh)"`).
- Ensure `devflow` with no args lists available commands and project-specific tasks (discoverable UX per R-CLI2).
- Enrich help text with examples reflecting config patterns from the design (custom tasks, pipelines, publish dry-run, venv init options).
- Maintain a Quickstart section mirroring the sample TOML from the design white paper and a troubleshooting section for portability issues (macOS/Linux/WSL).
- Output: documentation updates plus snapshot/CLI help tests as feasible.

## Workstream H: CI, Packaging, and Evidence
- Add `pyproject.toml` with console_scripts entry for `devflow`, runtime deps (typer, pydantic, tomli/tomllib backport if needed), and dev extras (pytest, ruff, build, twine for tests).
- Set up CI workflow: lint (ruff), type-check (if enabled), unit + integration tests. Plan matrix for `ubuntu-latest`, `macos-latest`, `windows-latest` (Git Bash/WSL) per portability NFRs.
- Encode acceptance tests mirroring the scenarios in the white paper (venv/test/build/publish dry-run, ci-check pipeline, git cleanliness failure) and capture logs/artifacts for evidence.
- Output: CI config plus baseline badges/README pointers; ensure deterministic exit codes and log snapshots for regressions.

## Coordination Checklist
- Establish shared config schema file (`config/schema.py`) and defaults to avoid drift; every workstream consumes the same models.
- Align on logging format, verbosity flags, phase prefixing, and dry-run semantics early; reuse across commands and tests.
- Favor small, mergeable PRs per workstream; keep integration tests green and avoid overlapping edits to schema or core helpers without coordination.
- Cross-reference acceptance scenarios from the design white paper and update this plan as evidence accumulates.
