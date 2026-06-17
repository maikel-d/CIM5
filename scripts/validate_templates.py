#!/usr/bin/env python3
"""
Script independiente: validate_templates.py

Detecta templates HTML con contenido fuera de {% block %} tags.
No requiere Django instalado.

Uso:
    python scripts/validate_templates.py [--base-dir RUTA]
"""

import re
import sys
import argparse
from pathlib import Path


def check_file(filepath):
    """Return list of (lineno, snippet) for content outside blocks."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return []

    if "{% extends" not in content:
        return []

    lines = content.splitlines()
    block_depth = 0
    findings = []

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()

        if not stripped:
            continue
        if stripped.startswith("{#") or stripped.startswith("{% comment"):
            continue

        opens = len(re.findall(r"{%\s*block\s+\w+", stripped))
        closes = len(re.findall(r"{%\s*endblock", stripped))
        depth_change = opens - closes

        if block_depth == 0:
            if opens > 0:
                pass
            elif depth_change == 0 and closes == 0:
                cleaned = re.sub(r"{%[^%]*%}", "", stripped)
                cleaned = re.sub(r"{{.*?}}", "", cleaned)
                cleaned = cleaned.strip()

                if cleaned:
                    if re.match(
                        r"{%\s*(extends|load|static|spaceless|lorem)",
                        stripped
                    ):
                        continue
                    findings.append((lineno, cleaned[:100]))

        block_depth += depth_change
        if block_depth < 0:
            block_depth = 0

    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Valida que los templates HTML tengan su contenido dentro de blocks"
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Directorio raiz del proyecto (default: directorio actual)"
    )
    args = parser.parse_args()

    base = Path(args.base_dir)
    excluded = {"venv", "node_modules", ".git", "__pycache__", "env", ".venv"}

    templates = sorted(
        p for p in base.rglob("*.html")
        if not any(part in excluded for part in p.parts)
    )

    if not templates:
        print("No HTML templates found.")
        sys.exit(0)
        return

    msg = "Escaneando {} templates del proyecto...".format(len(templates))
    print(msg)
    print()

    findings = []
    for fp in templates:
        issues = check_file(fp)
        if issues:
            findings.append((fp, issues))

    if not findings:
        print("OK: Todos los templates tienen su contenido dentro de {% block %}.")
        sys.exit(0)
        return

    msg = "ERROR: {} template(s) con contenido fuera de bloques:".format(len(findings))
    print(msg)
    print()

    for fp, issues in findings:
        rel = fp.relative_to(base)
        print("  {}:".format(rel))
        for lineno, snippet in issues:
            print("    Linea {:<5} {}".format(lineno, snippet))
        print()

    msg = "{} archivo(s) con contenido fuera de bloques. ".format(len(findings))
    msg += "Mueve ese contenido dentro de un {% block %}."
    print()
    print(msg)

    sys.exit(1)


if __name__ == "__main__":
    main()
