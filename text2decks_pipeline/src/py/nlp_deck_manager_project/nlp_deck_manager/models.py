from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TextUnit:
    """Unità testuale normalizzata prodotta dai reader."""

    text: str
    source_path: Path | None = None
    source_type: str | None = None
    line_number: int | None = None


@dataclass(frozen=True)
class LemmaOccurrence:
    """Occorrenza aggregata di un lemma dopo l'analisi NLP."""

    lemma: str
    normalized_lemma: str
    frequency: int
    language: str
    part_of_speech: str | None = None


@dataclass(frozen=True)
class RankedLemmaRow:
    rank: int
    lemma: str
    normalized_lemma: str
    frequency: int
    core_band: str
    language: str
    part_of_speech: str | None = None

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "rank": self.rank,
            "lemma": self.lemma,
            "normalized_lemma": self.normalized_lemma,
            "frequency": self.frequency,
            "core_band": self.core_band,
            "language": self.language,
            "part_of_speech": self.part_of_speech,
        }


@dataclass
class Note:
    """Rappresentazione flessibile di una note linguistica.

    fields contiene i campi specifici del modello di note.
    Non viene inventata conoscenza linguistica non verificata: i processor vanilla
    inseriscono placeholder espliciti quando mancano dati affidabili.
    """

    language: str
    lemma: str
    normalized_lemma: str
    deck_name: str
    note_type: str = "vocabulary"
    fields: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    status: str = "draft"
    vocab_id: int | None = None
    deck_id: int | None = None
    note_id: int | None = None


@dataclass
class LemmaInfo:
    """Informazione persistente associata a un lemma.

    Serve come cache applicativa per evitare chiamate ripetute a API,
    dizionari online, traduttori o servizi AI.
    """

    vocab_id: int
    nome_informazione: str
    informazione: str
    origine: str
    tstamp: str


@dataclass
class ProcessingContext:
    """Contesto passato ai processor custom."""

    language: str
    deck_name: str | None = None
    reference_db: Any | None = None
    logger: Any | None = None
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Risultato di un processor applicato a una note."""

    changed: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    updated_fields: dict[str, Any] = field(default_factory=dict)
