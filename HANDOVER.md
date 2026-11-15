# OM-5 firmware development: current handover

## Known-good baseline

The owner reported that v0.1.0-alpha8 boots on an
OM-5 Mark II (E148, stock firmware 1.1).

The report covers selected colour-profile, HSL,
tone-control and Live ND functionality. It is not
a general safety or compatibility certification.

Authoritative evidence:
- research/OM5II-ALPHA8-CAMERA-2026-11-15.md
- releases/v0.1.0-alpha8/patch.json
- tests/alpha8-results.json

## Development status

The previous handover has been preserved verbatim at:

docs/archive/HANDOVER.md

It contains the latest recorded UI candidate, build hashes,
memory addresses, graphics investigation, emulator results,
remaining defects and detailed next actions.

**Important:** This workflow migration has not independently
revalidated those technical findings or determined whether
subsequent commits superseded them.

Before continuing firmware development, review the archived
handover alongside recent Git history and reconcile this
section with the actual current source state.

Do not assume that the latest emulator-tested candidate
has been physically camera-tested.

## Current priorities

- Establish the current firmware candidate and test status.
- Resolve outstanding colour-wheel and tone-curve graphics
  issues on physical hardware.
- Confirm the relevant Live ND and colour-profile UI fixes.
- Maintain a safe distinction between OM-5 II and OM-5 I.
- Incorporate upstream features only after the port is stable.

These priorities are inherited from the archived handover
and should be updated if newer verified work supersedes them.

## Next action

Reconcile this handover against the latest commits and
the preserved technical record before starting new firmware
work. Move durable findings into topic-specific documentation
without deleting the original evidence.

## Workflow

Shared instructions: AGENTS.md

Documentation index: docs/INDEX.md

Tests:

    python scripts/check.py fast
    python scripts/check.py integration
    python scripts/check.py full

Git checkpoint:

    python scripts/checkpoint.py

## Evidence rules

Emulator-tested does not mean camera-tested.

The owner performs physical-camera updates.

Do not change release safety status without an explicit
physical-camera report linked to the exact package hash.
