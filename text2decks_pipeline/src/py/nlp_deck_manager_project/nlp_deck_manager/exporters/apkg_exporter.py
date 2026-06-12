from __future__ import annotations

import hashlib
import json
from pathlib import Path

from nlp_deck_manager.models import Note


def stable_int_id(text: str, *, digits: int = 10) -> int:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
    return int(digest[:digits], 16)


def export_notes_to_apkg(path: Path, deck_name: str, notes: list[Note]) -> None:
    try:
        import genanki
    except ImportError as exc:
        raise RuntimeError("genanki non è installato. Installare con: python -m pip install genanki") from exc

    model = genanki.Model(
        stable_int_id("nlp_deck_manager_default_model"),
        "NLP Deck Manager Default Model",
        fields=[
            {"name": "Lemma"},
            {"name": "Language"},
            {"name": "NoteType"},
            {"name": "TranslationIt"},
            {"name": "Article"},
            {"name": "PartOfSpeech"},
            {"name": "Inflection"},
            {"name": "Conjugation"},
            {"name": "Examples"},
            {"name": "SourceRank"},
            {"name": "SourceFrequency"},
            {"name": "ExtraJson"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "<h2>{{Lemma}}</h2><div>{{Language}} - {{NoteType}}</div>",
                "afmt": """
{{FrontSide}}
<hr id=answer>
<div><b>Traduzione:</b> {{TranslationIt}}</div>
<div><b>Articolo:</b> {{Article}}</div>
<div><b>Parte del discorso:</b> {{PartOfSpeech}}</div>
<div><b>Flessione:</b><pre>{{Inflection}}</pre></div>
<div><b>Coniugazione:</b><pre>{{Conjugation}}</pre></div>
<div><b>Esempi:</b><pre>{{Examples}}</pre></div>
<div><b>Extra:</b><pre>{{ExtraJson}}</pre></div>
""",
            }
        ],
    )
    deck = genanki.Deck(stable_int_id(deck_name), deck_name)
    for note in notes:
        fields = note.fields
        genanki_note = genanki.Note(
            model=model,
            fields=[
                note.lemma,
                note.language,
                note.note_type,
                str(fields.get("translation_it", "")),
                str(fields.get("article", "")),
                str(fields.get("part_of_speech", "")),
                str(fields.get("declension_json", "")),
                str(fields.get("conjugation_json", "")),
                str(fields.get("examples_json", "")),
                str(fields.get("source_rank", "")),
                str(fields.get("source_frequency", "")),
                json.dumps(fields, ensure_ascii=False, sort_keys=True),
            ],
            tags=[_safe_tag(tag) for tag in note.tags if tag],
            guid=genanki.guid_for(deck_name, note.language, note.normalized_lemma, note.note_type),
        )
        deck.add_note(genanki_note)
    path.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(path))


def _safe_tag(tag: str) -> str:
    return tag.replace(" ", "_").replace(",", "_")
