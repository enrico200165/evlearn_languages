from __future__ import annotations

import io
import tarfile
from pathlib import Path
from typing import Iterable

from nlp_deck_manager.models import TextUnit
from nlp_deck_manager.readers.base import BaseReader
from nlp_deck_manager.readers.normalization import normalize_text_line


class LeipzigTarReader(BaseReader):
    source_type = "leipzig_tar"

    def read(self, path: Path) -> Iterable[TextUnit]:
        with tarfile.open(path, mode="r:gz") as tar:
            members = [m for m in tar.getmembers() if m.name.endswith("sentences.txt")]
            if not members:
                raise RuntimeError("Nessun file sentences.txt trovato nell'archivio Leipzig.")
            member = members[0]
            extracted = tar.extractfile(member)
            if extracted is None:
                raise RuntimeError(f"Impossibile estrarre {member.name}")
            stream = io.TextIOWrapper(extracted, encoding="utf-8", errors="replace")
            for line_number, line in enumerate(stream, start=1):
                line = line.strip()
                if not line:
                    continue
                if "\t" in line:
                    _, line = line.split("\t", 1)
                text = normalize_text_line(line)
                if text:
                    yield TextUnit(text=text, source_path=path, source_type=self.source_type, line_number=line_number)
