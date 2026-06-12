from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

from nlp_deck_manager.models import LemmaOccurrence, TextUnit

GERMAN_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]+(?:-[A-Za-zÄÖÜäöüß]+)?")
JAPANESE_BLOCK_RE = re.compile(r"[一-龯々〆〤ぁ-んァ-ンー]+")

DEFAULT_SPACY_MODELS = {
    "de": "de_core_news_sm",
    "ja": "ja_core_news_sm",
}


@dataclass(frozen=True)
class AnalyzerConfig:
    language: str
    model_name: str | None = None
    limit_units: int | None = None
    batch_size: int = 100
    mode: str = "auto"  # auto, spacy, simple


class LemmaAnalyzer:
    def __init__(self, config: AnalyzerConfig) -> None:
        self.config = config
        self.language = config.language.lower().strip()
        self.model_name = config.model_name or DEFAULT_SPACY_MODELS.get(self.language)

    def count_lemmas(self, text_units: Iterable[TextUnit], logger=None) -> dict[str, LemmaOccurrence]:
        if self.config.mode not in {"auto", "spacy", "simple"}:
            raise ValueError("mode deve essere auto, spacy o simple")

        if self.config.mode in {"auto", "spacy"}:
            try:
                return self._count_with_spacy(text_units, logger=logger)
            except Exception as exc:
                if self.config.mode == "spacy":
                    raise
                if logger:
                    logger.warning("spaCy non disponibile o modello non caricabile: %s", exc)
                    logger.warning("Uso fallback simple. Per produzione installare spaCy e il modello della lingua.")
        return self._count_simple(text_units, logger=logger)

    def _count_with_spacy(self, text_units: Iterable[TextUnit], logger=None) -> dict[str, LemmaOccurrence]:
        if not self.model_name:
            raise RuntimeError(f"Nessun modello spaCy configurato per lingua {self.language}")
        import spacy

        if logger:
            logger.info("Caricamento modello spaCy: %s", self.model_name)
        nlp = spacy.load(self.model_name, disable=["ner"])

        counts: Counter[str] = Counter()
        display_lemma: dict[str, str] = {}
        pos_counts: dict[str, Counter[str]] = defaultdict(Counter)
        processed = 0

        for doc in nlp.pipe((unit.text for unit in text_units), batch_size=self.config.batch_size):
            processed += 1
            if self.config.limit_units is not None and processed > self.config.limit_units:
                break
            for token in doc:
                if not self._accept_spacy_token(token):
                    continue
                lemma = token.lemma_ or token.text
                normalized = self._normalize_lemma(lemma)
                if not normalized:
                    continue
                counts[normalized] += 1
                display_lemma.setdefault(normalized, lemma.strip())
                pos = (token.pos_ or "unknown").lower()
                pos_counts[normalized][pos] += 1

            if logger and processed % 2500 == 0:
                logger.info("Unità testuali elaborate: %s", processed)

        if logger:
            logger.info("Unità testuali elaborate: %s", processed)
            logger.info("Lemmi distinti: %s", len(counts))
        return {
            normalized: LemmaOccurrence(
                lemma=display_lemma.get(normalized, normalized),
                normalized_lemma=normalized,
                frequency=int(freq),
                language=self.language,
                part_of_speech=pos_counts[normalized].most_common(1)[0][0] if pos_counts[normalized] else None,
            )
            for normalized, freq in counts.items()
        }

    def _count_simple(self, text_units: Iterable[TextUnit], logger=None) -> dict[str, LemmaOccurrence]:
        counts: Counter[str] = Counter()
        display: dict[str, str] = {}
        processed = 0
        for unit in text_units:
            processed += 1
            if self.config.limit_units is not None and processed > self.config.limit_units:
                break
            if self.language == "ja":
                tokens = JAPANESE_BLOCK_RE.findall(unit.text)
            else:
                tokens = GERMAN_WORD_RE.findall(unit.text)
            for token in tokens:
                normalized = self._normalize_lemma(token)
                if not normalized:
                    continue
                counts[normalized] += 1
                display.setdefault(normalized, normalized if self.language == "de" else token.strip())
        if logger:
            logger.info("Fallback simple: unità testuali elaborate: %s", processed)
            logger.info("Fallback simple: lemmi distinti: %s", len(counts))
        return {
            normalized: LemmaOccurrence(
                lemma=display.get(normalized, normalized),
                normalized_lemma=normalized,
                frequency=int(freq),
                language=self.language,
                part_of_speech=None,
            )
            for normalized, freq in counts.items()
        }

    def _accept_spacy_token(self, token) -> bool:
        if token.is_space or token.is_punct or token.like_num:
            return False
        text = token.text.strip()
        if not text:
            return False
        if self.language == "de":
            return bool(GERMAN_WORD_RE.fullmatch(text))
        if self.language == "ja":
            return not token.is_stop and bool(JAPANESE_BLOCK_RE.search(text))
        return True

    def _normalize_lemma(self, lemma: str) -> str:
        lemma = lemma.strip()
        if not lemma:
            return ""
        if self.language == "de":
            return lemma.lower()
        return lemma
