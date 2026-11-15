#!/usr/bin/env python3
"""Tiered checks for caduceus-om5."""

import argparse
import datetime
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "generated" / "check-logs"


def execute(name, command, env=None):
    LOGS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log = LOGS / f"{stamp}-{name}.log"

    print(f"[RUN] {name}", flush=True)

    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            check=False,
        )

    status = "PASS" if result.returncode == 0 else "FAIL"
    print(f"[{status}] {name} | {log}", flush=True)

    if result.returncode:
        print("Last 25 log lines:", flush=True)
        lines = log.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines()
        print("\n".join(lines[-25:]), flush=True)
        raise SystemExit(result.returncode)


def require_path(value, label):
    if not value:
        raise SystemExit(
            f"UNAVAILABLE: {label} is required. "
            "No integration checks were performed."
        )
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise SystemExit(
            f"UNAVAILABLE: {label} does not exist: {path}"
        )
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "level",
        choices=["fast", "integration", "full"],
    )
    parser.add_argument(
        "--case",
        help="Optional emulator case for focused integration checks",
    )
    args = parser.parse_args()

    execute(
        "python-tests",
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
        ],
    )

    if args.level == "fast":
        print(
            "Fast checks complete. Firmware/emulator "
            "integration was not run."
        )
        return

    stock = require_path(
        os.environ.get("OM5_STOCK"),
        "OM5_STOCK",
    )
    emu = require_path(
        os.environ.get("OM_EMU_DIR"),
        "OM_EMU_DIR",
    )

    build = ROOT / "generated" / "workflow-strict"
    results = ROOT / "generated" / "workflow-regressions"

    execute(
        "strict-build",
        [
            sys.executable,
            "tools/oly_patch.py",
            "firmware/om5ii",
            "--stock",
            str(stock),
            "--out",
            str(build),
            "--decoded",
        ],
    )

    emulator_command = [
        sys.executable,
        "tests/run_emulator.py",
        "--emu",
        str(emu),
        "--build",
        str(build),
        "--stock",
        str(stock),
        "--out",
        str(results),
    ]

    if args.case:
        emulator_command.extend(["--case", args.case])

    execute("emulator", emulator_command)

    if args.level == "full":
        execute(
            "build-audit",
            [
                sys.executable,
                "tests/audit_build.py",
                "--build",
                str(build),
                "--stock",
                str(stock),
                "--out",
                str(
                    ROOT
                    / "generated"
                    / "workflow-build-audit.json"
                ),
            ],
        )

        print(
            "Full wrapper checks complete. Review "
            "tests/README.md for additional release-specific "
            "and startup fault-injection checks."
        )
    else:
        print("Integration checks complete.")


if __name__ == "__main__":
    main()
