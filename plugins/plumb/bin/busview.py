# /// script
# requires-python = ">=3.9"
# dependencies = ["textual>=1.0"]
# ///
"""plumb bus view — a mailbox TUI over a project's bus. The observer's window.

STRICTLY READ-ONLY — by ruling, not just by v1 scope, and enforced by
construction: the database is opened with SQLite's `mode=ro`, and there is no
code path that writes. The moment an observer can act from this window they
become a participant with an identity on the bus, and that is a different tool.

Launched by `mcc bus view`, which shells out to `uv run` — the PEP 723 header
above declares this script's own dependencies, so core mcc stays stdlib-only
while this side surface pays for its own comfort.

Layout: mailbox rail on the left (All + one inbox per agent, with pending
counts), message list on top, markdown-rendered detail below. Polls at 1 Hz —
level-triggered like everything else on this bus — and only rebuilds when the
data actually changed.
"""

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import DataTable, Footer, Header, Label, ListItem, ListView, Markdown

DEFAULT_DB = ".mcc/bus.db"


# ------------------------------------------------------------------ data layer

def db_path(explicit=None):
    if explicit:
        return Path(explicit)
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return Path(root) / DEFAULT_DB


def open_ro(path):
    """Read-only connection. mode=ro makes the ruling mechanical."""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def mailboxes(conn):
    """(name, pending_count) per known agent, from traffic + check-ins."""
    rows = conn.execute(
        "SELECT a.agent AS agent, COALESCE(p.n, 0) AS pending FROM "
        "  (SELECT agent FROM agents UNION "
        "   SELECT DISTINCT recipient FROM messages UNION "
        "   SELECT DISTINCT sender FROM messages) a "
        "LEFT JOIN (SELECT recipient, COUNT(*) n FROM messages "
        "           WHERE delivered_at IS NULL AND quarantined=0 "
        "           GROUP BY recipient) p ON p.recipient = a.agent "
        "ORDER BY a.agent").fetchall()
    return [(r["agent"], r["pending"]) for r in rows]


def fetch(conn, box=None, gating_only=False, undelivered_only=False, limit=500):
    sql = "SELECT * FROM messages"
    where, params = [], []
    if box:
        where.append("recipient=?")
        params.append(box)
    if gating_only:
        where.append("urgency='gating'")
    if undelivered_only:
        where.append("delivered_at IS NULL AND quarantined=0")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    return conn.execute(sql, params).fetchall()


def change_token(conn):
    """Cheap fingerprint of bus state — rebuild only when it moves."""
    r = conn.execute(
        "SELECT COUNT(*), COALESCE(MAX(id),0), "
        "  SUM(delivered_at IS NOT NULL), SUM(acked_at IS NOT NULL), "
        "  SUM(quarantined) FROM messages").fetchone()
    return tuple(r)


def state_of(r):
    if r["quarantined"]:
        return "QUARANTINED"
    if r["delivered_at"]:
        return f"delivered:{r['delivered_by']}"
    return "pending"


def commit_of(r):
    try:
        return r["delivered_commit"]
    except (KeyError, IndexError):
        return None


def fmt_ts(epoch):
    return time.strftime("%m-%d %H:%M:%S", time.localtime(epoch))


# ------------------------------------------------------------------------ TUI

