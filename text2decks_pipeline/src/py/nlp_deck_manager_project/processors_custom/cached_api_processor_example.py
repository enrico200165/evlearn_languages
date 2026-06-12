from nlp_deck_manager.models import Note, ProcessingContext, ProcessingResult
from nlp_deck_manager.processors.base import NoteProcessor


class CustomProcessor(NoteProcessor):
    """Esempio di processor custom con cache info_lemma.

    Sostituire fake_api_call() con una chiamata reale a dizionario, traduttore o AI.
    Prima controlla info_lemma; se la risposta esiste, evita la chiamata.
    Se la risposta non esiste, chiama il servizio e salva il risultato nel DB.
    """

    name = "cached_api_processor_example"

    def process(self, note: Note, context: ProcessingContext) -> ProcessingResult:
        db = context.reference_db
        if db is None or note.vocab_id is None:
            return ProcessingResult(changed=False, warnings=["Reference DB o vocab_id non disponibile"])

        info_name = "frasi esempio"
        origin = "fake_api_example"

        cached = db.get_lemma_info(
            vocab_id=note.vocab_id,
            nome_informazione=info_name,
            origine=origin,
        )

        if cached is not None:
            return ProcessingResult(
                changed=True,
                updated_fields={
                    "examples_json": cached.informazione,
                    "examples_source": f"cache:{cached.origine}:{cached.tstamp}",
                },
            )

        api_result = fake_api_call(note.lemma)
        db.upsert_lemma_info(
            vocab_id=note.vocab_id,
            nome_informazione=info_name,
            informazione=api_result,
            origine=origin,
        )

        return ProcessingResult(
            changed=True,
            updated_fields={
                "examples_json": api_result,
                "examples_source": f"api:{origin}",
            },
            warnings=["Esempio vanilla: sostituire fake_api_call con una chiamata reale"],
        )


def fake_api_call(lemma: str) -> str:
    return (
        '[{"de": "TODO: frase 1 con ' + lemma + '", "it": "TODO"}, '
        '{"de": "TODO: frase 2 con ' + lemma + '", "it": "TODO"}]'
    )
