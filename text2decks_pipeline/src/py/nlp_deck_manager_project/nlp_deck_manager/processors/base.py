from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable

from nlp_deck_manager.models import Note, ProcessingContext, ProcessingResult


class NoteProcessor(ABC):
    """Interfaccia stabile per codice custom di elaborazione note."""

    name: str = "base"

    @abstractmethod
    def process(self, note: Note, context: ProcessingContext) -> ProcessingResult:
        raise NotImplementedError


@dataclass
class ProcessorPipeline:
    processors: list[NoteProcessor] = field(default_factory=list)

    def process_note(self, note: Note, context: ProcessingContext) -> list[tuple[str, ProcessingResult]]:
        results: list[tuple[str, ProcessingResult]] = []
        for processor in self.processors:
            result = processor.process(note, context)
            for key, value in result.updated_fields.items():
                note.fields[key] = value
            results.append((processor.name, result))
        return results

    def process_notes(self, notes: Iterable[Note], context: ProcessingContext) -> list[Note]:
        output = []
        for note in notes:
            self.process_note(note, context)
            output.append(note)
        return output