class BusView(App):
    TITLE = "plumb bus"

    CSS = """
    #boxes { width: 26; border-right: solid $secondary; }
    #boxes ListItem { padding: 0 1; }
    #msgs  { height: 45%; border-bottom: solid $secondary; }
    #detail { padding: 1 2; }
    #detail-head { padding: 0 2; color: $text-muted; }
    """

    BINDINGS = [
        Binding("q", "quit", "quit"),
        Binding("g", "toggle_gating", "gating only"),
        Binding("u", "toggle_undelivered", "undelivered only"),
        Binding("r", "refresh_now", "refresh"),
        Binding("tab", "focus_next", "next pane", show=False),
    ]

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.conn = open_ro(path)
        self.box = None            # None = All
        self.gating_only = False
        self.undelivered_only = False
        self._token = None
        self._boxes = []

    # -- layout

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield ListView(id="boxes")
            with Vertical():
                yield DataTable(id="msgs", cursor_type="row", zebra_stripes=True)
                yield Label("", id="detail-head")
                with VerticalScroll():
                    yield Markdown("", id="detail")
        yield Footer()

    def on_mount(self):
        table = self.query_one("#msgs", DataTable)
        table.add_columns("id", "time", "!", "from", "to", "state", "thread")
        self.refresh_all(force=True)
        self.set_interval(1.0, self.refresh_all)

    # -- state → widgets

    def refresh_all(self, force=False):
        try:
            token = change_token(self.conn)
        except sqlite3.OperationalError:
            return  # a writer held the lock; next tick
        if not force and token == self._token:
            return
        self._token = token
        self.rebuild_boxes()
        self.rebuild_table()

    def rebuild_boxes(self):
        boxes = mailboxes(self.conn)
        if boxes == self._boxes:
            return
        self._boxes = boxes
        lv = self.query_one("#boxes", ListView)
        selected = self.box
        lv.clear()
        total_pending = sum(p for _, p in boxes)
        lv.append(ListItem(Label(f"All ({total_pending} pending)"), name="__all__"))
        for agent, pending in boxes:
            tag = f" ({pending} pending)" if pending else ""
            lv.append(ListItem(Label(f"@{agent}{tag}"), name=agent))
        names = ["__all__"] + [a for a, _ in boxes]
        try:
            lv.index = names.index(selected if selected else "__all__")
        except ValueError:
            lv.index = 0

    def rebuild_table(self):
        table = self.query_one("#msgs", DataTable)
        keep = self.current_id()
        table.clear()
        rows = fetch(self.conn, self.box, self.gating_only, self.undelivered_only)
        for r in rows:
            table.add_row(
                str(r["id"]), fmt_ts(r["created_at"]),
                "!" if r["urgency"] == "gating" else "",
                f"@{r['sender']}", f"@{r['recipient']}",
                state_of(r), r["thread"] or "",
                key=str(r["id"]),
            )
        if rows:
            target = 0
            if keep is not None:
                ids = [str(r["id"]) for r in rows]
                if str(keep) in ids:
                    target = ids.index(str(keep))
            table.move_cursor(row=target)
            self.show_detail(rows[target]["id"])
        else:
            self.show_detail(None)
        self.update_subtitle(len(rows))

    def update_subtitle(self, shown):
        bits = [str(self.path), f"{shown} shown"]
        if self.box:
            bits.append(f"inbox @{self.box}")
        if self.gating_only:
            bits.append("GATING ONLY")
        if self.undelivered_only:
            bits.append("UNDELIVERED ONLY")
        self.sub_title = "  ·  ".join(bits)

    def current_id(self):
        table = self.query_one("#msgs", DataTable)
        if table.row_count == 0 or table.cursor_row is None:
            return None
        try:
            return int(table.coordinate_to_cell_key(
                (table.cursor_row, 0)).row_key.value)
        except Exception:
            return None

    def show_detail(self, msg_id):
        head = self.query_one("#detail-head", Label)
        md = self.query_one("#detail", Markdown)
        if msg_id is None:
            head.update("")
            md.update("*no messages in this view*")
            return
        r = self.conn.execute("SELECT * FROM messages WHERE id=?",
                              (msg_id,)).fetchone()
        if r is None:
            return
        parts = [f"#{r['id']}", f"@{r['sender']} → @{r['recipient']}",
                 r["urgency"].upper(), state_of(r)]
        if r["thread"]:
            parts.append(f"thread {r['thread']}")
        if r["record_ref"]:
            parts.append(f"record {r['record_ref']}")
        if r["delivered_at"]:
            parts.append(f"delivered {fmt_ts(r['delivered_at'])}")
        if commit_of(r):
            parts.append(f"repo @{commit_of(r)}")
        head.update("  ·  ".join(parts))
        md.update(r["body"])

    # -- events

    def on_list_view_highlighted(self, event):
        name = event.item.name if event.item else None
        new_box = None if name in (None, "__all__") else name
        if new_box != self.box:
            self.box = new_box
            self.rebuild_table()

    def on_data_table_row_highlighted(self, event):
        try:
            self.show_detail(int(event.row_key.value))
        except (TypeError, ValueError):
            pass

    # -- actions

    def action_toggle_gating(self):
        self.gating_only = not self.gating_only
        self.rebuild_table()

    def action_toggle_undelivered(self):
        self.undelivered_only = not self.undelivered_only
        self.rebuild_table()

    def action_refresh_now(self):
        self.refresh_all(force=True)


# ----------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="read-only mailbox view over a plumb bus")
    ap.add_argument("--db", help=f"bus database (default: ./{DEFAULT_DB})")
    ap.add_argument("--check", action="store_true",
                    help="open the db, print a summary, exit (no TUI)")
    ap.add_argument("--smoke", action="store_true",
                    help="run the TUI headless for one beat and exit (CI)")
    args = ap.parse_args()

    path = db_path(args.db)
    if not path.is_file():
        print(f"busview: no bus database at {path}\n"
              f"  This project has no bus traffic yet (the store is created on "
              f"first use). Run from the project root, or pass --db.",
              file=sys.stderr)
        return 1

    if args.check:
        conn = open_ro(path)
        token = change_token(conn)
        print(f"db: {path}")
        print(f"messages: {token[0]}  max-id: {token[1]}  "
              f"delivered: {token[2] or 0}  acked: {token[3] or 0}  "
              f"quarantined: {token[4] or 0}")
        for agent, pending in mailboxes(conn):
            print(f"  @{agent}: {pending} pending")
        return 0

    if args.smoke:
        import asyncio

        async def _smoke():
            app = BusView(path)
            async with app.run_test() as pilot:
                await pilot.pause()
                table = app.query_one("#msgs", DataTable)
                print(f"smoke: rows={table.row_count} boxes={len(app._boxes)}")
        asyncio.run(_smoke())
        return 0

    BusView(path).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
