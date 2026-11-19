#!/usr/bin/env python3
"""Valida un mensaje de commit contra el estándar de la skill commit-message.

Uso:
  validate_commit_msg.py <archivo>          # como hook commit-msg
  validate_commit_msg.py -                  # leer de stdin
  validate_commit_msg.py --rev <commit>     # validar un commit existente

Sale con 0 si el mensaje cumple (o está exento) y con 1 si no.
"""
from __future__ import annotations

import re
import subprocess
import sys

TYPES = {
    "💥": "BREAKING", "🚑️": "HOTFIX", "🔒️": "SECURITY",
    "✨": "FEATURE", "💄": "UI", "♿️": "A11Y", "🔍️": "SEO",
    "🐛": "FIX", "⚡️": "PERF", "👽️": "API", "🗃️": "DB", "🚨": "LINT",
    "♻️": "REFACTOR", "🎨": "STYLE", "🚚": "MOVE", "🔥": "REMOVE", "🏷️": "TYPES",
    "🔖": "RELEASE", "🔧": "CONFIG", "📦️": "BUILD", "👷": "CI", "🧱": "INFRA", "🚀": "DEPLOY",
    "📝": "DOCS", "✅": "TEST", "🌐": "I18N", "🎉": "INIT", "🚧": "WIP", "⏪️": "REVERT",
    "🔀": "MERGE", "🍱": "ASSETS", "✏️": "TYPO",
}
VS16 = "️"
VERBS = {
    "Añade", "Corrige", "Elimina", "Refactoriza", "Extrae", "Reemplaza", "Simplifica",
    "Configura", "Actualiza", "Optimiza", "Migra", "Mueve", "Renombra", "Integra",
    "Activa", "Valida", "Documenta", "Revierte",
}
GENERIC_TITLES = ("actualiza archivos", "mejoras varias", "cambios menores", "ajustes")
BANNED_MOTIVO = ("se requiere", "es necesario", "para mejorar")
CATEGORIES = [
    "Nuevas Funcionalidades", "Mejoras", "Correcciones", "Refactorización",
    "Configuración", "Documentación", "Pruebas",
]
SECTIONS = ["· Motivo:", "· Cambios clave:", "· Beneficio:"]
EXEMPT = re.compile(r"^(Merge |Revert \"|fixup! |squash! |amend! )")
TRAILER = re.compile(r"^[A-Za-z][A-Za-z0-9-]*: .+")
RELEASE = re.compile(r"^v\d+\.\d+\.\d+(-(alpha|beta|rc)(\.\d+)?|-dev)?$")


def visible_len(text: str) -> int:
    """Longitud contando cada emoji como 1 carácter (sin el selector invisible)."""
    return len(text.replace(VS16, ""))


def clean(raw: str) -> list[str]:
    """Aplica lo mismo que git: quita comentarios y todo tras la línea de tijeras."""
    lines = []
    for line in raw.splitlines():
        if line.startswith("# ------------------------ >8"):
            break
        if line.startswith("#"):
            continue
        lines.append(line.rstrip())
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    # Git junta las líneas en blanco consecutivas; hacemos lo mismo.
    out: list[str] = []
    for line in lines:
        if line == "" and out and out[-1] == "":
            continue
        out.append(line)
    return out


def check_title(title: str, errors: list[str]) -> str | None:
    match = re.match(r"^(\S+) ([A-Z0-9]+): (.+)$", title)
    if not match:
        errors.append("Título: debe ser '<EMOJI> <TYPE>: <Verbo> <qué y dónde>'.")
        return None
    emoji, kind, rest = match.groups()
    expected = TYPES.get(emoji) or TYPES.get(emoji + VS16) or TYPES.get(emoji.replace(VS16, ""))
    if kind not in TYPES.values():
        errors.append(f"Título: tipo '{kind}' no existe en la taxonomía.")
    elif expected != kind:
        errors.append(f"Título: el emoji '{emoji}' no corresponde al tipo {kind}.")
    if visible_len(title) > 72:
        errors.append(f"Título: tiene {visible_len(title)} caracteres (máx. 72).")
    if title.endswith("."):
        errors.append("Título: no debe terminar en punto.")
    if kind == "RELEASE":
        if not RELEASE.match(rest):
            errors.append("Título: RELEASE debe ser exactamente '🔖 RELEASE: vX.Y.Z'.")
        return kind
    verb = rest.split()[0]
    if verb not in VERBS:
        errors.append(f"Título: el verbo '{verb}' no está en la lista permitida ({', '.join(sorted(VERBS))}).")
    if rest.lower().rstrip(".") in GENERIC_TITLES or rest.lower() in GENERIC_TITLES:
        errors.append("Título: es genérico; di qué cambia y dónde.")
    return kind


