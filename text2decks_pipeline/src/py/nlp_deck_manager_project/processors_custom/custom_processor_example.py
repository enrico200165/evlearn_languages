from __future__ import annotations

from nlp_deck_manager.models import Note, ProcessingContext, ProcessingResult
from nlp_deck_manager.processors.base import NoteProcessor


class CustomProcessor(NoteProcessor):
    """Esempio di processor custom.

    Copiare questo file, rinominarlo e modificare il metodo process().
    Qui si possono chiamare dizionari, traduttori, API AI o strumenti locali.
    """

    name = "custom_processor_example"

    def process(self, note: Note, context: ProcessingContext) -> ProcessingResult:
        updated = {}

        # Esempio: impostare un campo solo se è vuoto.
        if not note.fields.get("custom_note"):
            updated["custom_note"] = "TODO: campo compilato da processor custom"

        return ProcessingResult(
            changed=bool(updated),
            updated_fields=updated,
            warnings=[] if updated else ["Nessuna modifica applicata"],
        )
