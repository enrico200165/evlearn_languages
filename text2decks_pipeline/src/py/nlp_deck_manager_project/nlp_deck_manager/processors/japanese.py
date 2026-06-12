from __future__ import annotations

from nlp_deck_manager.models import Note, ProcessingContext, ProcessingResult
from nlp_deck_manager.processors.base import NoteProcessor


class JapaneseVanillaFieldsProcessor(NoteProcessor):
    """Processor vanilla per predisporre campi giapponesi senza inventare dati."""

    name = "japanese_vanilla_fields"

    def process(self, note: Note, context: ProcessingContext) -> ProcessingResult:
        if note.language != "ja":
            return ProcessingResult(changed=False)
        defaults = {
            "kanji": note.lemma,
            "kana": "",
            "romaji": "",
            "furigana": "",
            "jlpt_level": "",
            "needs_reading": True,
            "needs_five_colloquial_examples": True,
        }
        updated = {key: value for key, value in defaults.items() if key not in note.fields}
        for idx in range(1, 6):
            updated.setdefault(f"example_{idx}_ja", note.fields.get(f"example_{idx}_ja") or f"TODO: frase colloquiale frequente {idx} con '{note.lemma}'")
            updated.setdefault(f"example_{idx}_it", note.fields.get(f"example_{idx}_it") or "TODO: traduzione italiana verificata")
        return ProcessingResult(changed=bool(updated), updated_fields=updated)
