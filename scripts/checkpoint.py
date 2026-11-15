#!/usr/bin/env python3
"""Safe Git checkpoint helper. Never force-pushes."""

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--message",
        help="Commit message for explicitly staged changes",
    )
    args = parser.parse_args()

    branch = git("branch", "--show-current")
    if not branch:
        raise SystemExit("Detached HEAD; refusing checkpoint.")

    print(f"Branch: {branch}")
    print(git("status", "--short") or "Working tree clean")

    if args.message:
        staged = git("diff", "--cached", "--name-only")
        if not staged:
            raise SystemExit(
                "No staged changes. Stage intended files first."
            )

        print("\nStaged files:\n" + staged)
        if input("Commit staged changes? [y/N] ").lower() != "y":
            raise SystemExit("Cancelled.")

        git("commit", "-m", args.message)

    if git("status", "--porcelain"):
        print(
            "\nWARNING: Uncommitted changes remain. "
            "They will not be included in the push."
        )

    print(f"\nRemote tracking: {branch}")
    if input("Push committed work? [y/N] ").lower() != "y":
        raise SystemExit("Push cancelled.")

    subprocess.run(
        ["git", "push", "-u", "origin", branch],
        cwd=ROOT,
        check=True,
    )

    print("Push complete.")
    print("HEAD:", git("rev-parse", "--short", "HEAD"))


if __name__ == "__main__":
    main()
