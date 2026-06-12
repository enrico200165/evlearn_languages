from __future__ import annotations

from nlp_deck_manager.models import LemmaOccurrence, RankedLemmaRow


def build_ranked_rows(
    occurrences: dict[str, LemmaOccurrence],
    *,
    language: str,
    max_rank: int = 5000,
    band_size: int = 1000,
) -> list[RankedLemmaRow]:
    items = sorted(occurrences.values(), key=lambda item: (-item.frequency, item.normalized_lemma))[:max_rank]
    rows: list[RankedLemmaRow] = []
    for rank, occ in enumerate(items, start=1):
        band_number = ((rank - 1) // band_size) + 1
        band_end = band_number * band_size
        rows.append(
            RankedLemmaRow(
                rank=rank,
                lemma=occ.lemma,
                normalized_lemma=occ.normalized_lemma,
                frequency=int(occ.frequency),
                core_band=f"Core-{band_end}",
                language=language,
                part_of_speech=occ.part_of_speech,
            )
        )
    validate_no_core_overlap(rows)
    return rows


def rows_for_band(rows: list[RankedLemmaRow], *, band_number: int, band_size: int = 1000) -> list[RankedLemmaRow]:
    start = ((band_number - 1) * band_size) + 1
    end = band_number * band_size
    return [row for row in rows if start <= row.rank <= end]


def validate_no_core_overlap(rows: list[RankedLemmaRow]) -> None:
    seen: dict[str, str] = {}
    duplicates: list[tuple[str, str, str]] = []
    for row in rows:
        previous = seen.get(row.normalized_lemma)
        if previous is not None and previous != row.core_band:
            duplicates.append((row.normalized_lemma, previous, row.core_band))
        seen[row.normalized_lemma] = row.core_band
    if duplicates:
        sample = "; ".join(f"{lemma}: {a}/{b}" for lemma, a, b in duplicates[:10])
        raise RuntimeError(f"Overlap tra bande Core rilevato: {sample}")
