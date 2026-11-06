#!/usr/bin/env python3
"""Ajoute un thème (un mot ou une phrase) à la section « Thèmes suivis » de watchlist.md.

--clean : affiche le thème nettoyé sans toucher au fichier.
Code de sortie 1 si le thème est invalide.
"""
import re
import sys
import unicodedata
from pathlib import Path

WATCHLIST = Path(__file__).resolve().parent.parent / "watchlist.md"
HEADING = "## Thèmes suivis"
MAX_LENGTH = 100


def clean(raw):
    """Un thème peut être une phrase. On retire ce qui casserait le fichier Markdown ou la lecture des cours."""
    text = unicodedata.normalize("NFC", raw)
    text = "".join(" " if ch.isspace() else ch for ch in text if ch.isprintable() or ch.isspace())
    text = text.replace("(", " ").replace(")", " ")  # « (TICKER) » est lu comme une valeur cotée par cours.py
    text = re.sub(r"\s+", " ", text).strip().lstrip("#>*+- ").strip()
    if not (2 <= len(text) <= MAX_LENGTH):
        sys.exit(f"Thème invalide : entre 2 et {MAX_LENGTH} caractères.")
    return text


def add(word):
    lines = WATCHLIST.read_text(encoding="utf-8").splitlines()
    if HEADING not in lines:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["", HEADING, ""]
    start = lines.index(HEADING) + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    existing = {l[2:].strip().lower() for l in lines[start:end] if l.startswith("- ")}
    if word.lower() in existing:
        return
    last = max([i for i in range(start, end) if lines[i].startswith("- ")], default=start)
    lines.insert(last + 1 if last > start else start + (1 if lines[start:start + 1] == [""] else 0), f"- {word}")
    WATCHLIST.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--clean":
        print(clean(args[1]))
    elif len(args) == 1:
        add(clean(args[0]))
    else:
        sys.exit(__doc__)
