from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable

from nlp_deck_manager.models import TextUnit


class BaseReader(ABC):
    source_type: str = "unknown"

    @abstractmethod
    def read(self, path: Path) -> Iterable[TextUnit]:
        raise NotImplementedError
