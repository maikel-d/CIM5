#!/usr/bin/env python3
"""Linter estatico para el Sistema de Gestion - Direccion General.

Detecta patrones problematicos comunes:
  - redirect() con query string concatenado al nombre de la vista
  - Archivo views.py monolitico (debe estar en views/ modulos)

Uso:
  python scripts/lint_django.py [--base-dir RUTA]

Exit codes:
  0 = Todo correcto
  1 = Se encontraron problemas
"""

import os
import re
import sys


def find_py_files(base_dir):
    """Encuentra archivos .py excluyendo directorios comunes."""
    files = []
    exclude = {"__pycache__", "venv", "env", ".venv", ".env",
               "node_modules", "staticfiles", "media", "logs",
               "backups", "data", "dist", "build"}
    for root, dirs, filenames in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in exclude]
        for f in filenames:
            if f.endswith(".py"):
                files.append(os.path.join(root, f))
    return files


def check_redirect_with_query(filepath):
    """Busca redirect con query string concatenado al nombre (NoReverseMatch)."""
    errors = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (IOError, OSError):
        return errors

    # Construir patrones para todas las combinaciones de comillas
    # Ej: redirect(url_name + query_string) debe usar reverse() por separado
    patterns = []
    for oq in ["'", '"']:
        for iq in ["'", '"']:
            pat = (
                r"redirect\s*\(\s*" + oq + r"[^" + oq + r"]*" + oq +
                r"\s*\+\s*\(?\s*f?" + iq + r"[?&]" +
                r"[^" + iq + r"]*" + iq
            )
            patterns.append(re.compile(pat))

    for pat in patterns:
        for m in pat.finditer(content):
            line_num = content[:m.start()].count("\n") + 1
            errors.append({
                "file": filepath,
                "line": line_num,
                "message": "redirect() concatenado con query string. Usar reverse() + query params por separado.",
                "severity": "ERROR",
            })
    return errors


def check_monolithic_views_py(filepath):
    """Verifica que no exista direccion/views.py (debe estar en views/)."""
    bname = os.path.basename(filepath)
    dname = os.path.basename(os.path.dirname(filepath))
    if bname == "views.py" and dname == "direccion":
        return [{"file": filepath, "line": 1,
                 "message": "Archivo views.py monolitico detectado. Usar modulos en views/.",
                 "severity": "ERROR"}]
    return []


def run_checks(base_dir):
    all_errors = []
    script_path = os.path.abspath(__file__)
    for fp in find_py_files(base_dir):
        if os.path.abspath(fp) == script_path:
            continue  # No escanear el propio linter
        all_errors.extend(check_redirect_with_query(fp))
        all_errors.extend(check_monolithic_views_py(fp))
    return all_errors


def print_report(errors):
    if not errors:
        print("OK - No se encontraron problemas.")
        return 0
    ecount = sum(1 for e in errors if e["severity"] == "ERROR")
    print("Problemas encontrados:")
    for e in errors:
        rel = os.path.relpath(e["file"], start=os.getcwd())
        print("  %s:%d [%s] %s" % (rel, e["line"], e["severity"], e["message"]))
    return 1 if ecount else 0


if __name__ == "__main__":
    bdir = "."
    if len(sys.argv) > 2 and sys.argv[1] == "--base-dir":
        bdir = sys.argv[2]
    sys.exit(print_report(run_checks(bdir)))
