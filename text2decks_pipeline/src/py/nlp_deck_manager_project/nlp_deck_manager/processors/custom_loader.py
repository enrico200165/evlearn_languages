from __future__ import annotations

import importlib.util
from pathlib import Path

from nlp_deck_manager.processors.base import NoteProcessor


def load_processor_from_file(path: Path, class_name: str = "CustomProcessor") -> NoteProcessor:
    path = path.resolve()
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Impossibile caricare processor custom: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cls = getattr(module, class_name)
    processor = cls()
    if not isinstance(processor, NoteProcessor):
        raise TypeError(f"{class_name} deve estendere NoteProcessor")
    return processor
