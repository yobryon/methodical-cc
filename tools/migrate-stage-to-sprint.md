# Stage-to-Sprint Terminology Migration

You are performing a one-time terminology migration for a project that has been using the Multi-Agent Methodology with "stage" terminology, and needs to switch to "sprint" terminology.

## Context

This project has been using "stage" instead of "sprint" for its project management artifacts:
- Files named like `implementation_plan_stage19.md` instead of `sprint`
- Content referring to "Stage 19" instead of "Sprint 19"
- References in CLAUDE.md, roadmaps, briefs, logs, and deltas

We need to migrate ALL project management references from "stage" to "sprint" while being careful NOT to change domain-specific uses of "stage" that are unrelated to project management.

## What IS Project Management (CHANGE THESE)

- Sprint/stage artifacts: `implementation_plan_*`, `implementor_brief_*`, `implementation_log_*`
- Delta files: `delta_*.md`
- Roadmap files: `roadmap.md`
- Project CLAUDE.md files: `.claude/CLAUDE.md`
- References to "Stage N" or "stage N" when talking about sprints/iterations of work
- Headers like "## Stage 19: Feature Name"
- References like "completed in stage 5" or "planned for stage 12"

## What is NOT Project Management (DO NOT CHANGE)

- Domain content about literal stages (rocket stages, pipeline stages, game stages, etc.)
- Code variables or functions with "stage" in the name that are domain-related
- Documentation about staging environments (that's different from sprint stages)
- Any file that's clearly a product artifact, not a PM artifact

## Your Mission

1. **Explore First**: Use Glob and Read to understand the project structure. Find:
   - All files with "stage" + number in the filename
   - All markdown files in `docs/`
   - The `.claude/CLAUDE.md` file
   - Any other files that might contain PM references

2. **Identify PM Artifacts**: For each file, determine if it's a PM artifact or domain content. Be smart about this - read the content if you're unsure.

3. **Rename Files**: Rename PM artifact files from `*stageN*` to `*sprintN*`

4. **Update Content**: In PM artifacts, update references:
   - "Stage N" → "Sprint N"
   - "stage N" → "sprint N"
   - "STAGE N" → "SPRINT N"
   - "stageN" → "sprintN" (in file references)
   - Be case-aware and context-aware

5. **Report What You Did**: After making changes, summarize:
   - Files renamed
   - Files with content updated
   - Any files you intentionally skipped and why

## Important Guidelines

- **When in doubt, read the file** - understand context before changing
- **Preserve formatting** - don't reformat files, just change the terminology
- **Be thorough** - check all markdown files, not just obvious ones
- **Be conservative with code** - only change comments/strings that are clearly PM references
- **Skip binary files, node_modules, .git, etc.**

## Begin

Start by exploring the project structure to understand what we're working with. Then systematically migrate the terminology.
