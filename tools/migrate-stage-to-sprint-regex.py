#!/usr/bin/env python3
"""
Stage-to-Sprint Migration Utility

Finds all "stage" references in a project and helps migrate them to "sprint".
Handles both file names and file content.

Usage:
    python stage-to-sprint-migration.py [project_path]

If no path provided, uses current directory.
"""

import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class FileRename:
    old_path: Path
    new_path: Path


@dataclass
class ContentChange:
    file_path: Path
    line_number: int
    old_line: str
    new_line: str
    context_before: list[str]
    context_after: list[str]


class StageMigrator:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.file_renames: list[FileRename] = []
        self.content_changes: list[ContentChange] = []

        # Patterns to match (case-insensitive where appropriate)
        # Word boundary aware to avoid changing "backstage" etc.
        self.content_patterns = [
            (r'\bStage\s+(\d+)', r'Sprint \1'),           # "Stage 19" -> "Sprint 19"
            (r'\bstage\s+(\d+)', r'sprint \1'),           # "stage 19" -> "sprint 19"
            (r'\bSTAGE\s+(\d+)', r'SPRINT \1'),           # "STAGE 19" -> "SPRINT 19"
            (r'\bStage(\d+)', r'Sprint\1'),               # "Stage19" -> "Sprint19"
            (r'\bstage(\d+)', r'sprint\1'),               # "stage19" -> "sprint19"
            (r'_stage(\d+)', r'_sprint\1'),               # "_stage19" -> "_sprint19"
            (r'stage_(\d+)', r'sprint_\1'),               # "stage_19" -> "sprint_19"
        ]

        # File extensions to scan for content
        self.scan_extensions = {'.md', '.txt', '.json', '.yaml', '.yml', '.py', '.js', '.ts', '.tsx', '.jsx'}

        # Directories to skip
        self.skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build'}

    def scan(self):
        """Scan the project for stage references."""
        print(f"\nScanning {self.project_path}...\n")

        for root, dirs, files in os.walk(self.project_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]

            for filename in files:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(self.project_path)

                # Check for file rename
                if re.search(r'stage\d+', filename, re.IGNORECASE):
                    new_filename = re.sub(r'stage(\d+)', r'sprint\1', filename, flags=re.IGNORECASE)
                    new_path = Path(root) / new_filename
                    self.file_renames.append(FileRename(file_path, new_path))

                # Check content if it's a text file we care about
                if file_path.suffix.lower() in self.scan_extensions:
                    self._scan_file_content(file_path)

    def _scan_file_content(self, file_path: Path):
        """Scan a file's content for stage references."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except (UnicodeDecodeError, PermissionError):
            return

        for i, line in enumerate(lines):
            for pattern, replacement in self.content_patterns:
                if re.search(pattern, line):
                    new_line = re.sub(pattern, replacement, line)
                    if new_line != line:
                        # Get context
                        context_before = lines[max(0, i-2):i]
                        context_after = lines[i+1:min(len(lines), i+3)]

                        self.content_changes.append(ContentChange(
                            file_path=file_path,
                            line_number=i + 1,
                            old_line=line.rstrip('\n'),
                            new_line=new_line.rstrip('\n'),
                            context_before=[l.rstrip('\n') for l in context_before],
                            context_after=[l.rstrip('\n') for l in context_after]
                        ))
                        break  # Only record once per line

    def show_report(self):
        """Display what would change."""
        print("=" * 70)
        print("STAGE → SPRINT MIGRATION REPORT")
        print("=" * 70)

        # File renames
        if self.file_renames:
            print(f"\n📁 FILE RENAMES ({len(self.file_renames)} files)\n")
            for rename in self.file_renames:
                old_rel = rename.old_path.relative_to(self.project_path)
                new_rel = rename.new_path.relative_to(self.project_path)
                print(f"  {old_rel}")
                print(f"    → {new_rel}")
                print()
        else:
            print("\n📁 FILE RENAMES: None found\n")

        # Content changes grouped by file
        if self.content_changes:
            print(f"\n📝 CONTENT CHANGES ({len(self.content_changes)} lines across multiple files)\n")

            # Group by file
            changes_by_file: dict[Path, list[ContentChange]] = {}
            for change in self.content_changes:
                if change.file_path not in changes_by_file:
                    changes_by_file[change.file_path] = []
                changes_by_file[change.file_path].append(change)

            for file_path, changes in changes_by_file.items():
                rel_path = file_path.relative_to(self.project_path)
                print(f"  📄 {rel_path} ({len(changes)} changes)")
                print()

                for change in changes[:5]:  # Show first 5 per file
                    print(f"    Line {change.line_number}:")
                    print(f"      - {change.old_line[:80]}{'...' if len(change.old_line) > 80 else ''}")
                    print(f"      + {change.new_line[:80]}{'...' if len(change.new_line) > 80 else ''}")
                    print()

                if len(changes) > 5:
                    print(f"    ... and {len(changes) - 5} more changes in this file\n")
        else:
            print("\n📝 CONTENT CHANGES: None found\n")

        print("=" * 70)
        print(f"SUMMARY: {len(self.file_renames)} file renames, {len(self.content_changes)} content changes")
        print("=" * 70)

    def apply_changes(self, dry_run: bool = False):
        """Apply the changes."""
        if dry_run:
            print("\n🔍 DRY RUN - No changes will be made\n")
            return

        print("\n🚀 APPLYING CHANGES...\n")

        # Apply content changes first (before renaming files)
        files_modified = set()
        for change in self.content_changes:
            if change.file_path not in files_modified:
                self._apply_content_changes_to_file(change.file_path)
                files_modified.add(change.file_path)

        print(f"  ✓ Modified content in {len(files_modified)} files")

        # Apply file renames
        for rename in self.file_renames:
            # Update path if the file was in our modified set
            old_path = rename.old_path
            if old_path in files_modified:
                # File content already updated
                pass
            rename.old_path.rename(rename.new_path)

        print(f"  ✓ Renamed {len(self.file_renames)} files")

        print("\n✅ Migration complete!\n")

    def _apply_content_changes_to_file(self, file_path: Path):
        """Apply all content changes to a single file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for pattern, replacement in self.content_patterns:
            content = re.sub(pattern, replacement, content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)


def main():
    # Get project path
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1]).resolve()
    else:
        project_path = Path.cwd()

    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}")
        sys.exit(1)

    print(f"\n🔄 Stage-to-Sprint Migration Utility")
    print(f"   Project: {project_path}\n")

    # Create migrator and scan
    migrator = StageMigrator(project_path)
    migrator.scan()

    # Show report
    migrator.show_report()

    if not migrator.file_renames and not migrator.content_changes:
        print("\nNo stage references found. Nothing to migrate!")
        return

    # Ask for confirmation
    print("\nOptions:")
    print("  [d] Dry run - show what would change without changing")
    print("  [y] Yes - apply all changes")
    print("  [n] No - exit without changes")
    print()

    while True:
        choice = input("What would you like to do? [d/y/n]: ").strip().lower()

        if choice == 'd':
            migrator.apply_changes(dry_run=True)
            # Ask again
            continue
        elif choice == 'y':
            # Final confirmation
            confirm = input("\n⚠️  This will modify files. Are you sure? [yes/no]: ").strip().lower()
            if confirm == 'yes':
                migrator.apply_changes(dry_run=False)
            else:
                print("Aborted.")
            break
        elif choice == 'n':
            print("Aborted. No changes made.")
            break
        else:
            print("Please enter 'd', 'y', or 'n'")


if __name__ == "__main__":
    main()
