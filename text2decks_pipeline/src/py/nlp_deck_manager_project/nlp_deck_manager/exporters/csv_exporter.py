from __future__ import annotations

import csv
import json
from pathlib import Path

from nlp_deck_manager.models import Note

ANKI_FIELDNAMES = [
    "lemma",
    "language",
    "note_type",
    "translation_it",
    "article",
    "part_of_speech",
    "inflection",
    "conjugation",
    "examples",
    "source_rank",
    "source_frequency",
    "extra_json",
    "tags",
]


def export_notes_to_anki_csv(path: Path, notes: list[Note]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ANKI_FIELDNAMES)
        writer.writeheader()
        for note in notes:
            fields = note.fields
            writer.writerow(
                {
                    "lemma": note.lemma,
                    "language": note.language,
                    "note_type": note.note_type,
                    "translation_it": fields.get("translation_it", ""),
                    "article": fields.get("article", ""),
                    "part_of_speech": fields.get("part_of_speech", ""),
                    "inflection": fields.get("declension_json", ""),
                    "conjugation": fields.get("conjugation_json", ""),
                    "examples": fields.get("examples_json", ""),
                    "source_rank": fields.get("source_rank", ""),
                    "source_frequency": fields.get("source_frequency", ""),
                    "extra_json": json.dumps(fields, ensure_ascii=False, sort_keys=True),
                    "tags": " ".join(note.tags),
                }
            )
