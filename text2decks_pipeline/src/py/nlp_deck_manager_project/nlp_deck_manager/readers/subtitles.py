from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from nlp_deck_manager.models import TextUnit
from nlp_deck_manager.readers.base import BaseReader
from nlp_deck_manager.readers.normalization import normalize_text_line

_SRT_TS_RE = re.compile(r"^\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s+-->\s+\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}")
_VTT_TS_RE = re.compile(r"^(?:\d{1,2}:)?\d{2}:\d{2}\.\d{1,3}\s+-->\s+(?:\d{1,2}:)?\d{2}:\d{2}\.\d{1,3}")
_ASS_DIALOGUE_RE = re.compile(r"^Dialogue:\s*(.*)$", re.IGNORECASE)


class SrtReader(BaseReader):
    source_type = "srt"

    def read(self, path: Path) -> Iterable[TextUnit]:
        with path.open("r", encoding="utf-8-sig", errors="replace") as f:
            for line_number, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line or line.isdigit() or _SRT_TS_RE.match(line):
                    continue
                text = normalize_text_line(line)
                if text:
                    yield TextUnit(text=text, source_path=path, source_type=self.source_type, line_number=line_number)


class VttReader(BaseReader):
    source_type = "vtt"

    def read(self, path: Path) -> Iterable[TextUnit]:
        with path.open("r", encoding="utf-8-sig", errors="replace") as f:
            for line_number, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line:
                    continue
                if line.upper().startswith("WEBVTT") or line.startswith("NOTE"):
                    continue
                if _VTT_TS_RE.match(line):
                    continue
                text = normalize_text_line(line)
                if text:
                    yield TextUnit(text=text, source_path=path, source_type=self.source_type, line_number=line_number)


class AssSsaReader(BaseReader):
    source_type = "ass_ssa"

    def read(self, path: Path) -> Iterable[TextUnit]:
        with path.open("r", encoding="utf-8-sig", errors="replace") as f:
            for line_number, raw in enumerate(f, start=1):
                line = raw.strip()
                match = _ASS_DIALOGUE_RE.match(line)
                if not match:
                    continue
                payload = match.group(1)
                # ASS Dialogue ha 10 campi; il testo è di norma l'ultimo.
                parts = payload.split(",", 9)
                if len(parts) < 10:
                    continue
                text = normalize_text_line(parts[9].replace(r"\N", " "))
                if text:
                    yield TextUnit(text=text, source_path=path, source_type=self.source_type, line_number=line_number)