def check_sentence(name: str, block: list[str], errors: list[str]) -> None:
    if len(block) != 1:
        errors.append(f"{name}: debe ser 1 sola oración en 1 línea.")
        return
    text = block[0]
    if visible_len(text) > 120:
        errors.append(f"{name}: tiene {visible_len(text)} caracteres (máx. 120).")
    if name == "Motivo" and text.lower().startswith(BANNED_MOTIVO):
        errors.append("Motivo: no empieces con 'Se requiere', 'Es necesario' ni 'Para mejorar'.")


def check_changes(block: list[str], errors: list[str]) -> None:
    bullets = 0
    last_cat = -1
    variant = None
    for line in block:
        if line == "":
            continue
        if line.startswith("  - "):
            variant = variant or "A"
            if variant != "A":
                errors.append("Cambios clave: no mezcles viñetas de 2 y 4 espacios.")
            bullets += 1
            item = line[2:]
        elif line.startswith("    - "):
            variant = variant or "B"
            if variant != "B" or last_cat < 0:
                errors.append("Cambios clave: las viñetas de 4 espacios van bajo una categoría.")
            bullets += 1
            item = line[4:]
        elif re.match(r"^  \S.*:$", line):
            variant = variant or "B"
            name = line.strip()[:-1]
            if name not in CATEGORIES:
                errors.append(f"Cambios clave: categoría '{name}' no permitida ({', '.join(CATEGORIES)}).")
                last_cat = max(last_cat, 0)
                continue
            idx = CATEGORIES.index(name)
            if idx <= last_cat:
                errors.append("Cambios clave: categorías repetidas o fuera de orden.")
            last_cat = idx
            continue
        else:
            errors.append(f"Cambios clave: línea con sangría inválida: '{line}'.")
            continue
        if visible_len(item) > 100:
            errors.append(f"Cambios clave: viñeta de {visible_len(item)} caracteres (máx. 100): '{item[:40]}…'.")
        if not re.match(r"^- .+?: \S", item):
            errors.append(f"Cambios clave: usa la forma 'Entidad: Verbo + detalle': '{item[:40]}…'.")
    if bullets == 0:
        errors.append("Cambios clave: falta al menos 1 viñeta.")
    if bullets > 5:
        errors.append(f"Cambios clave: {bullets} viñetas (máx. 5).")


def validate(raw: str) -> list[str]:
    lines = clean(raw)
    if not lines:
        return []  # git aborta solo los mensajes vacíos
    if EXEMPT.match(lines[0]):
        return []
    errors: list[str] = []
    check_title(lines[0], errors)
    if len(lines) < 2 or lines[1] != "":
        errors.append("Formato: deja 1 línea en blanco después del título.")
    body = lines[1:]
    positions = []
    for section in SECTIONS:
        if body.count(section) != 1:
            errors.append(f"Formato: falta la sección '{section}' (o está repetida).")
            return errors
        positions.append(body.index(section))
    if positions != sorted(positions):
        errors.append("Formato: el orden debe ser Motivo, Cambios clave, Beneficio.")
        return errors
    for pos in positions:
        if pos + 1 >= len(body) or body[pos + 1] != "":
            errors.append(f"Formato: deja 1 línea en blanco después de '{body[pos]}'.")
    motivo = [l for l in body[positions[0] + 1:positions[1]] if l]
    cambios = body[positions[1] + 1:positions[2]]
    tail = body[positions[2] + 1:]
    paragraphs: list[list[str]] = []
    for line in tail:
        if line == "":
            paragraphs.append([])
        elif paragraphs:
            paragraphs[-1].append(line)
        else:
            paragraphs.append([line])
    paragraphs = [p for p in paragraphs if p]
    beneficio = paragraphs[0] if paragraphs else []
    for extra in paragraphs[1:]:
        if not all(TRAILER.match(l) for l in extra):
            errors.append("Formato: después de Beneficio solo se permiten trailers (Clave: valor).")
    check_sentence("Motivo", motivo, errors)
    check_changes(cambios, errors)
    check_sentence("Beneficio", beneficio, errors)
    return errors


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "--rev":
        if argv[2].startswith("-"):
            print("ERROR: --rev espera un commit, no una opción.", file=sys.stderr)
            return 2
        raw = subprocess.run(["git", "log", "-1", "--format=%B", "--end-of-options", argv[2]],
                             capture_output=True, text=True, check=True).stdout
    elif len(argv) == 2 and argv[1] == "-":
        raw = sys.stdin.read()
    elif len(argv) == 2:
        with open(argv[1], encoding="utf-8") as fh:
            raw = fh.read()
    else:
        print(__doc__, file=sys.stderr)
        return 2
    errors = validate(raw)
    if errors:
        print("✖ El mensaje de commit no cumple el estándar (skill commit-message):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print("  Corrige el mensaje y vuelve a hacer el commit; tu texto sigue en .git/COMMIT_EDITMSG.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
