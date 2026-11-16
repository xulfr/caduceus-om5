# Tiered development checks

Run from the repository root:

    python scripts/check.py fast
    python scripts/check.py integration
    python scripts/check.py full

## Fast

Runs the existing Python unittest suite.

This is the default for ordinary source and tooling changes.

Some existing tests may report skips when external firmware
is unavailable. Review the summary rather than treating
skipped tests as successful validation.

## Integration

Requires the official stock firmware file, a configured
assembler and an existing OM-Emu checkout.

Set:

    OM5_STOCK=/path/to/official/firmware.BIN
    OM_EMU_DIR=/path/to/om-emu

On Windows, use the equivalent environment variables.

Integration performs a strict build and runs the existing
emulator regression entry point.

The script refuses to claim integration success when the
required environment is missing.

## Full

Runs integration checks and the existing static build audit.

It is not a replacement for physical-camera testing.

Additional release-specific tests described in tests/README.md
may still be required. This runner is an initial consolidation,
not a claim of complete release validation.

## Logs

Detailed output is saved under generated/check-logs/.

The console shows concise results.

The runner does not automatically cache firmware builds.
Caching can be introduced after establishing reliable input
fingerprints and dependency tracking.
