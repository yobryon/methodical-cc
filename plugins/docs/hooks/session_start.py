#!/usr/bin/env python3
"""docs plugin SessionStart hook.

Surfaces a one-line count of unaddressed feedback files in the configured
feedback path. Reads .mcc/docs-publish.yml for path overrides; defaults to
docs/feedback/. Files in docs/feedback/processed/ are excluded — the
move-on-complete pattern means processed feedback is out of sight.

Stdlib only. Silent when no manifest, no feedback dir, or zero unaddressed.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DEFAULT_FEEDBACK_PATH = "docs/feedback"
MANIFEST_PATH = ".mcc/docs-publish.yml"


def parse_feedback_path(manifest_text: str) -> str:
    """Tiny YAML scalar reader for `feedback_path:`. Avoids the PyYAML dep.

    Looks for a top-level `feedback_path: <value>` line. Strips quotes and
    trailing comments. Returns DEFAULT_FEEDBACK_PATH if not found.
    """
    for raw in manifest_text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line or line.startswith(" ") or line.startswith("\t"):
            continue
        if line.startswith("feedback_path:"):
            value = line[len("feedback_path:"):].strip()
            if value.startswith(("'", '"')) and value.endswith(value[0]):
                value = value[1:-1]
            if value:
                return value
    return DEFAULT_FEEDBACK_PATH


def count_unaddressed(feedback_dir: Path) -> int:
    if not feedback_dir.is_dir():
        return 0
    n = 0
    for entry in feedback_dir.iterdir():
        if entry.is_file() and entry.suffix == ".md":
            n += 1
    return n


def main() -> int:
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    cwd = Path(os.getcwd())
    manifest = cwd / MANIFEST_PATH
    feedback_path = DEFAULT_FEEDBACK_PATH
    if manifest.is_file():
        try:
            feedback_path = parse_feedback_path(manifest.read_text(encoding="utf-8"))
        except Exception:
            feedback_path = DEFAULT_FEEDBACK_PATH

    feedback_dir = cwd / feedback_path
    n = count_unaddressed(feedback_dir)
    if n <= 0:
        return 0

    label = "file" if n == 1 else "files"
    print(f"=== DOCS ===")
    print(f"{n} unaddressed feedback {label} in {feedback_path}/")
    print(f"Run /docs:address to triage.")
    print("---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
