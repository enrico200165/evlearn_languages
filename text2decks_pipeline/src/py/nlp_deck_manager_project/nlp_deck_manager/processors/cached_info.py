from __future__ import annotations

import json
import re

from nlp_deck_manager.models import Note, ProcessingContext, ProcessingResult
from nlp_deck_manager.processors.base import NoteProcessor


_SAFE_FIELD_RE = re.compile(r"[^0-9A-Za-z_]+")


class CachedLemmaInfoProcessor(NoteProcessor):
    """Carica informazioni persistenti da info_lemma prima di chiamare servizi esterni.

    Il processor non chiama API. Legge dal Reference DB le informazioni già
    memorizzate per il lemma della note e le copia nei campi della note.

    Può essere usato prima dei processor che chiamano traduttori, dizionari o AI.
    Se un campo è già valorizzato, non viene sovrascritto.
    """

    name = "cached_lemma_info"

    DEFAULT_INFO_NAMES = [
        "traduzione",
        "flessione",
        "coniugazione",
        "frasi esempio",
        "articolo",
        "genere",
        "plurale",
        "lettura",
        "furigana",
        "jlpt",
    ]

    FIELD_MAP = {
        "traduzione": "translation_it",
        "flessione": "declension_json",
        "coniugazione": "conjugation_json",
        "frasi esempio": "examples_json",
        "articolo": "article",
        "genere": "gender",
        "plurale": "plural",
        "lettura": "kana",
        "furigana": "furigana",
        "jlpt": "jlpt_level",
    }

    def __init__(self, info_names: list[str] | None = None, *, origin: str | None = None) -> None:
        self.info_names = info_names or list(self.DEFAULT_INFO_NAMES)
        self.origin = origin

    def process(self, note: Note, context: ProcessingContext) -> ProcessingResult:
        db = context.reference_db
        if db is None or note.vocab_id is None:
            return ProcessingResult(changed=False)

        updated: dict[str, object] = {}
        cached_summary: dict[str, dict[str, str]] = dict(note.fields.get("cached_lemma_info") or {})

        for info_name in self.info_names:
            cached = db.get_lemma_info(
                vocab_id=note.vocab_id,
                nome_informazione=info_name,
                origine=self.origin,
            )
            if cached is None:
                continue

            cached_summary[info_name] = {
                "origine": cached.origine,
                "tstamp": cached.tstamp,
            }

            field_name = self.FIELD_MAP.get(info_name) or f"info_{_safe_field(info_name)}"
            if not note.fields.get(field_name):
                updated[field_name] = _maybe_json(cached.informazione)

            raw_field_name = f"info_raw_{_safe_field(info_name)}"
            if not note.fields.get(raw_field_name):
                updated[raw_field_name] = cached.informazione

        if cached_summary:
            updated["cached_lemma_info"] = cached_summary

        return ProcessingResult(changed=bool(updated), updated_fields=updated)


def _safe_field(value: str) -> str:
    cleaned = _SAFE_FIELD_RE.sub("_", value.strip().lower()).strip("_")
    return cleaned or "lemma_info"


def _maybe_json(value: str):
    stripped = value.strip()
    if not stripped:
        return value
    if stripped[0] not in "[{\"":
        return value
    try:
        return json.dumps(json.loads(stripped), ensure_ascii=False, sort_keys=True)
    except Exception:
        return value
