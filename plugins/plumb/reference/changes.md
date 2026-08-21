# Changes — the transition line's source

This file is read by the SessionStart orientation: when a project launches under a
newer plumb than it last saw, the versions in between are announced, once, from the
entries here. **Every release adds an entry** — a release without one is invisible to
running projects, which is the exact presence failure this file exists to close.
Write entries FOR that ambient moment: one to three lines, action-pointing ("reread
the `bus` skill"), no changelog prose.

## 0.11.0
- New guard for shared checkouts: `git push` now surfaces outgoing commits recorded by
  ANOTHER session (print, not block). `plumb:establish` now asks the working-tree
  topology question — worktree-per-session is the recommended multi-session default.
- The Stop-hook inbox recipe (`plumb ledger guide`) gained its scoping section: the hook
  stays, keep `limit` small, fix mis-assignments at the source the first time one
  surfaces. Upstream filters are filed (NON-65/66/67).
- A day-one defect meant the 0.10.0 announcement never reached projects already running
  plumb. If the entry below is news: **reread the `bus` skill** — going idle is silent,
  tickers can wake you, large messages clip loudly with a retrieval pointer.

## 0.10.1
- Version transitions now announce themselves like this, at session start, once per
  project. You are reading the feature.

## 0.10.0
- **Bus physics changed — reread the `bus` skill.** Going idle is SILENT (nothing
  announces your stopping — if it means something, say it); "proceeding unless
  countermanded" means *proceed*; the board is an acknowledgment only where something
  subscribes to it. Large messages now clip LOUDLY with a `bus.py show <id>` retrieval
  pointer, and senders are warned at send time.
- **Tickers**: `[tickers.<name>]` in `.plumb.toml` runs project scripts inside plumb's
  monitor — the one surface that can WAKE an idle session (tracker inbox, CI). See the
  `bus` skill. `bus.py refs --since 2h` quiets the bus/tracker notification seam.
- Catalog mechanics: canonical `## <n>. <title>` headings; `plumb catalog next` /
  `plumb catalog append` claim entry numbers from the file itself.
- Image and other binary formats no longer trip the control-bytes guard.

## 0.9.0
- `plumb:feedback` — the step-back skill: notice what you have stopped noticing, write
  what the plumb team can use; your PO owns the channel back.

## 0.8.3
- The nonlinear Stop-hook inbox recipe uses `runAsHook: true` (hook-shaped output that
  can re-invoke you with the items). `mcc list` became sugar for `mcc session list`.
