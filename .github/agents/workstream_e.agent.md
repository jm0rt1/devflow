---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name:workstream_e
description:
---

# My Agent

Reference the document, ./docs/COPILOT_PLAN.md and ./docs/DESIGN_SPEC.md for details...

Your portion of ./docs/COPILOT_PLAN.md:
## Workstream E: Git Integration & Safety Rails (Owner: git helpers)
- Implement git helper module for status checks, tag existence/creation, and version reporting (e.g., from `setuptools_scm` or config fallback) aligned with FR14–FR15.
- Support config flags: `require_clean_working_tree`, `tag_on_publish`, `tag_format`, `tag_prefix`, and optional `version_source`. Provide clear error messages when the working tree is dirty.
- Add reusable pre-flight checks for publish and optional CI guardrails; consider `devflow git status`/`devflow version` utility commands if feasible.
- Output: tests using temp git repos to validate blocking behavior, tag formatting, idempotent tagging, and version surfacing.
- **Ownership boundary:** Other streams call git helpers; they should not shell out to git directly or recreate cleanliness checks.
