from __future__ import annotations

import html
import re
import unicodedata

_TAG_RE = re.compile(r"<[^>]+>")
_SPACES_RE = re.compile(r"\s+")
_ASS_INLINE_RE = re.compile(r"\{\\[^}]+\}")


def normalize_text_line(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = html.unescape(text)
    text = _ASS_INLINE_RE.sub("", text)
    text = _TAG_RE.sub("", text)
    text = text.replace("\ufeff", "")
    text = _SPACES_RE.sub(" ", text)
    return text.strip()
