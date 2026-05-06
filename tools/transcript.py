#!/usr/bin/env python3
"""Walk a Claude Code session JSONL and emit a single through-line transcript.

Algorithm:
  1. Index every entry by uuid.
  2. Pick the leaf: latest-timestamp entry of eligible type (user/assistant, non-sidechain).
  3. Walk back via parentUuid; fall through to logicalParentUuid at compact boundaries.
  4. Stop on first dead bridge (parent and logical both unresolvable).
  5. Reverse → chronological. Render eligible entries.

Verification:
  Check whether the first eligible entry in the file (by timestamp) appears in the chain.
  If not, print a diagnostic naming where the walk stopped.
"""

import argparse
import json
import sys
from pathlib import Path


def is_eligible(entry):
    return entry.get("type") in ("user", "assistant") and not entry.get("isSidechain", False)


def load_entries(path):
    entries = {}
    by_line = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            d["_line"] = i
            by_line.append(d)
            u = d.get("uuid")
            if u:
                entries[u] = d
    return entries, by_line


def pick_leaf(by_line):
    eligible = [d for d in by_line if is_eligible(d) and d.get("timestamp")]
    if not eligible:
        return None
    return max(eligible, key=lambda d: d["timestamp"])


def walk_back(leaf, entries):
    chain, seen = [], set()
    cur = leaf
    bridged = 0
    dead_bridge = None
    while cur is not None and cur.get("uuid") not in seen:
        seen.add(cur.get("uuid"))
        chain.append(cur)
        parent_id = cur.get("parentUuid")
        nxt = entries.get(parent_id) if parent_id else None
        if nxt is None:
            logical_id = cur.get("logicalParentUuid")
            nxt = entries.get(logical_id) if logical_id else None
            if nxt is not None:
                bridged += 1
            elif parent_id or logical_id:
                dead_bridge = {
                    "at_uuid": cur.get("uuid"),
                    "at_line": cur.get("_line"),
                    "type": cur.get("type"),
                    "subtype": cur.get("subtype"),
                    "ts": cur.get("timestamp"),
                    "wanted_parent": parent_id,
                    "wanted_logical": logical_id,
                }
                break
        cur = nxt
    chain.reverse()
    return chain, bridged, dead_bridge


def render_content(content):
    """Flatten a message's content (string or block list) to plain text."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)
    parts = []
    for block in content:
        if not isinstance(block, dict):
            parts.append(str(block))
            continue
        btype = block.get("type")
        if btype == "text":
            parts.append(block.get("text", ""))
        elif btype == "tool_use":
            name = block.get("name", "?")
            parts.append(f"[tool_use: {name}]")
        elif btype == "tool_result":
            inner = block.get("content", "")
            text = inner if isinstance(inner, str) else render_content(inner)
            parts.append(f"[tool_result]\n{text}")
        elif btype == "thinking":
            parts.append(f"[thinking]\n{block.get('thinking', '')}")
        else:
            parts.append(f"[{btype}]")
    return "\n\n".join(p for p in parts if p)


def render_transcript(chain):
    lines = []
    for d in chain:
        if not is_eligible(d):
            continue
        msg = d.get("message")
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", d.get("type", "?"))
        ts = d.get("timestamp", "")
        content = render_content(msg.get("content", ""))
        if not content.strip():
            continue
        lines.append(f"## {role}  ·  {ts}")
        lines.append("")
        lines.append(content)
        lines.append("")
    return "\n".join(lines)


def verify(by_line, chain, dead_bridge):
    eligible = [d for d in by_line if is_eligible(d) and d.get("timestamp")]
    if not eligible:
        return []
    eligible.sort(key=lambda d: d["timestamp"])
    first, last = eligible[0], eligible[-1]
    chain_uuids = {e.get("uuid") for e in chain}
    findings = []
    if first.get("uuid") not in chain_uuids:
        findings.append(("first", first))
    if last.get("uuid") not in chain_uuids:
        findings.append(("last", last))
    return findings


def excerpt(entry, n=120):
    msg = entry.get("message")
    if isinstance(msg, dict):
        c = render_content(msg.get("content", ""))
        c = c.replace("\n", " ").strip()
        return (c[:n] + "…") if len(c) > n else c
    return ""


def print_verification(findings, chain, by_line, bridged, dead_bridge, out=sys.stderr):
    print(f"[transcript] entries in file: {len(by_line)}", file=out)
    eligible = [d for d in by_line if is_eligible(d) and d.get("timestamp")]
    print(f"[transcript] eligible entries (user/assistant, non-sidechain): {len(eligible)}", file=out)
    print(f"[transcript] chain length: {len(chain)}", file=out)
    print(f"[transcript] logical bridges followed: {bridged}", file=out)
    if chain:
        first_in_chain = next((e for e in chain if is_eligible(e)), None)
        last_in_chain = next((e for e in reversed(chain) if is_eligible(e)), None)
        if first_in_chain:
            print(f"[transcript] chain first eligible: L{first_in_chain.get('_line')} {first_in_chain.get('timestamp')}", file=out)
        if last_in_chain:
            print(f"[transcript] chain last eligible:  L{last_in_chain.get('_line')} {last_in_chain.get('timestamp')}", file=out)

    if not findings:
        print("[transcript] verification: PASS (first and last eligible messages both in chain)", file=out)
        return

    print("[transcript] verification: NEGATIVE FINDINGS", file=out)
    for which, entry in findings:
        print(f"[transcript]   {which} eligible entry NOT in chain:", file=out)
        print(f"[transcript]     L{entry.get('_line')}  uuid={entry.get('uuid','')[:8]}  ts={entry.get('timestamp')}  type={entry.get('type')}", file=out)
        print(f"[transcript]     content: {excerpt(entry)}", file=out)
    if dead_bridge:
        print(f"[transcript]   walk terminated at L{dead_bridge['at_line']} ({dead_bridge['type']}/{dead_bridge['subtype']}) ts={dead_bridge['ts']}", file=out)
        print(f"[transcript]     wanted parentUuid={(dead_bridge['wanted_parent'] or '')[:8] or '<none>'} (resolved: no)", file=out)
        if dead_bridge["wanted_logical"]:
            print(f"[transcript]     wanted logicalParentUuid={dead_bridge['wanted_logical'][:8]} (resolved: no)", file=out)
    print("[transcript] please share this diagnostic so we can refine the algorithm.", file=out)


def main(argv=None):
    p = argparse.ArgumentParser(description="Generate a single through-line transcript from a CC session JSONL")
    p.add_argument("jsonl", type=Path, help="Path to the session .jsonl file")
    p.add_argument("-o", "--output", type=Path, help="Output transcript path (default: stdout)")
    args = p.parse_args(argv)

    if not args.jsonl.exists():
        print(f"error: {args.jsonl} not found", file=sys.stderr)
        return 2

    entries, by_line = load_entries(args.jsonl)
    leaf = pick_leaf(by_line)
    if leaf is None:
        print("error: no eligible (user/assistant) entries found", file=sys.stderr)
        return 1

    chain, bridged, dead_bridge = walk_back(leaf, entries)
    transcript = render_transcript(chain)

    if args.output:
        args.output.write_text(transcript, encoding="utf-8")
        print(f"[transcript] wrote {args.output} ({len(transcript)} bytes)", file=sys.stderr)
    else:
        sys.stdout.write(transcript)

    findings = verify(by_line, chain, dead_bridge)
    print_verification(findings, chain, by_line, bridged, dead_bridge)
    return 0


if __name__ == "__main__":
    sys.exit(main())
