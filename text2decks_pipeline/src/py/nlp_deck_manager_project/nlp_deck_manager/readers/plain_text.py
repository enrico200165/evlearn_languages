from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from nlp_deck_manager.models import TextUnit
from nlp_deck_manager.readers.base import BaseReader
from nlp_deck_manager.readers.normalization import normalize_text_line


class PlainTextReader(BaseReader):
    source_type = "plain_text"

    def read(self, path: Path) -> Iterable[TextUnit]:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                # Leipzig in formato ID<TAB>frase.
                if "\t" in line:
                    first, rest = line.split("\t", 1)
                    if first.strip().isdigit():
                        line = rest
                text = normalize_text_line(line)
                if text:
                    yield TextUnit(text=text, source_path=path, source_type=self.source_type, line_number=line_number)


class CsvTextReader(BaseReader):
    source_type = "csv"

    def __init__(self, text_column: str | None = None) -> None:
        self.text_column = text_column

    def read(self, path: Path) -> Iterable[TextUnit]:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel
            reader = csv.DictReader(f, dialect=dialect)
            if not reader.fieldnames:
                return
            column = self.text_column or self._guess_text_column(reader.fieldnames)
            for line_number, row in enumerate(reader, start=2):
                text = normalize_text_line(row.get(column, "") or "")
                if text:
                    yield TextUnit(text=text, source_path=path, source_type=self.source_type, line_number=line_number)

    @staticmethod
    def _guess_text_column(fieldnames: list[str]) -> str:
        preferred = ["text", "sentence", "frase", "example", "content", "lemma"]
        lowered = {name.lower(): name for name in fieldnames}
        for key in preferred:
            if key in lowered:
                return lowered[key]
        return fieldnames[0]
