#!/usr/bin/env python3
"""SessionStart orientation — puts the way of working IN THE ROOM.

The finding this exists for: plumb made the wow *authoritative* (the document
wins where a skill disagrees) but not *present* — a working session could run
for days without the document ever entering context, and compaction moves every
session further from the conversation where the process was alive. MAMA's
methodology was ambient because it lived in harness-surfaced skills; the wow's
ambient surface is this block plus the project's own instrument skills.

Deliberately tiny — a few lines, plain stdout (the injection path proven on
every SessionStart source). Fires on startup|resume only; compaction.py owns
the crowded post-compact injection point. Silent when the project has no
manifest: a project that has not adopted plumb's process gets no nagging.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))

try:
    import plumb
except ImportError:
    sys.exit(0)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if payload.get("source") == "compact":
        return  # compaction.py owns that injection point

    root = payload.get("cwd")
    try:
        mf = plumb.Manifest.load(root, required=False)
    except SystemExit:
        return
    if mf is None:
        return  # not a plumb-established project; say nothing

    bits = [f"process v{mf.process_version}"]
    doc = mf.data.get("document")
    if doc:
        bits.append(f"way of working: {doc} (the source of truth — it wins "
                    f"where any skill disagrees; process_read serves it)")
    adapter = mf.ledger.get("adapter")
    if adapter:
        led = f"ledger: {adapter}"
        scope = mf.ledger.get("scope")
        if scope:
            led += f" — scope: {scope}"
        bits.append(led)

    skills_dir = mf.root / ".claude" / "skills"
    names = sorted(p.parent.name for p in skills_dir.glob("*/SKILL.md")) \
        if skills_dir.is_dir() else []
    if names:
        bits.append("this project's own skills: " + ", ".join(names))

    print("=== PLUMB ===")
    print("  " + "\n  ".join(bits))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
