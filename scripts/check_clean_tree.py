#!/usr/bin/env python3
"""Refuse a reproducible evaluation when source files are outside Git history."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )


inside = git("rev-parse", "--is-inside-work-tree")
if inside.returncode != 0 or inside.stdout.strip() != "true":
    sys.exit("Reproducibility check failed: project is not a Git work tree.")

head = git("rev-parse", "HEAD")
if head.returncode != 0:
    sys.exit("Reproducibility check failed: project has no source commit.")

status = git("status", "--porcelain", "--untracked-files=all")
if status.returncode != 0:
    sys.exit(f"Reproducibility check failed: {status.stderr.strip()}")

if status.stdout.strip():
    print("Reproducibility check failed: source tree is dirty:", file=sys.stderr)
    print(status.stdout.rstrip(), file=sys.stderr)
    print("Commit, discard, or ignore these files before running the gate.", file=sys.stderr)
    raise SystemExit(1)

print(f"Clean source commit: {head.stdout.strip()}")
