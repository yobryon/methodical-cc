"""docs subcommand module for mcc.

Implements `mcc docs setup|publish|pull|status` — markdown-to-docx publishing
and Word-comments-to-feedback ingest. Stdlib-only, hand-rolled YAML reader for
the narrow manifest schema we ship.

Manifest format (`.mcc/docs-publish.yml`):

    output: docx                          # default output format
    template: .mcc/templates/default.docx # optional pandoc --reference-doc
    structure: mirror                     # mirror | flat
    publish_path: .mcc/publish            # output dir
    feedback_path: docs/feedback          # ingest dir
    pandoc_args: []                       # extra args (escape hatch)
    from_extensions: []                   # markdown read-side ext (e.g. lists_without_preceding_blankline)
    to_extensions: []                     # output-format write-side ext
    docs:
      - docs/pdt                          # directory → <dir>/**/*.md
      - docs/**/design*.md                # explicit glob
      - docs/product/spec.md              # literal
      - pattern: docs/architecture
        structure: flat
      - pattern: docs/product/roadmap.md
        publish_as: roadmap-2026.docx
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

# Public defaults (also referenced by hooks)
DEFAULT_PUBLISH_PATH = ".mcc/publish"
DEFAULT_FEEDBACK_PATH = "docs/feedback"
DEFAULT_OUTPUT = "docx"
DEFAULT_STRUCTURE = "mirror"
MANIFEST_PATH = ".mcc/docs-publish.yml"
PUBLISH_STATE_PATH = ".mcc/docs-publish-state.json"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace("w", W_NS)

# ----------------------------- helpers (re-implemented locally to keep
# this module independent of the parent's util surface) ---------------

def _die(msg, code=1):
    print(f"mcc: docs: {msg}", file=sys.stderr)
    sys.exit(code)


def _info(msg):
    print(msg)


def _warn(msg):
    print(f"  ⚠ {msg}", file=sys.stderr)


def _ok(msg):
    print(f"  ✓ {msg}")


def _prompt(msg, default=None):
    suffix = f" [{default}]" if default else ""
    raw = input(f"{msg}{suffix}: ").strip()
    return raw or (default or "")


def _confirm(msg, default=True):
    suffix = "[Y/n]" if default else "[y/N]"
    raw = input(f"{msg} {suffix} ").strip().lower()
    if not raw:
        return default
    return raw.startswith("y")


# ----------------------------- manifest reader -----------------------

def _strip_comment(line: str) -> str:
    """Strip YAML # comments, but only when the # is not inside quotes.

    Our manifest schema doesn't use # in any string value, but be defensive.
    """
    in_single = in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return line[:i]
    return line


def _strip_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        return v[1:-1]
    return v


def _parse_scalar(value: str):
    v = _strip_quotes(value.strip())
    if v in ("true", "True", "yes"):
        return True
    if v in ("false", "False", "no"):
        return False
    if v in ("null", "~", ""):
        return None
    return v


def _parse_inline_list(rest: str, key: str) -> list:
    """Parse `[a, b, c]` form into a list of strings. Empty → []."""
    if not (rest.startswith("[") and rest.endswith("]")):
        _die(f"{key} must be a list (e.g. [] or [\"a\", \"b\"])")
    inner = rest[1:-1].strip()
    if not inner:
        return []
    return [_strip_quotes(p.strip()) for p in inner.split(",") if p.strip()]


def _parse_mapping_value(value: str):
    """Used inside a doc-mapping. Inline-list form supported; otherwise scalar."""
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        return _parse_inline_list(v, "value")
    return _parse_scalar(v)


def load_manifest(repo_root: Path) -> dict:
    """Read `.mcc/docs-publish.yml` and return a normalized dict.

    Supports the narrow schema documented at module top. Anything more exotic
    will produce a clear parse error rather than ambiguous behavior.
    """
    path = repo_root / MANIFEST_PATH
    if not path.is_file():
        _die(f"no manifest at {MANIFEST_PATH}. Run `mcc docs setup` first.")

    text = path.read_text(encoding="utf-8")
    out = {
        "output": DEFAULT_OUTPUT,
        "template": None,
        "structure": DEFAULT_STRUCTURE,
        "publish_path": DEFAULT_PUBLISH_PATH,
        "feedback_path": DEFAULT_FEEDBACK_PATH,
        "pandoc_args": [],
        "from_extensions": [],
        "to_extensions": [],
        "docs": [],
    }

    state = "top"  # "top" | "docs_list" | "doc_mapping"
    current_mapping = None
    pandoc_args_inline = False

    for raw_line in text.splitlines():
        line = _strip_comment(raw_line).rstrip()
        if not line.strip():
            if state == "doc_mapping" and current_mapping is not None:
                out["docs"].append(current_mapping)
                current_mapping = None
                state = "docs_list"
            continue

        # Determine indent level
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)

        if indent == 0 and ":" in stripped:
            # Top-level key
            if state == "doc_mapping" and current_mapping is not None:
                out["docs"].append(current_mapping)
                current_mapping = None

            key, _, rest = stripped.partition(":")
            key = key.strip()
            rest = rest.strip()

            if key == "docs":
                if rest and rest != "[]":
                    _die(f"`docs:` must start a list (newline + `- ...` items) or be `[]`")
                state = "docs_list"
                continue

            if key in ("pandoc_args", "from_extensions", "to_extensions"):
                if rest:
                    out[key] = _parse_inline_list(rest, key)
                else:
                    out[key] = []
                state = "top"
                continue

            if key in ("output", "template", "structure", "publish_path", "feedback_path"):
                out[key] = _parse_scalar(rest)
                state = "top"
                continue

            _die(f"unknown top-level key `{key}` in manifest")

        if state == "docs_list":
            if stripped.startswith("- "):
                item = stripped[2:].strip()
                # Either a bare scalar or a mapping starting on this line
                if ":" in item and not item.startswith(("'", '"')):
                    # Mapping starts here
                    if current_mapping is not None:
                        out["docs"].append(current_mapping)
                    current_mapping = {}
                    k, _, v = item.partition(":")
                    current_mapping[k.strip()] = _parse_mapping_value(v)
                    state = "doc_mapping"
                else:
                    if current_mapping is not None:
                        out["docs"].append(current_mapping)
                        current_mapping = None
                    out["docs"].append(_strip_quotes(item))
                continue

            if state == "doc_mapping" and current_mapping is not None and indent >= 2:
                k, _, v = stripped.partition(":")
                if not _:
                    _die(f"can't parse mapping line: {raw_line!r}")
                current_mapping[k.strip()] = _parse_mapping_value(v)
                continue

        if state == "doc_mapping":
            if stripped.startswith("- "):
                # Next item starts; flush
                if current_mapping is not None:
                    out["docs"].append(current_mapping)
                    current_mapping = None
                state = "docs_list"
                # Re-process this line as docs_list
                item = stripped[2:].strip()
                if ":" in item and not item.startswith(("'", '"')):
                    current_mapping = {}
                    k, _, v = item.partition(":")
                    current_mapping[k.strip()] = _parse_mapping_value(v)
                    state = "doc_mapping"
                else:
                    out["docs"].append(_strip_quotes(item))
                continue
            if indent >= 2:
                k, _, v = stripped.partition(":")
                if not _:
                    _die(f"can't parse mapping line: {raw_line!r}")
                current_mapping[k.strip()] = _parse_mapping_value(v)
                continue

    if state == "doc_mapping" and current_mapping is not None:
        out["docs"].append(current_mapping)

    return out


# ----------------------------- pattern resolution ---------------------

def _glob_patterns_for(item, repo_root: Path):
    """Return list of (source_path, override_dict) tuples for one manifest item.

    `item` is either a bare string or a mapping. Bare strings:
      - directory → "<dir>/**/*.md"
      - glob (contains *, ?, [) → as-is
      - literal path → as-is
    """
    if isinstance(item, str):
        spec = item
        overrides = {}
    elif isinstance(item, dict):
        spec = item.get("pattern")
        if not spec:
            _die(f"manifest entry missing `pattern:` key: {item!r}")
        overrides = {k: v for k, v in item.items() if k != "pattern"}
    else:
        _die(f"unsupported manifest entry type: {type(item).__name__}")

    abs_spec_path = repo_root / spec
    is_glob = any(c in spec for c in ("*", "?", "["))
    if not is_glob and abs_spec_path.is_dir():
        pattern = f"{spec}/**/*.md"
    elif not is_glob:
        pattern = spec
    else:
        pattern = spec

    matched = sorted(repo_root.glob(pattern))
    return matched, overrides


def resolve_publish_targets(manifest: dict, repo_root: Path, cli_patterns=None):
    """Return list of dicts: {source, output_path, output_format, template, pandoc_args}.

    `cli_patterns` (if given) narrows the manifest's pattern set: a manifest
    item is included only if its source path is matched by *any* CLI pattern.
    CLI patterns are interpreted as repo-root-relative globs (or directories).
    """
    publish_root = repo_root / manifest["publish_path"]
    structure_default = manifest["structure"]
    output_default = manifest["output"]
    template_default = manifest.get("template")
    pandoc_args_default = list(manifest.get("pandoc_args") or [])
    from_ext_default = list(manifest.get("from_extensions") or [])
    to_ext_default = list(manifest.get("to_extensions") or [])

    targets = []
    seen_outputs = {}  # output_path -> source_path (collision detection)
    cli_resolved = _resolve_cli_narrowing(cli_patterns, repo_root) if cli_patterns else None

    for item in manifest.get("docs", []):
        matched, overrides = _glob_patterns_for(item, repo_root)
        if not matched:
            spec = item if isinstance(item, str) else item.get("pattern")
            _warn(f"pattern `{spec}` matched no files")
            continue

        for source in matched:
            if source.suffix.lower() != ".md":
                spec = item if isinstance(item, str) else item.get("pattern")
                _die(f"non-markdown match: pattern `{spec}` matched `{source.relative_to(repo_root)}`. Adjust the pattern.")

            if cli_resolved is not None and source.resolve() not in cli_resolved:
                continue

            output_format = overrides.get("output") or output_default
            structure = overrides.get("structure") or structure_default
            template = overrides.get("template") or template_default
            publish_as = overrides.get("publish_as")

            rel = source.relative_to(repo_root)
            if publish_as:
                output_rel = Path(publish_as)
            elif structure == "flat":
                output_rel = Path(rel.stem + f".{output_format}")
            else:  # mirror
                output_rel = rel.with_suffix(f".{output_format}")

            output_path = publish_root / output_rel

            existing = seen_outputs.get(str(output_path))
            if existing is not None and existing != source:
                _die(f"output collision: both `{existing.relative_to(repo_root)}` and `{rel}` resolve to `{output_rel}`")
            seen_outputs[str(output_path)] = source

            from_ext = overrides.get("from_extensions")
            to_ext = overrides.get("to_extensions")
            targets.append({
                "source": source,
                "output_path": output_path,
                "output_format": output_format,
                "template": (repo_root / template).resolve() if template else None,
                "pandoc_args": pandoc_args_default,
                "from_extensions": list(from_ext) if from_ext is not None else from_ext_default,
                "to_extensions": list(to_ext) if to_ext is not None else to_ext_default,
            })

    return targets


def _resolve_cli_narrowing(cli_patterns, repo_root: Path):
    """Turn CLI patterns into a set of resolved source paths (filter set)."""
    resolved = set()
    for spec in cli_patterns:
        spec_path = repo_root / spec
        is_glob = any(c in spec for c in ("*", "?", "["))
        if not is_glob and spec_path.is_dir():
            for p in spec_path.rglob("*.md"):
                resolved.add(p.resolve())
        elif not is_glob:
            if spec_path.is_file():
                resolved.add(spec_path.resolve())
        else:
            for p in repo_root.glob(spec):
                resolved.add(p.resolve())
    if not resolved:
        _die(f"CLI pattern(s) matched no files: {cli_patterns}")
    return resolved


# ----------------------------- pandoc invocation ---------------------

def _have_pandoc():
    return shutil.which("pandoc") is not None


def _publish_one(target: dict) -> tuple[bool, str]:
    src = target["source"]
    out = target["output_path"]
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = ["pandoc", str(src), "-o", str(out)]
    from_ext = target.get("from_extensions") or []
    to_ext = target.get("to_extensions") or []
    # v1 input is always markdown; output_format is per-target.
    def _join_ext(base, exts):
        # Pandoc syntax: `markdown+ext1-ext2`. Accept entries with explicit
        # `+`/`-` prefix; default to `+` for bare names.
        return base + "".join(e if e[:1] in ("+", "-") else f"+{e}" for e in exts)
    if from_ext:
        cmd.extend(["--from", _join_ext("markdown", from_ext)])
    if to_ext:
        cmd.extend(["--to", _join_ext(target["output_format"], to_ext)])
    if target.get("template"):
        cmd.extend(["--reference-doc", str(target["template"])])

    # Resolve relative paths in the source (images, includes) against the
    # source's containing directory, not the invoking CWD. Pandoc defaults
    # to CWD, which breaks when mcc is run from repo root but the markdown
    # lives in a subdirectory and references images via relative paths.
    # Include CWD as a fallback for paths authored relative to the repo.
    src_parent = src.parent.resolve()
    cwd = Path.cwd().resolve()
    resource_dirs = [str(src_parent)]
    if cwd != src_parent:
        resource_dirs.append(str(cwd))
    cmd.extend(["--resource-path", os.pathsep.join(resource_dirs)])

    if target.get("pandoc_args"):
        cmd.extend(target["pandoc_args"])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return False, proc.stderr.strip() or "pandoc returned non-zero"
    return True, ""


# ----------------------------- docx comment parser -------------------

def _w(tag):
    return f"{{{W_NS}}}{tag}"


def _extract_text(elem) -> str:
    """Concatenate all <w:t> descendants of an element."""
    parts = []
    for t in elem.iter(_w("t")):
        if t.text:
            parts.append(t.text)
    return "".join(parts)


def parse_docx_comments(docx_path: Path) -> dict:
    """Return {comments: [...], doc_meta: {...}}.

    Each comment dict: {id, author, date, body, anchored_text, section}.
    `section` is the heading text of the nearest preceding heading paragraph.
    """
    if not docx_path.is_file():
        return {"comments": [], "doc_meta": {}}

    with zipfile.ZipFile(docx_path) as z:
        names = z.namelist()
        if "word/comments.xml" not in names:
            return {"comments": [], "doc_meta": {}}

        comments_xml = z.read("word/comments.xml").decode("utf-8")
        document_xml = z.read("word/document.xml").decode("utf-8")

    comments_root = ET.fromstring(comments_xml)
    body_root = ET.fromstring(document_xml)

    # Build: id → {author, date, body}
    comment_meta = {}
    for c in comments_root.iter(_w("comment")):
        cid = c.get(_w("id"))
        if cid is None:
            continue
        comment_meta[cid] = {
            "id": cid,
            "author": c.get(_w("author")) or "(unknown)",
            "date": c.get(_w("date")) or "",
            "body": _extract_text(c).strip(),
        }

    # Walk body to find anchors. Need an iter-with-context approach because
    # commentRangeStart/End are siblings of the runs they bracket. Build a
    # flat iteration over the body, tracking heading state and active ranges.
    flat = []
    body_elem = body_root.find(_w("body"))
    if body_elem is None:
        return {"comments": list(comment_meta.values()), "doc_meta": {}}

    def _walk(elem, path):
        for child in elem:
            yield child, path + [elem]
            yield from _walk(child, path + [elem])

    current_heading = None
    open_ranges = {}  # id → {section, accumulated_text}

    # We iterate paragraphs in order; within each paragraph we look for
    # range markers and runs.
    for p in body_elem.iter(_w("p")):
        # Check if this paragraph is a heading
        pStyle = None
        ppr = p.find(_w("pPr"))
        if ppr is not None:
            ps = ppr.find(_w("pStyle"))
            if ps is not None:
                pStyle = ps.get(_w("val")) or ""
        is_heading = bool(pStyle and pStyle.startswith("Heading"))
        if is_heading:
            current_heading = _extract_text(p).strip()

        # Walk children of the paragraph in document order
        for node in p.iter():
            tag = node.tag
            if tag == _w("commentRangeStart"):
                cid = node.get(_w("id"))
                if cid is not None:
                    open_ranges[cid] = {
                        "section": current_heading or "(top of document)",
                        "text": [],
                    }
            elif tag == _w("commentRangeEnd"):
                cid = node.get(_w("id"))
                if cid in open_ranges:
                    meta = comment_meta.get(cid)
                    if meta is not None:
                        meta["section"] = open_ranges[cid]["section"]
                        meta["anchored_text"] = "".join(open_ranges[cid]["text"]).strip()
                    open_ranges.pop(cid, None)
            elif tag == _w("t") and node.text:
                # Add text to all currently-open ranges
                for state in open_ranges.values():
                    state["text"].append(node.text)

    # Any comments that never matched an anchor: leave anchored_text empty
    for meta in comment_meta.values():
        meta.setdefault("section", "(unanchored)")
        meta.setdefault("anchored_text", "")

    # Sort by date when possible, else by id
    def _sort_key(m):
        return (m.get("date", ""), int(m.get("id", "0") or 0))
    comments_sorted = sorted(comment_meta.values(), key=_sort_key)

    return {"comments": comments_sorted, "doc_meta": {}}


# ----------------------------- feedback rendering --------------------

def _doc_slug(source: Path, repo_root: Path) -> str:
    rel = source.relative_to(repo_root) if source.is_absolute() else Path(source)
    parts = list(rel.with_suffix("").parts)
    if parts and parts[0] == "docs":
        parts = parts[1:]
    if not parts:
        parts = [rel.stem]
    return "-".join(re.sub(r"[^A-Za-z0-9]+", "-", p).strip("-") for p in parts).lower() or "doc"


def _now_local_iso():
    return _dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def _now_compact():
    return _dt.datetime.now().strftime("%Y%m%dT%H%M%S")


def render_feedback_file(
    source_md: Path, docx_path: Path, parsed: dict, repo_root: Path
) -> str:
    comments = parsed["comments"]
    rel_source = source_md.relative_to(repo_root) if source_md.is_absolute() else source_md
    rel_docx = docx_path.relative_to(repo_root) if docx_path.is_absolute() else docx_path
    reviewers = sorted({c["author"] for c in comments if c.get("author")})

    lines = []
    lines.append("---")
    lines.append(f"source: {rel_source}")
    lines.append(f"published_as: {rel_docx}")
    lines.append(f"pulled_at: {_now_local_iso()}")
    lines.append(f"reviewers: [{', '.join(reviewers)}]")
    lines.append(f"comment_count: {len(comments)}")
    lines.append("---")
    lines.append("")
    lines.append(f"# Feedback on {rel_source}")
    lines.append("")
    if not comments:
        lines.append("_No comments found._")
        lines.append("")
        return "\n".join(lines)

    for i, c in enumerate(comments, 1):
        when = c.get("date") or "(no date)"
        author = c.get("author") or "(unknown)"
        section = c.get("section") or "(unanchored)"
        excerpt = c.get("anchored_text") or "(no text anchored)"
        body = c.get("body") or "(empty comment)"

        lines.append(f"## Comment {i} — {author}, {when}")
        lines.append("")
        lines.append(f"**Anchored to:** Section \"{section}\"")
        if excerpt:
            short = excerpt if len(excerpt) <= 240 else excerpt[:237] + "..."
            lines.append(f"**Excerpt:** \"{short}\"")
        lines.append("")
        for line in body.splitlines():
            lines.append(line)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ----------------------------- pull-state tracking -------------------

def _load_publish_state(repo_root: Path) -> dict:
    p = repo_root / PUBLISH_STATE_PATH
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_publish_state(repo_root: Path, state: dict):
    p = repo_root / PUBLISH_STATE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _new_comment_ids(parsed: dict, prior_seen: list) -> list:
    seen = set(prior_seen or [])
    return [c["id"] for c in parsed["comments"] if c["id"] not in seen]


# ----------------------------- output→source mapping -----------------

def _source_for_output(output_path: Path, manifest: dict, repo_root: Path) -> Path | None:
    targets = resolve_publish_targets(manifest, repo_root)
    for t in targets:
        if t["output_path"].resolve() == output_path.resolve():
            return t["source"]
    return None


# ----------------------------- commands ------------------------------

def cmd_docs_setup(args):
    repo_root = Path.cwd()
    manifest_file = repo_root / MANIFEST_PATH
    manifest_file.parent.mkdir(parents=True, exist_ok=True)

    _info("docs setup — interactive")
    _info("")

    if manifest_file.exists():
        if not _confirm(f"  {MANIFEST_PATH} exists. Overwrite?", default=False):
            _info("Aborted. No changes made.")
            return

    if not _have_pandoc():
        _warn("pandoc not found on PATH.")
        _info("    Install: https://pandoc.org/installing.html")
        if not _confirm("  Continue setup anyway? (you can install pandoc later)", default=True):
            _info("Aborted.")
            return

    output = _prompt("Output format", default="docx")
    structure = _prompt("Structure (mirror | flat)", default="mirror")
    publish_path = _prompt("Publish path", default=DEFAULT_PUBLISH_PATH)
    feedback_path = _prompt("Feedback path", default=DEFAULT_FEEDBACK_PATH)
    template = _prompt("Reference template (path or empty for none)", default="")

    lines = [
        "# docs publish manifest. See `mcc docs -h` and docs-design.md for schema.",
        f"output: {output}",
    ]
    if template:
        lines.append(f"template: {template}")
    lines.append(f"structure: {structure}")
    lines.append(f"publish_path: {publish_path}")
    lines.append(f"feedback_path: {feedback_path}")
    lines.append("pandoc_args: []")
    lines.append("# Pandoc format extensions. Examples:")
    lines.append("#   from_extensions: [lists_without_preceding_blankline]")
    lines.append("#   to_extensions: []")
    lines.append("from_extensions: []")
    lines.append("to_extensions: []")
    lines.append("")
    lines.append("# What to publish. Each entry can be:")
    lines.append("#   - a directory (publishes all *.md beneath it)")
    lines.append("#   - a glob pattern (e.g. docs/**/design*.md)")
    lines.append("#   - a literal path")
    lines.append("#   - a mapping with `pattern:` plus optional overrides:")
    lines.append("#       output, structure, template, publish_as")
    lines.append("docs:")
    lines.append("  # - docs/product")
    lines.append("  # - docs/**/design*.md")
    lines.append("  # - pattern: docs/architecture/overview.md")
    lines.append("  #   publish_as: architecture-overview.docx")
    lines.append("")

    manifest_file.write_text("\n".join(lines), encoding="utf-8")
    _ok(f"wrote {MANIFEST_PATH}")

    _ensure_gitignore_entries(repo_root, [
        f"{publish_path.rstrip('/')}/",
        ".mcc/docs-publish-state.json",
    ])

    _info("")
    _info("Next steps:")
    _info(f"  1. Edit {MANIFEST_PATH} to declare which docs to publish.")
    _info(f"  2. Set up {publish_path}/ (typically a symlink to your synced folder).")
    _info(f"     Example (WSL → OneDrive):")
    _info(f"       ln -s /mnt/c/Users/<you>/OneDrive/.../ProjectDocs {publish_path}")
    _info(f"  3. Run `mcc docs publish` to generate, then notify your reviewers.")
    _info(f"  4. After comments come in, run `mcc docs pull` to ingest as feedback files.")


def _ensure_gitignore_entries(repo_root: Path, entries: list):
    gi = repo_root / ".gitignore"
    existing = gi.read_text(encoding="utf-8") if gi.is_file() else ""
    existing_set = set(line.strip() for line in existing.splitlines())
    to_add = [e for e in entries if e not in existing_set]
    if not to_add:
        return
    if existing and not existing.endswith("\n"):
        existing += "\n"
    if existing and not existing.endswith("\n\n"):
        existing += "\n"
    existing += "# docs plugin\n"
    for e in to_add:
        existing += f"{e}\n"
    gi.write_text(existing, encoding="utf-8")
    _ok(f"updated .gitignore with: {', '.join(to_add)}")


def cmd_docs_publish(args):
    if not _have_pandoc():
        _die("pandoc not found on PATH. Install pandoc and retry.")

    repo_root = Path.cwd()
    manifest = load_manifest(repo_root)

    cli_patterns = list(args.patterns) if args.patterns else None
    targets = resolve_publish_targets(manifest, repo_root, cli_patterns=cli_patterns)
    if not targets:
        _info("No targets resolved. Check your manifest's `docs:` list.")
        return

    _info(f"Publishing {len(targets)} document(s) → {manifest['publish_path']}/")
    ok_count = 0
    for t in targets:
        rel_src = t["source"].relative_to(repo_root)
        rel_out = t["output_path"].relative_to(repo_root)
        ok, err = _publish_one(t)
        if ok:
            _ok(f"{rel_src} → {rel_out}")
            ok_count += 1
        else:
            _warn(f"{rel_src} → {rel_out}\n      {err}")

    _info("")
    _info(f"Done: {ok_count}/{len(targets)} published.")


def cmd_docs_pull(args):
    repo_root = Path.cwd()
    manifest = load_manifest(repo_root)
    publish_root = repo_root / manifest["publish_path"]
    feedback_root = repo_root / manifest["feedback_path"]
    if not publish_root.exists():
        _die(f"publish path does not exist: {manifest['publish_path']}")

    feedback_root.mkdir(parents=True, exist_ok=True)
    state = _load_publish_state(repo_root)

    docx_files = sorted(publish_root.rglob("*.docx"))
    if not docx_files:
        _info(f"No .docx files under {manifest['publish_path']}/.")
        return

    targets = resolve_publish_targets(manifest, repo_root)
    output_to_source = {str(t["output_path"].resolve()): t["source"] for t in targets}

    pulled = 0
    skipped_no_new = 0
    for docx in docx_files:
        key = str(docx.resolve())
        source = output_to_source.get(key)
        if source is None:
            _warn(f"skipping {docx.relative_to(publish_root)} (no manifest match)")
            continue

        parsed = parse_docx_comments(docx)
        if not parsed["comments"]:
            continue

        prior = state.get(key, {}).get("seen_comment_ids", [])
        new_ids = _new_comment_ids(parsed, prior)
        if not new_ids:
            skipped_no_new += 1
            continue

        slug = _doc_slug(source, repo_root)
        stamp = _now_compact()
        out_name = f"{slug}-{stamp}.md"
        out_path = feedback_root / out_name
        out_path.write_text(
            render_feedback_file(source, docx, parsed, repo_root),
            encoding="utf-8",
        )
        _ok(f"{docx.relative_to(publish_root)} → {out_path.relative_to(repo_root)} "
            f"({len(new_ids)} new of {len(parsed['comments'])} total)")
        pulled += 1

        state[key] = {
            "last_pull": _now_local_iso(),
            "seen_comment_ids": [c["id"] for c in parsed["comments"]],
            "source": str(source.relative_to(repo_root)),
        }

    _save_publish_state(repo_root, state)

    _info("")
    if pulled == 0 and skipped_no_new == 0:
        _info("No docs had comments.")
    else:
        _info(f"Pulled: {pulled}; up-to-date: {skipped_no_new}.")


def cmd_docs_status(args):
    repo_root = Path.cwd()
    manifest_file = repo_root / MANIFEST_PATH
    if not manifest_file.is_file():
        _info(f"docs: not configured ({MANIFEST_PATH} missing). Run `mcc docs setup`.")
        return
    manifest = load_manifest(repo_root)
    publish_root = repo_root / manifest["publish_path"]
    feedback_root = repo_root / manifest["feedback_path"]

    _info(f"manifest:      {MANIFEST_PATH}")
    _info(f"publish_path:  {manifest['publish_path']}/  "
          f"({'exists' if publish_root.exists() else 'MISSING — symlink it before publish'})")
    _info(f"feedback_path: {manifest['feedback_path']}/")

    targets = resolve_publish_targets(manifest, repo_root)
    _info(f"declared docs: {len(targets)}")

    pending = 0
    if feedback_root.is_dir():
        pending = sum(1 for p in feedback_root.iterdir() if p.is_file() and p.suffix == ".md")
    _info(f"pending feedback (unaddressed): {pending}")
    if pending:
        _info("  Run /docs:address in any active Claude session to triage.")
