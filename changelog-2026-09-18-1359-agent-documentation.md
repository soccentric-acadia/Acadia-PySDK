# Changelog: Agent documentation standardization

**Completed:** 2026-09-18 13:59 PDT

## Changed

- Added `Plan.md` and `Task.md` ignore rules for local task workflow artifacts.
- Added an `AGENTS.md` pointer and replaced the detailed root `CLAUDE.md` with
  a pointer to the canonical document.
- Kept the canonical document limited to title, summary, and Python validation
  and distribution-build instructions.

## Validation

- Verified the pointer files and canonical document meet the required shape.
- Verified `make check` and `make build` are declared Makefile targets.
