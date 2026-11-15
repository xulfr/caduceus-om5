# Shared agent instructions

These rules apply to Codex, Claude Code and other coding agents.

## Project

Repository: xulfr/caduceus-om5.

The project modifies OM System camera firmware. Incorrect patches
may cause physical-camera failures.

OM-5 Mark II (E148, firmware 1.1) is the primary target.
Original OM-5 (E144, firmware 1.2) is a separate, less-validated
target. Never transfer validation claims between models.

Read HANDOVER.md for current status. Read docs/INDEX.md to
locate detailed technical documentation.

## Starting a session

1. Check `git status`, current branch and recent commits.
2. Read this file and HANDOVER.md.
3. Identify the specific task and affected subsystem.
4. Read only relevant source, tests and documentation.
5. Check for another agent's uncommitted work.
6. Do not repeat previously documented investigations
   without a reason.

Do not automatically read the entire research directory,
historical logs or full test outputs.

## Development

- Make the smallest coherent change that solves the task.
- Prefer existing architecture and established firmware hooks.
- Avoid unrelated refactoring.
- Record new verified reverse-engineering findings.
- Distinguish observation, inference and hypothesis.
- Preserve negative test results.
- Never conceal failed audits by changing expected hashes.
- Never modify stock firmware artefacts to satisfy tests.
- Do not distribute proprietary stock firmware or full
  patched firmware images.

Respect existing licensing, attribution and NOTICE files.

## Firmware safety

A successful build is not proof that firmware boots.

An emulator result is not a physical-camera result.

Use "camera-tested" only when an explicit physical-camera
report records:
- Camera model and stock firmware version.
- Exact package SHA-256.
- Test procedure.
- Observed result.

The owner performs all physical-camera flashing.

Do not initiate camera updates.

Do not mark a build camera-tested without owner evidence.

Do not publish releases without explicit owner approval.

Preserve the existing installer warnings, compatibility
restrictions, preimage checks, section-bound checks,
compression checks and integrity checks.

Do not weaken safety assertions to make tests pass.

## Testing

Use the smallest sufficient test scope.

Run:

    python scripts/check.py fast

for ordinary changes.

Run:

    python scripts/check.py integration

for changes affecting firmware behaviour, hooks, memory,
resource layout, startup or image generation, provided
the required external tools and firmware are available.

Run:

    python scripts/check.py full

before proposing a release candidate or physical-camera
test package, where the environment supports it.

The test runner must never imply success for checks that
were skipped or could not be executed.

A targeted test is acceptable during development.
Before integrating a firmware change, consider whether
the affected subsystem needs broader regression testing.

Never use cached results when relevant inputs have changed.

Do not run the entire emulator suite after documentation-only
changes unless a specific dependency justifies it.

Keep raw logs in generated/ or another ignored directory.
Report concise results, with paths to detailed logs.

## Git workflow

- Treat main as the integration branch.
- Prefer short-lived branches for substantial work.
- Commit small, coherent increments.
- Push committed work regularly.
- Push before ending a session where credentials permit.
- Never discard another agent's uncommitted work.
- Never force-push.
- Never rewrite shared history.
- Never merge known-failing changes into main.
- Do not commit stock firmware, secrets, generated binaries
  or large test logs.
- Do not publish releases without explicit approval.

For an active feature branch, push to its corresponding
remote branch. Do not silently merge it into main.

If pushing fails, retain the local commits and report the
failure. Never claim the work was backed up remotely.

Before approaching context exhaustion, commit coherent
work, push it, and update HANDOVER.md.

Do not create meaningless commits solely to produce a
checkpoint. If work is incomplete, use a clearly labelled
WIP commit on a development branch where appropriate.

## Documentation

HANDOVER.md is a concise current-state document.

It should contain:
- Latest known-good physical-camera baseline.
- Current active work.
- Known blockers.
- Validation still required.
- Immediate next actions.
- Links to detailed evidence.

Keep it approximately 150 lines or fewer.

Do not append chronological session transcripts.

Move durable technical findings into topic-specific docs.
Preserve exact addresses, hashes, observations and failed
experiments where they may be useful.

Remove resolved items from the active handover only after
their important findings are preserved.

Do not repeatedly rewrite documentation without a material
change in project state.

## Context and output efficiency

- Prefer focused searches to reading entire large files.
- Read test summaries before raw logs.
- Avoid redundant summaries and speculative investigations.
- Do not rebuild unchanged toolchains unnecessarily.
- Avoid lengthy progress narration.
- Report only material changes and blockers.

At the end of a task, report:
1. What changed.
2. Tests run and results.
3. Tests skipped or unavailable.
4. Commit hash and pushed branch.
5. Outstanding issues.

Never claim a push, test or camera validation succeeded
unless it actually did.
