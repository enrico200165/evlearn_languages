from __future__ import annotations

from enum import Enum
from pathlib import Path


class InputType(str, Enum):
    LEIPZIG_TAR = "leipzig_tar"
    PLAIN_TEXT = "plain_text"
    CSV = "csv"
    SUBTITLE_SRT = "subtitle_srt"
    SUBTITLE_VTT = "subtitle_vtt"
    SUBTITLE_ASS = "subtitle_ass"
    SUBTITLE_SSA = "subtitle_ssa"
    UNKNOWN_TEXT = "unknown_text"


def detect_input_type(path: Path) -> InputType:
    name = path.name.lower()
    suffix = path.suffix.lower()

    if name.endswith(".tar.gz"):
        return InputType.LEIPZIG_TAR
    if suffix == ".txt":
        return InputType.PLAIN_TEXT
    if suffix == ".csv":
        return InputType.CSV
    if suffix == ".srt":
        return InputType.SUBTITLE_SRT
    if suffix == ".vtt":
        return InputType.SUBTITLE_VTT
    if suffix == ".ass":
        return InputType.SUBTITLE_ASS
    if suffix == ".ssa":
        return InputType.SUBTITLE_SSA
    return InputType.UNKNOWN_TEXT


SUPPORTED_SUFFIXES = {".txt", ".csv", ".srt", ".vtt", ".ass", ".ssa"}


def is_supported_path(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".tar.gz") or path.suffix.lower() in SUPPORTED_SUFFIXES
