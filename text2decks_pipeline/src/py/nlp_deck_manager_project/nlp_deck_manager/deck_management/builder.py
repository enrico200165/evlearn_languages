from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from nlp_deck_manager.models import Note, RankedLemmaRow
from nlp_deck_manager.notes import make_note_from_ranked_row
from nlp_deck_manager.reference_db import ReferenceDb


@dataclass(frozen=True)
class DeckBuildResult:
    deck_name: str
    created_notes: int
    skipped_duplicates: int
    intentional_duplicates: int
    report_rows: list[dict[str, object]]


def register_rows_as_deck_notes(
    *,
    db: ReferenceDb,
    rows: list[RankedLemmaRow],
    language: str,
    deck_name: str,
    deck_kind: str,
    deck_description: str | None,
    relation_description_template: str,
    skip_core_duplicates: bool = False,
    intentional_duplicates: dict[str, str] | None = None,
) -> DeckBuildResult:
    intentional_duplicates = intentional_duplicates or {}
    deck_id = db.upsert_deck(
        language=language,
        deck_name=deck_name,
        description=deck_description,
        deck_kind=deck_kind,
    )
    created = 0
    skipped = 0
    intentional = 0
    report_rows: list[dict[str, object]] = []

    for row in rows:
        vocab_id = db.get_vocab_id(language=language, normalized_lemma=row.normalized_lemma)
        if vocab_id is None:
            report_rows.append(_report(row, deck_name, "ERROR", "lemma non presente nel Reference DB"))
            continue

        already_in_core = db.lemma_is_in_core_deck(language=language, normalized_lemma=row.normalized_lemma)
        duplicate_description = intentional_duplicates.get(row.normalized_lemma) or intentional_duplicates.get(row.lemma)

        if skip_core_duplicates and already_in_core and not duplicate_description:
            skipped += 1
            report_rows.append(_report(row, deck_name, "SKIPPED_CORE_DUPLICATE", "lemma già collegato a deck Core", already_in_core=True))
            continue

        if already_in_core and duplicate_description:
            intentional += 1
            relation_description = duplicate_description[:255]
            action = "ADDED_INTENTIONAL_DUPLICATE"
        else:
            relation_description = relation_description_template.format(
                lemma=row.lemma,
                rank=row.rank,
                frequency=row.frequency,
                core_band=row.core_band,
                deck_name=deck_name,
            )[:255]
            action = "ADDED"

        db.link_lemma_to_deck(vocab_id=vocab_id, deck_id=deck_id, deck_description=relation_description)
        note = make_note_from_ranked_row(row, deck_name=deck_name)
        note.vocab_id = vocab_id
        note.deck_id = deck_id
        db.save_note(note)
        created += 1
        report_rows.append(_report(row, deck_name, action, relation_description, already_in_core=already_in_core))

    db.conn.commit()
    return DeckBuildResult(deck_name, created, skipped, intentional, report_rows)


def write_deck_build_report(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "lemma",
        "normalized_lemma",
        "deck_name",
        "rank",
        "frequency",
        "core_band",
        "already_in_core",
        "action",
        "reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_intentional_duplicates_csv(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    result: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lemma = (row.get("normalized_lemma") or row.get("lemma") or "").strip()
            desc = (row.get("deck_description") or row.get("description") or "").strip()
            if lemma:
                result[lemma] = desc or "Duplicazione intenzionale documentata"
    return result


def _report(
    row: RankedLemmaRow,
    deck_name: str,
    action: str,
    reason: str,
    *,
    already_in_core: bool = False,
) -> dict[str, object]:
    return {
        "lemma": row.lemma,
        "normalized_lemma": row.normalized_lemma,
        "deck_name": deck_name,
        "rank": row.rank,
        "frequency": row.frequency,
        "core_band": row.core_band,
        "already_in_core": already_in_core,
        "action": action,
        "reason": reason,
    }
