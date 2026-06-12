from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from nlp_deck_manager.models import LemmaOccurrence, RankedLemmaRow
from nlp_deck_manager.reference_db.repository import LemmaImportResult

CORE_FIELDNAMES = ["rank", "lemma", "normalized_lemma", "frequency", "core_band", "language", "part_of_speech"]
FREQ_FIELDNAMES = ["lemma", "normalized_lemma", "frequency", "language", "part_of_speech"]
IMPORT_REPORT_FIELDNAMES = ["lemma", "normalized_lemma", "language", "frequency", "action", "vocab_id"]
OVERLAP_REPORT_FIELDNAMES = ["lemma", "normalized_lemma", "bands"]


def write_csv_dicts(path: Path, fieldnames: list[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_full_frequencies(path: Path, occurrences: dict[str, LemmaOccurrence]) -> None:
    rows = (
        {
            "lemma": occ.lemma,
            "normalized_lemma": occ.normalized_lemma,
            "frequency": int(occ.frequency),
            "language": occ.language,
            "part_of_speech": occ.part_of_speech,
        }
        for occ in sorted(occurrences.values(), key=lambda item: (-item.frequency, item.normalized_lemma))
    )
    write_csv_dicts(path, FREQ_FIELDNAMES, rows)


def write_ranked_rows(path: Path, rows: list[RankedLemmaRow]) -> None:
    write_csv_dicts(path, CORE_FIELDNAMES, (row.as_dict() for row in rows))


def write_reference_import_report(path: Path, results: list[LemmaImportResult]) -> None:
    write_csv_dicts(
        path,
        IMPORT_REPORT_FIELDNAMES,
        (
            {
                "lemma": item.lemma,
                "normalized_lemma": item.normalized_lemma,
                "language": item.language,
                "frequency": item.frequency,
                "action": item.action,
                "vocab_id": item.vocab_id,
            }
            for item in results
        ),
    )


def write_core_exports(
    output_dir: Path,
    rows: list[RankedLemmaRow],
    *,
    language: str,
    max_rank: int = 5000,
    band_size: int = 1000,
    write_explicit_band_names: bool = True,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_ranked_rows(output_dir / f"core_0001_{max_rank:04d}_{language}.csv", rows)
    band_count = (max_rank + band_size - 1) // band_size
    for band_number in range(1, band_count + 1):
        start = ((band_number - 1) * band_size) + 1
        end = band_number * band_size
        band_rows = [row for row in rows if start <= row.rank <= end]
        if not band_rows:
            continue
        write_ranked_rows(output_dir / f"core_{end}_{language}.csv", band_rows)
        if write_explicit_band_names:
            write_ranked_rows(output_dir / f"core_{start:04d}_{end:04d}_{language}.csv", band_rows)


def write_core_overlap_report(path: Path, rows: list[RankedLemmaRow]) -> None:
    bands_by_lemma: dict[str, set[str]] = {}
    display: dict[str, str] = {}
    for row in rows:
        bands_by_lemma.setdefault(row.normalized_lemma, set()).add(row.core_band)
        display.setdefault(row.normalized_lemma, row.lemma)
    report = [
        {"lemma": display[norm], "normalized_lemma": norm, "bands": ";".join(sorted(bands))}
        for norm, bands in sorted(bands_by_lemma.items())
        if len(bands) > 1
    ]
    write_csv_dicts(path, OVERLAP_REPORT_FIELDNAMES, report)
