from __future__ import annotations

from pathlib import Path
from typing import Iterable

from nlp_deck_manager.models import TextUnit
from nlp_deck_manager.readers.detect import InputType, detect_input_type, is_supported_path
from nlp_deck_manager.readers.leipzig import LeipzigTarReader
from nlp_deck_manager.readers.plain_text import CsvTextReader, PlainTextReader
from nlp_deck_manager.readers.subtitles import AssSsaReader, SrtReader, VttReader


def reader_for_path(path: Path):
    input_type = detect_input_type(path)
    if input_type == InputType.LEIPZIG_TAR:
        return LeipzigTarReader()
    if input_type == InputType.CSV:
        return CsvTextReader()
    if input_type in (InputType.PLAIN_TEXT, InputType.UNKNOWN_TEXT):
        return PlainTextReader()
    if input_type == InputType.SUBTITLE_SRT:
        return SrtReader()
    if input_type == InputType.SUBTITLE_VTT:
        return VttReader()
    if input_type in (InputType.SUBTITLE_ASS, InputType.SUBTITLE_SSA):
        return AssSsaReader()
    raise ValueError(f"Formato non supportato: {path}")


def iter_text_units_from_path(path: Path) -> Iterable[TextUnit]:
    path = path.resolve()
    if path.is_dir():
        for item in sorted(path.rglob("*")):
            if item.is_file() and is_supported_path(item):
                yield from reader_for_path(item).read(item)
        return
    yield from reader_for_path(path).read(path)
