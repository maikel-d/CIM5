"""
Management command: validate_template_blocks

Detects project templates that have HTML content or scripts placed
OUTSIDE of {% block %} tags. Only checks templates under BASE_DIR
(project templates, not venv or third-party packages).

Usage:
    python manage.py validate_template_blocks
"""

import re
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Detects project templates with content outside {% block %} tags "
        "(content that gets silently ignored by Django)."
    )

    def handle(self, *args, **options):
        base = Path(settings.BASE_DIR)
        # Exclude venv, node_modules, .git, and __pycache__
        excluded = {"venv", "node_modules", ".git", "__pycache__", "env", ".venv"}
        templates = sorted(
            p for p in base.rglob("*.html")
            if not any(part in excluded for part in p.parts)
        )

        if not templates:
            self.stdout.write(self.style.WARNING("No HTML templates found."))
            return

        self.stdout.write(
            "Escaneando {} templates del proyecto...\n".format(len(templates))
        )

        findings = []
        for fp in templates:
            issues = self._check_file(fp)
            if issues:
                findings.append((fp, issues))

        if not findings:
            self.stdout.write(
                self.style.SUCCESS(                        "OK: Todos los templates tienen su contenido "
                        "dentro de {% block %}."
                )
            )
            return

        self.stdout.write(
            self.style.ERROR(                    "ERROR: {} template(s) con contenido fuera de bloques:\n".format(
                    len(findings)
                )
            )
        )

        for fp, issues in findings:
            rel = fp.relative_to(base)
            self.stdout.write("  {}:".format(rel))
            for lineno, snippet in issues:
                self.stdout.write(
                    "    Linea {:<5} {}".format(lineno, snippet)
                )
            self.stdout.write("")

        self.stdout.write(
            self.style.WARNING(
                "\n{} archivo(s) con contenido fuera de bloques. ".format(
                    len(findings)
                )
                + "Mueve ese contenido dentro de un {% block %}."
            )
        )

        # Return non-zero exit code for CI
        raise SystemExit(1)

    def _check_file(self, filepath):
        """Return list of (lineno, snippet) for content outside blocks."""
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            return []

        # Only check templates that extend a parent
        if "{% extends" not in content:
            return []

        lines = content.splitlines()
        block_depth = 0
        findings = []

        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip empty lines and Django comments
            if not stripped:
                continue
            if stripped.startswith("{#") or stripped.startswith("{% comment"):
                continue

            # Count block depth changes on this line
            opens = len(re.findall(r"{%\s*block\s+\w+", stripped))
            closes = len(re.findall(r"{%\s*endblock", stripped))
            depth_change = opens - closes

            # Check if line has content at root depth (outside any block)
            if block_depth == 0:
                if opens > 0:
                    # Starting a new block on this line - content is inside the block
                    # Don't flag (e.g. {% block title %}content{% endblock %})
                    pass
                elif depth_change == 0 and closes == 0:
                    # No block activity at all on this line
                    # Remove all Django template tags and variables
                    cleaned = re.sub(r"{%[^%]*%}", "", stripped)
                    cleaned = re.sub(r"{{.*?}}", "", cleaned)
                    cleaned = cleaned.strip()

                    if cleaned:
                        # Allow only these template tags at root level
                        if re.match(
                            r"{%\s*(extends|load|static|spaceless|lorem)\b",
                            stripped
                        ):
                            continue
                        findings.append((lineno, cleaned[:100]))

            block_depth += depth_change
            if block_depth < 0:
                block_depth = 0

        return findings