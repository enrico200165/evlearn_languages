from __future__ import annotations

from nlp_deck_manager.models import Note, ProcessingContext, ProcessingResult
from nlp_deck_manager.processors.base import NoteProcessor


class TranslationPlaceholderProcessor(NoteProcessor):
    """Placeholder per traduzioni.

    Sostituire o estendere questa classe con chiamate a traduttori, dizionari o AI.
    """

    name = "translation_placeholder"

    def process(self, note: Note, context: ProcessingContext) -> ProcessingResult:
        if note.fields.get("translation_it"):
            return ProcessingResult(changed=False)
        return ProcessingResult(
            changed=True,
            updated_fields={"translation_it": "TODO: traduzione italiana verificata"},
            warnings=["Traduzione placeholder: completare con processor custom o revisione manuale."],
        )
