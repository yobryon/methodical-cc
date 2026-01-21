# MAM Tools

Standalone utilities for the Multi-Agent Methodology. These are **not** part of the plugin runtime - they're helper scripts for specific tasks.

## Stage-to-Sprint Migration

If you've been using "stage" terminology in your project and want to switch to "sprint" (to align with the MAM plugin), these tools help migrate your files and content.

### Claude-Powered Migration (Recommended)

Uses Claude Code to intelligently find and update PM terminology while leaving domain content alone.

```bash
# From your project directory
/path/to/cc-methodology/tools/migrate-stage-to-sprint.sh .

# Or specify the project path
./migrate-stage-to-sprint.sh /path/to/your-project
```

**What it does:**
- Explores your project structure
- Identifies PM artifacts (briefs, plans, logs, deltas, roadmap, CLAUDE.md)
- Renames files: `implementation_plan_stage19.md` → `implementation_plan_sprint19.md`
- Updates content: "Stage 19" → "Sprint 19"
- Leaves domain content alone (won't touch `rocket-booster-stage.md`)

**Modes:**
- **Interactive**: Claude asks permission for each change (safer, slower)
- **Autonomous**: Claude makes all changes without prompts (faster)

**Safety:**
- Review changes with `git diff` before committing
- If something goes wrong: `git checkout .` to revert everything
- Git history is unchanged - old commits keep their original terminology

### Regex-Based Migration (Fallback)

A simpler Python script that uses pattern matching. Faster but less intelligent - may catch false positives.

```bash
python /path/to/cc-methodology/tools/migrate-stage-to-sprint-regex.py /path/to/your-project
```

**What it does:**
- Scans for files with `stage` + number in the name
- Scans content for patterns like "Stage 19", "stage_19", etc.
- Shows a report of what would change
- Asks for confirmation before applying

**When to use:**
- Quick scan to see what's there
- If Claude-powered approach isn't available
- For simpler projects with obvious PM artifacts

## Contributing

These tools are separate from the plugin. Feel free to modify them for your needs - they won't affect the MAM plugin behavior.
