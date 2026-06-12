from __future__ import annotations

import json

from nlp_deck_manager.models import Note, ProcessingContext, ProcessingResult
from nlp_deck_manager.processors.base import NoteProcessor


class GermanVanillaMorphologyProcessor(NoteProcessor):
    """Processor vanilla per predisporre i campi tedeschi.

    Non inventa flessioni, articoli o coniugazioni. Inserisce strutture vuote e
    placeholder espliciti che potranno essere riempiti da codice custom, AI,
    dizionari o revisione manuale.
    """

    name = "german_vanilla_morphology"

    def process(self, note: Note, context: ProcessingContext) -> ProcessingResult:
        if note.language != "de":
            return ProcessingResult(changed=False)

        fields = dict(note.fields)
        pos = (fields.get("part_of_speech") or "").lower()
        lemma = note.normalized_lemma.lower()
        is_verb = pos in {"verb", "aux", "auxiliary"} or lemma.endswith(("en", "eln", "ern"))
        updated = {}

        if "article" not in fields:
            updated["article"] = ""
        if "gender" not in fields:
            updated["gender"] = ""
        if "plural" not in fields:
            updated["plural"] = ""

        if not fields.get("declension_json") or fields.get("declension_json") == "{}":
            updated["declension_json"] = json.dumps(
                {
                    "nominativ": {"singular": "", "plural": ""},
                    "akkusativ": {"singular": "", "plural": ""},
                    "dativ": {"singular": "", "plural": ""},
                    "genitiv": {"singular": "", "plural": ""},
                    "note": "TODO: inserire flessione completa verificata con articoli",
                },
                ensure_ascii=False,
                sort_keys=True,
            )

        if not fields.get("conjugation_json") or fields.get("conjugation_json") == "{}":
            updated["conjugation_json"] = json.dumps(
                {
                    "praesens": {"ich": "", "du": "", "er_sie_es": "", "wir": "", "ihr": "", "sie_Sie": ""},
                    "praeteritum": {"ich": "", "du": "", "er_sie_es": "", "wir": "", "ihr": "", "sie_Sie": ""},
                    "perfekt": "",
                    "imperativ": {"du": "", "ihr": "", "Sie": ""},
                    "konjunktiv_II": "",
                    "partizip_II": "",
                    "note": "TODO: inserire coniugazione completa verificata",
                },
                ensure_ascii=False,
                sort_keys=True,
            )

        updated.setdefault("needs_full_inflection", not is_verb)
        updated.setdefault("needs_full_conjugation", is_verb or fields.get("needs_full_conjugation") is True)
        updated.setdefault("needs_five_colloquial_examples", True)

        if updated:
            return ProcessingResult(changed=True, updated_fields=updated)
        return ProcessingResult(changed=False)


class GermanFiveExamplesPlaceholderProcessor(NoteProcessor):
    """Predispone 5 campi per frasi colloquiali frequenti.

    Le frasi reali vanno riempite da dizionari, AI, traduttori o revisione manuale.
    """

    name = "german_five_examples_placeholder"

    def process(self, note: Note, context: ProcessingContext) -> ProcessingResult:
        if note.language != "de":
            return ProcessingResult(changed=False)
        updated = {}
        lemma = note.lemma
        examples = []
        for idx in range(1, 6):
            de_key = f"example_{idx}_de"
            it_key = f"example_{idx}_it"
            if not note.fields.get(de_key):
                updated[de_key] = f"TODO: frase colloquiale frequente {idx} con '{lemma}'"
            if not note.fields.get(it_key):
                updated[it_key] = "TODO: traduzione italiana verificata"
            examples.append({"de": updated.get(de_key, note.fields.get(de_key, "")), "it": updated.get(it_key, note.fields.get(it_key, ""))})
        updated["examples_json"] = json.dumps(examples, ensure_ascii=False)
        return ProcessingResult(changed=bool(updated), updated_fields=updated)
