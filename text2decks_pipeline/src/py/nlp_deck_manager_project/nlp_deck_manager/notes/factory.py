from __future__ import annotations

from nlp_deck_manager.models import Note, RankedLemmaRow


def make_note_from_ranked_row(row: RankedLemmaRow, *, deck_name: str) -> Note:
    base_fields = {
        "lemma": row.lemma,
        "normalized_lemma": row.normalized_lemma,
        "language": row.language,
        "source_rank": row.rank,
        "source_frequency": row.frequency,
        "source_core_band": row.core_band,
        "part_of_speech": row.part_of_speech or "",
        "translation_it": "",
        "notes": "",
    }
    if row.language == "de":
        base_fields.update(_german_vanilla_fields(row))
    elif row.language == "ja":
        base_fields.update(_japanese_vanilla_fields(row))
    else:
        base_fields.update({"examples_json": "[]"})
    return Note(
        language=row.language,
        lemma=row.lemma,
        normalized_lemma=row.normalized_lemma,
        deck_name=deck_name,
        note_type="vocabulary",
        fields=base_fields,
        tags=[row.language, row.core_band.lower()],
        status="draft",
    )


def _german_vanilla_fields(row: RankedLemmaRow) -> dict[str, object]:
    pos = (row.part_of_speech or "").lower()
    is_verb = pos in {"verb", "aux", "auxiliary"}
    fields: dict[str, object] = {
        "article": "",
        "gender": "",
        "plural": "",
        "declension_json": "{}",
        "conjugation_json": "{}",
        "examples_json": "[]",
        "example_1_de": "",
        "example_1_it": "",
        "example_2_de": "",
        "example_2_it": "",
        "example_3_de": "",
        "example_3_it": "",
        "example_4_de": "",
        "example_4_it": "",
        "example_5_de": "",
        "example_5_it": "",
        "needs_full_inflection": not is_verb,
        "needs_full_conjugation": is_verb,
        "needs_five_colloquial_examples": True,
    }
    return fields


def _japanese_vanilla_fields(row: RankedLemmaRow) -> dict[str, object]:
    return {
        "kanji": row.lemma,
        "kana": "",
        "romaji": "",
        "furigana": "",
        "jlpt_level": "",
        "examples_json": "[]",
        "example_1_ja": "",
        "example_1_it": "",
        "example_2_ja": "",
        "example_2_it": "",
        "example_3_ja": "",
        "example_3_it": "",
        "example_4_ja": "",
        "example_4_it": "",
        "example_5_ja": "",
        "example_5_it": "",
    }
