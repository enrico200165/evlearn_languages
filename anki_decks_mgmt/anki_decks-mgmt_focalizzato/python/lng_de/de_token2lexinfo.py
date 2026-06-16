#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
de_token2lexinfo.py

Scopo
-----
Modulo linguistico puro per la lingua tedesca.

Il modulo NON contiene codice di persistenza, NON scrive su SQLite e NON genera
carte Anki. Il suo compito è ricevere una parola tedesca e restituire una
struttura dati articolata, serializzabile, contenente le informazioni linguistiche
necessarie per popolare un reference database esterno.

Funzione top
------------
    build_de_lexical_reference(word)

Input:
    una parola o forma tedesca.

Output:
    un oggetto LexicalReferenceRecord con:
    - forma originale;
    - forma normalizzata;
    - lemma principale;
    - lemmi alternativi;
    - parte del discorso stimata;
    - famiglia lessicale, quando ricavabile;
    - informazioni morfologiche comuni;
    - contenuto specifico per parte del discorso;
    - 5 frasi di esempio semplici;
    - fonti usate;
    - warning e confidence.

Fonti tecniche
--------------
1. UniMorph German come fonte principale per lemma e forme flesse.
2. spaCy come fallback opzionale per la lemmatizzazione.
3. Wiktionary tedesco come fonte opzionale per genere e dati nominali.

Architettura
------------
Il codice di memorizzazione nel database deve stare in un altro modulo.
Questo file produce solo strutture dati linguistiche.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal

# =============================================================================
# DESIGN NOTE
# =============================================================================
# Questo modulo deve rimanere un componente linguistico puro.
# Non deve conoscere lo schema SQLite, non deve aprire connessioni database e
# non deve generare campi Anki. La funzione top costruisce un oggetto dati
# ricco e serializzabile; il salvataggio e la trasformazione didattica devono
# restare responsabilità di moduli separati. Questa separazione permette di
# testare la qualità linguistica indipendentemente dalla persistenza e dagli
# usi didattici successivi.


DEFAULT_CACHE_DIR = Path("./lexical_cache")

# UniMorph è usato come fonte morfologica locale/cache-friendly.
# La prima esecuzione può scaricare il file tedesco; le esecuzioni successive
# lavorano sulla copia in cache, evitando query ripetute e rendendo il modulo
# adatto a popolamenti batch del reference database.
UNIMORPH_DEU_URL = "https://raw.githubusercontent.com/unimorph/deu/master/deu"

# Wiktionary viene usato solo come fonte ausiliaria, soprattutto per dati
# nominali che UniMorph non rappresenta sempre in modo direttamente comodo
# per il reference database, come genere e forme con articolo.
# Il parser è volutamente prudente: se l'informazione non viene riconosciuta
# in modo affidabile, viene lasciata mancante e segnalata nei warnings.
DE_WIKTIONARY_API = "https://de.wiktionary.org/w/api.php"

SUBSTANTIVE_POS_HINTS = {"N", "NOUN", "SUBST", "SUBSTANTIV"}
VERB_POS_HINTS = {"V", "VERB", "VERBFIN", "VERBINF"}
ADJECTIVE_POS_HINTS = {"ADJ", "ADJECTIVE", "ADJEKTIV"}

Gender = Literal["m", "f", "n"]
Number = Literal["sg", "pl"]
Case = Literal["nom", "acc", "dat", "gen"]
ArticleType = Literal["definite", "indefinite"]


DEFINITE_ARTICLES: dict[tuple[Gender, Number, Case], str] = {
    ("m", "sg", "nom"): "der",
    ("m", "sg", "acc"): "den",
    ("m", "sg", "dat"): "dem",
    ("m", "sg", "gen"): "des",
    ("f", "sg", "nom"): "die",
    ("f", "sg", "acc"): "die",
    ("f", "sg", "dat"): "der",
    ("f", "sg", "gen"): "der",
    ("n", "sg", "nom"): "das",
    ("n", "sg", "acc"): "das",
    ("n", "sg", "dat"): "dem",
    ("n", "sg", "gen"): "des",
    ("m", "pl", "nom"): "die",
    ("m", "pl", "acc"): "die",
    ("m", "pl", "dat"): "den",
    ("m", "pl", "gen"): "der",
    ("f", "pl", "nom"): "die",
    ("f", "pl", "acc"): "die",
    ("f", "pl", "dat"): "den",
    ("f", "pl", "gen"): "der",
    ("n", "pl", "nom"): "die",
    ("n", "pl", "acc"): "die",
    ("n", "pl", "dat"): "den",
    ("n", "pl", "gen"): "der",
}

INDEFINITE_ARTICLES: dict[tuple[Gender, Number, Case], str | None] = {
    ("m", "sg", "nom"): "ein",
    ("m", "sg", "acc"): "einen",
    ("m", "sg", "dat"): "einem",
    ("m", "sg", "gen"): "eines",
    ("f", "sg", "nom"): "eine",
    ("f", "sg", "acc"): "eine",
    ("f", "sg", "dat"): "einer",
    ("f", "sg", "gen"): "einer",
    ("n", "sg", "nom"): "ein",
    ("n", "sg", "acc"): "ein",
    ("n", "sg", "dat"): "einem",
    ("n", "sg", "gen"): "eines",
    ("m", "pl", "nom"): None,
    ("m", "pl", "acc"): None,
    ("m", "pl", "dat"): None,
    ("m", "pl", "gen"): None,
    ("f", "pl", "nom"): None,
    ("f", "pl", "acc"): None,
    ("f", "pl", "dat"): None,
    ("f", "pl", "gen"): None,
    ("n", "pl", "nom"): None,
    ("n", "pl", "acc"): None,
    ("n", "pl", "dat"): None,
    ("n", "pl", "gen"): None,
}


@dataclass(frozen=True)
class UniMorphEntry:
    """Una riga UniMorph: lemma, forma flessa, feature morfologiche."""

    lemma: str
    form: str
    features: tuple[str, ...]


@dataclass
class UniMorphIndex:
    """Indici rapidi per lookup per forma e per lemma."""

    by_form: dict[str, list[UniMorphEntry]] = field(default_factory=dict)
    by_lemma: dict[str, list[UniMorphEntry]] = field(default_factory=dict)


@dataclass
class LemmaResult:
    """Risultato di lemmatizzazione."""

    input_word: str
    lemma: str
    source: str
    alternatives: list[str] = field(default_factory=list)


@dataclass
class NounInflectionRow:
    """Forma nominale con articolo."""

    case: Case
    number: Number
    form: str
    definite_article: str | None
    indefinite_article: str | None
    with_definite_article: str | None
    with_indefinite_article: str | None


@dataclass
class MorphologyResult:
    """Risultato morfologico generale."""

    input_word: str
    lemma: str
    source: str
    entries: list[UniMorphEntry] = field(default_factory=list)
    noun_inflection: list[NounInflectionRow] = field(default_factory=list)
    verb_forms: list[UniMorphEntry] = field(default_factory=list)
    wiktionary_data: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class LexicalFamilyInfo:
    """Famiglia lessicale stimata o ricavata in modo euristico."""

    family_key: str | None = None
    base_lemma: str | None = None
    related_lemmas: list[str] = field(default_factory=list)
    derivation_notes: list[str] = field(default_factory=list)
    confidence: str = "low"


@dataclass
class LexicalReferenceRecord:
    """
    Oggetto top-level prodotto dal modulo linguistico.

    È pensato per essere consumato da un modulo esterno di persistenza, non per
    essere scritto direttamente in SQLite da questo modulo.
    """

    language: str
    input_word: str
    normalized_input: str
    lemma: str
    lemma_source: str
    lemma_alternatives: list[str]
    pos: str | None
    pos_candidates: list[str]
    lexical_family: LexicalFamilyInfo
    common: dict
    pos_specific: dict
    example_sentences: list[str]
    sources: list[str]
    warnings: list[str]
    confidence: str


def normalize_word(value: str) -> str:
    """Normalizzare una parola per lookup semplice."""

    return value.strip()


def cache_path_for_unimorph(cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    """Percorso locale del dataset UniMorph tedesco."""

    return cache_dir / "unimorph_deu.tsv"


def download_unimorph_deu(
    cache_dir: Path = DEFAULT_CACHE_DIR,
    force: bool = False,
    timeout: int = 120
) -> Path:
    """Scaricare il dataset UniMorph tedesco in cache locale."""

    cache_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    destination = cache_path_for_unimorph(cache_dir)

    if destination.exists() and not force:
        return destination

    with urllib.request.urlopen(UNIMORPH_DEU_URL, timeout=timeout) as response:
        data = response.read()

    destination.write_bytes(data)

    return destination


def parse_unimorph_line(line: str) -> UniMorphEntry | None:
    """Convertire una riga UniMorph in UniMorphEntry."""

    line = line.strip()

    if not line or line.startswith("#"):
        return None

    parts = line.split("\t")

    if len(parts) < 3:
        return None

    lemma, form, features_text = parts[0], parts[1], parts[2]

    features = tuple(
        item.strip()
        for item in features_text.split(";")
        if item.strip()
    )

    return UniMorphEntry(
        lemma=lemma,
        form=form,
        features=features
    )


def load_unimorph_index(
    cache_dir: Path = DEFAULT_CACHE_DIR,
    allow_download: bool = True
) -> UniMorphIndex:
    """Caricare UniMorph German e costruire indici per forma e lemma."""

    path = cache_path_for_unimorph(cache_dir)

    if not path.exists():
        if not allow_download:
            raise FileNotFoundError(
                f"Dataset UniMorph non trovato: {path}"
            )
        download_unimorph_deu(cache_dir=cache_dir)

    index = UniMorphIndex()

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            entry = parse_unimorph_line(line)

            if entry is None:
                continue

            index.by_form.setdefault(entry.form, []).append(entry)
            index.by_lemma.setdefault(entry.lemma, []).append(entry)

    return index


def lemmatize_with_spacy(word: str, model_name: str = "de_core_news_sm") -> str | None:
    """Lemmatizzare con spaCy, se installato e configurato."""

    try:
        import spacy
    except ImportError:
        return None

    try:
        nlp = spacy.load(model_name, disable=["ner", "parser"])
    except Exception:
        return None

    doc = nlp(word)

    if not doc:
        return None

    lemma = doc[0].lemma_.strip()

    return lemma or None


def produce_lemma(
    word: str,
    *,
    index: UniMorphIndex | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    allow_download: bool = True,
    use_spacy_fallback: bool = True
) -> LemmaResult:
    """Produrre un lemma a partire da una parola tedesca."""

    normalized = normalize_word(word)

    if not normalized:
        return LemmaResult(
            input_word=word,
            lemma="",
            source="empty-input"
        )

    if index is None:
        try:
            index = load_unimorph_index(
                cache_dir=cache_dir,
                allow_download=allow_download
            )
        except Exception:
            index = None

    if index is not None:
        entries = index.by_form.get(normalized, [])
        if entries:
            lemmas = sorted({entry.lemma for entry in entries})
            return LemmaResult(
                input_word=word,
                lemma=lemmas[0],
                source="unimorph",
                alternatives=lemmas[1:]
            )

    if use_spacy_fallback:
        lemma = lemmatize_with_spacy(normalized)
        if lemma:
            return LemmaResult(
                input_word=word,
                lemma=lemma,
                source="spacy"
            )

    return LemmaResult(
        input_word=word,
        lemma=normalized,
        source="identity-fallback"
    )


def features_match(
    entry: UniMorphEntry,
    required_features: Iterable[str] | None
) -> bool:
    """Verificare se una riga UniMorph contiene tutte le feature richieste."""

    if not required_features:
        return True

    required = {feature.upper() for feature in required_features}
    available = {feature.upper() for feature in entry.features}

    return required.issubset(available)


def lookup_inflected_forms(
    lemma: str,
    *,
    required_features: Iterable[str] | None = None,
    index: UniMorphIndex | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    allow_download: bool = True
) -> list[UniMorphEntry]:
    """Cercare forme flesse di un lemma tramite UniMorph."""

    if index is None:
        index = load_unimorph_index(
            cache_dir=cache_dir,
            allow_download=allow_download
        )

    entries = index.by_lemma.get(lemma, [])

    return [
        entry
        for entry in entries
        if features_match(entry, required_features)
    ]


def query_de_wiktionary_wikitext(word: str, timeout: int = 30) -> str | None:
    """Scaricare il wikitext della pagina de.wiktionary.org per una parola."""

    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
        "titles": word,
    }

    url = f"{DE_WIKTIONARY_API}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    pages = payload.get("query", {}).get("pages", {})

    for page in pages.values():
        revisions = page.get("revisions", [])
        if not revisions:
            continue
        slots = revisions[0].get("slots", {})
        main = slots.get("main", {})
        content = main.get("*")
        if content:
            return content

    return None


def extract_wiktionary_noun_data(word: str) -> dict:
    """Provare a estrarre genere e alcune forme nominali dal Wiktionary tedesco."""

    wikitext = query_de_wiktionary_wikitext(word)

    if not wikitext:
        return {}

    data: dict[str, str] = {}

    gender_match = re.search(r"\|\s*Genus\s*=\s*([mfn])", wikitext)
    if gender_match:
        data["gender"] = gender_match.group(1)

    fields = {
        "nominative_singular": r"\|\s*Nominativ Singular\s*=\s*([^\n|]+)",
        "genitive_singular": r"\|\s*Genitiv Singular\s*=\s*([^\n|]+)",
        "dative_singular": r"\|\s*Dativ Singular\s*=\s*([^\n|]+)",
        "accusative_singular": r"\|\s*Akkusativ Singular\s*=\s*([^\n|]+)",
        "nominative_plural": r"\|\s*Nominativ Plural\s*=\s*([^\n|]+)",
        "genitive_plural": r"\|\s*Genitiv Plural\s*=\s*([^\n|]+)",
        "dative_plural": r"\|\s*Dativ Plural\s*=\s*([^\n|]+)",
        "accusative_plural": r"\|\s*Akkusativ Plural\s*=\s*([^\n|]+)",
    }

    for key, pattern in fields.items():
        match = re.search(pattern, wikitext)
        if match:
            value = match.group(1).strip()
            if value and value != "—":
                data[key] = value

    return data


def article_for(
    gender: Gender,
    number: Number,
    case: Case,
    article_type: ArticleType
) -> str | None:
    """Restituire articolo determinativo o indeterminativo tedesco."""

    if article_type == "definite":
        return DEFINITE_ARTICLES[(gender, number, case)]

    return INDEFINITE_ARTICLES[(gender, number, case)]


def build_noun_inflection_with_articles(
    lemma: str,
    *,
    gender: Gender | None = None,
    singular_forms: dict[Case, str] | None = None,
    plural_forms: dict[Case, str] | None = None
) -> list[NounInflectionRow]:
    """Produrre forme nominali con articoli, se il genere è noto."""

    rows: list[NounInflectionRow] = []

    singular_forms = singular_forms or {}
    plural_forms = plural_forms or {}

    for number in ("sg", "pl"):
        for case in ("nom", "acc", "dat", "gen"):
            if number == "sg":
                form = singular_forms.get(case, lemma)
            else:
                form = plural_forms.get(case, "")

            if not form:
                continue

            definite = None
            indefinite = None

            if gender:
                definite = article_for(gender, number, case, "definite")
                indefinite = article_for(gender, number, case, "indefinite")

            rows.append(
                NounInflectionRow(
                    case=case,
                    number=number,
                    form=form,
                    definite_article=definite,
                    indefinite_article=indefinite,
                    with_definite_article=(
                        f"{definite} {form}" if definite else None
                    ),
                    with_indefinite_article=(
                        f"{indefinite} {form}" if indefinite else None
                    ),
                )
            )

    return rows


def wiktionary_noun_inflection(word: str) -> tuple[list[NounInflectionRow], dict]:
    """Creare flessione nominale con articoli usando dati Wiktionary, se disponibili."""

    data = extract_wiktionary_noun_data(word)

    gender = data.get("gender")
    gender_value: Gender | None = gender if gender in {"m", "f", "n"} else None

    singular_forms: dict[Case, str] = {
        "nom": data.get("nominative_singular", word),
        "acc": data.get("accusative_singular", data.get("nominative_singular", word)),
        "dat": data.get("dative_singular", data.get("nominative_singular", word)),
        "gen": data.get("genitive_singular", data.get("nominative_singular", word)),
    }

    plural_forms: dict[Case, str] = {}

    if "nominative_plural" in data:
        plural_forms = {
            "nom": data.get("nominative_plural", ""),
            "acc": data.get("accusative_plural", data.get("nominative_plural", "")),
            "dat": data.get("dative_plural", data.get("nominative_plural", "")),
            "gen": data.get("genitive_plural", data.get("nominative_plural", "")),
        }

    rows = build_noun_inflection_with_articles(
        lemma=word,
        gender=gender_value,
        singular_forms=singular_forms,
        plural_forms=plural_forms,
    )

    return rows, data


def likely_pos_from_unimorph(entries: list[UniMorphEntry]) -> str | None:
    """Stimare categoria grammaticale dalle feature UniMorph."""

    all_features = {
        feature.upper()
        for entry in entries
        for feature in entry.features
    }

    if "V" in all_features:
        return "VERB"

    if "N" in all_features:
        return "NOUN"

    if "ADJ" in all_features:
        return "ADJ"

    return None


def produce_morphology(
    word: str,
    *,
    pos_hint: str | None = None,
    required_features: Iterable[str] | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    allow_download: bool = True,
    use_wiktionary: bool = True
) -> MorphologyResult:
    """Produrre informazioni morfologiche per una parola o lemma tedesco."""

    index = load_unimorph_index(
        cache_dir=cache_dir,
        allow_download=allow_download
    )

    lemma_result = produce_lemma(
        word,
        index=index,
        cache_dir=cache_dir,
        allow_download=allow_download
    )

    entries = lookup_inflected_forms(
        lemma_result.lemma,
        required_features=required_features,
        index=index,
        cache_dir=cache_dir,
        allow_download=allow_download
    )

    inferred_pos = (pos_hint or likely_pos_from_unimorph(entries) or "").upper()

    result = MorphologyResult(
        input_word=word,
        lemma=lemma_result.lemma,
        source=lemma_result.source,
        entries=entries,
    )

    if inferred_pos in VERB_POS_HINTS or any("V" in entry.features for entry in entries):
        result.verb_forms = [
            entry
            for entry in entries
            if "V" in {feature.upper() for feature in entry.features}
        ]

    if use_wiktionary and inferred_pos in SUBSTANTIVE_POS_HINTS:
        noun_rows, wiktionary_data = wiktionary_noun_inflection(lemma_result.lemma)
        result.noun_inflection = noun_rows
        result.wiktionary_data = wiktionary_data

        if not noun_rows:
            result.warnings.append(
                "Nessuna flessione nominale affidabile trovata tramite Wiktionary."
            )

    return result


def choose_verb_form(
    entries: list[UniMorphEntry],
    preferred_features: list[str],
    fallback: str
) -> str:
    """Scegliere una forma verbale da feature UniMorph."""

    for entry in entries:
        if features_match(entry, preferred_features):
            return entry.form

    return fallback


def generate_example_sentences(
    word: str,
    *,
    lemma: str | None = None,
    pos_hint: str | None = None,
    index: UniMorphIndex | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    allow_download: bool = True,
    count: int = 5
) -> list[str]:
    """Generare frasi tedesche semplici usando parole molto frequenti."""

    count = max(1, min(count, 5))
    normalized = normalize_word(word)

    if index is None:
        try:
            index = load_unimorph_index(
                cache_dir=cache_dir,
                allow_download=allow_download
            )
        except Exception:
            index = None

    if lemma is None:
        lemma_result = produce_lemma(
            normalized,
            index=index,
            cache_dir=cache_dir,
            allow_download=allow_download
        )
        lemma = lemma_result.lemma

    entries = index.by_lemma.get(lemma, []) if index else []
    inferred_pos = (pos_hint or likely_pos_from_unimorph(entries) or "").upper()

    if inferred_pos in VERB_POS_HINTS:
        ich_form = choose_verb_form(entries, ["V", "PRS", "1", "SG"], lemma)
        du_form = choose_verb_form(entries, ["V", "PRS", "2", "SG"], lemma)
        er_form = choose_verb_form(entries, ["V", "PRS", "3", "SG"], lemma)
        wir_form = choose_verb_form(entries, ["V", "PRS", "1", "PL"], lemma)

        sentences = [
            f"Ich {ich_form} heute.",
            f"Du {du_form} sehr gut.",
            f"Er {er_form} jeden Tag.",
            f"Wir {wir_form} hier.",
            f"Ich möchte {lemma}.",
        ]
        return sentences[:count]

    if inferred_pos in ADJECTIVE_POS_HINTS:
        sentences = [
            f"Das ist {normalized}.",
            f"Das Haus ist {normalized}.",
            f"Ich finde das {normalized}.",
            f"Heute ist es {normalized}.",
            f"Der Tag ist {normalized}.",
        ]
        return sentences[:count]

    noun_rows: list[NounInflectionRow] = []

    try:
        noun_rows, _ = wiktionary_noun_inflection(lemma)
    except Exception:
        noun_rows = []

    nom_sg = next(
        (row.with_definite_article for row in noun_rows if row.number == "sg" and row.case == "nom" and row.with_definite_article),
        lemma,
    )
    acc_sg = next(
        (row.with_indefinite_article for row in noun_rows if row.number == "sg" and row.case == "acc" and row.with_indefinite_article),
        lemma,
    )

    sentences = [
        f"{nom_sg} ist hier.",
        f"Ich sehe {acc_sg}.",
        f"Wir haben {acc_sg}.",
        f"Das ist {lemma}.",
        f"Ich brauche {acc_sg} heute.",
    ]

    return sentences[:count]


def canonical_pos_label(pos: str | None) -> str | None:
    """Normalizzare una POS label verso etichette interne stabili."""

    if not pos:
        return None

    value = pos.strip().upper()

    if value in SUBSTANTIVE_POS_HINTS:
        return "NOUN"

    if value in VERB_POS_HINTS:
        return "VERB"

    if value in ADJECTIVE_POS_HINTS:
        return "ADJ"

    if value in {"ADV", "ADVERB", "ADVERBIALE"}:
        return "ADV"

    if value in {"PRON", "PRONOUN", "PRONOMEN"}:
        return "PRON"

    if value in {"DET", "ART", "ARTICLE", "ARTIKEL"}:
        return "DET"

    if value in {"ADP", "PREP", "PREPOSITION", "PRÄPOSITION", "PRAEPOSITION"}:
        return "ADP"

    if value in {"CONJ", "CCONJ", "SCONJ", "KONJUNKTION"}:
        return "CONJ"

    if value in {"NUM", "NUMERAL", "ZAHL"}:
        return "NUM"

    if value in {"PART", "PARTICLE", "PARTIKEL"}:
        return "PART"

    if value in {"INTJ", "INTERJECTION", "INTERJEKTION"}:
        return "INTJ"

    if value in {"PROPN", "PROPER_NOUN", "EIGENNAME"}:
        return "PROPN"

    return value


def detect_pos_candidates_from_entries(entries: list[UniMorphEntry]) -> list[str]:
    """Ricavare possibili parti del discorso dalle feature UniMorph."""

    candidates: set[str] = set()

    for entry in entries:
        features = {feature.upper() for feature in entry.features}

        if "V" in features:
            candidates.add("VERB")
        if "N" in features:
            candidates.add("NOUN")
        if "ADJ" in features:
            candidates.add("ADJ")
        if "ADV" in features:
            candidates.add("ADV")

    return sorted(candidates)


def choose_primary_pos(
    pos_hint: str | None,
    entries: list[UniMorphEntry],
    word: str
) -> tuple[str | None, list[str], str]:
    """Scegliere la parte del discorso primaria."""

    if pos_hint:
        normalized = canonical_pos_label(pos_hint)
        return normalized, [normalized] if normalized else [], "high"

    candidates = detect_pos_candidates_from_entries(entries)

    if candidates:
        if len(candidates) == 1:
            return candidates[0], candidates, "medium"
        return candidates[0], candidates, "low"

    if word and word[0].isupper():
        return "NOUN", ["NOUN"], "low"

    return None, [], "low"


def estimate_lexical_family(
    lemma: str,
    index: UniMorphIndex | None = None
) -> LexicalFamilyInfo:
    """
    Stimare una famiglia lessicale in modo prudente.

    Questa funzione non pretende di ricostruire scientificamente la derivazione
    tedesca. Produce una chiave di famiglia e alcuni lemmi correlati solo quando
    esistono indizi semplici.
    """

    normalized = normalize_word(lemma)

    if not normalized:
        return LexicalFamilyInfo()

    family_key = normalized.lower()
    related: list[str] = []
    notes: list[str] = []

    if index is not None:
        lower = normalized.lower()
        for candidate in index.by_lemma.keys():
            candidate_lower = candidate.lower()
            if candidate == normalized:
                continue
            if candidate_lower.startswith(lower) or lower.startswith(candidate_lower):
                related.append(candidate)
            if len(related) >= 20:
                break

    if related:
        notes.append("Relazioni lessicali stimate tramite prefisso comune su lemmi UniMorph.")
        confidence = "low"
    else:
        confidence = "low"

    return LexicalFamilyInfo(
        family_key=family_key,
        base_lemma=normalized,
        related_lemmas=sorted(set(related)),
        derivation_notes=notes,
        confidence=confidence,
    )


def build_common_reference_payload(
    morphology: MorphologyResult
) -> dict:
    """Costruire la parte comune del record lessicale."""

    return {
        "lemma": morphology.lemma,
        "forms_count": len(morphology.entries),
        "forms": [
            {
                "form": entry.form,
                "features": list(entry.features),
            }
            for entry in morphology.entries
        ],
    }


def build_noun_reference_payload(
    morphology: MorphologyResult
) -> dict:
    """Payload specifico per sostantivi tedeschi."""

    wiktionary_data = morphology.wiktionary_data or {}

    return {
        "gender": wiktionary_data.get("gender"),
        "plural": wiktionary_data.get("nominative_plural"),
        "wiktionary_data": wiktionary_data,
        "inflection_with_articles": [
            {
                "case": row.case,
                "number": row.number,
                "form": row.form,
                "definite_article": row.definite_article,
                "indefinite_article": row.indefinite_article,
                "with_definite_article": row.with_definite_article,
                "with_indefinite_article": row.with_indefinite_article,
            }
            for row in morphology.noun_inflection
        ],
    }


def build_verb_reference_payload(
    morphology: MorphologyResult
) -> dict:
    """Payload specifico per verbi tedeschi."""

    forms = morphology.verb_forms or [
        entry
        for entry in morphology.entries
        if "V" in {feature.upper() for feature in entry.features}
    ]

    praesens = [entry for entry in forms if "PRS" in {feature.upper() for feature in entry.features}]
    praeteritum = [entry for entry in forms if "PST" in {feature.upper() for feature in entry.features}]
    participles = [entry for entry in forms if "PTCP" in {feature.upper() for feature in entry.features}]

    return {
        "forms_count": len(forms),
        "present_forms": [
            {"form": entry.form, "features": list(entry.features)}
            for entry in praesens
        ],
        "past_forms": [
            {"form": entry.form, "features": list(entry.features)}
            for entry in praeteritum
        ],
        "participles": [
            {"form": entry.form, "features": list(entry.features)}
            for entry in participles
        ],
        "all_verb_forms": [
            {"form": entry.form, "features": list(entry.features)}
            for entry in forms
        ],
    }


def build_adjective_reference_payload(
    morphology: MorphologyResult
) -> dict:
    """Payload specifico per aggettivi tedeschi."""

    adjective_forms = [
        entry
        for entry in morphology.entries
        if "ADJ" in {feature.upper() for feature in entry.features}
    ]

    return {
        "forms_count": len(adjective_forms),
        "forms": [
            {"form": entry.form, "features": list(entry.features)}
            for entry in adjective_forms
        ],
    }


def build_generic_pos_payload(
    morphology: MorphologyResult
) -> dict:
    """Payload per POS non ancora specializzate."""

    return {
        "forms_count": len(morphology.entries),
        "forms": [
            {"form": entry.form, "features": list(entry.features)}
            for entry in morphology.entries
        ],
    }


def build_pos_specific_payload(
    pos: str | None,
    morphology: MorphologyResult
) -> dict:
    """Costruire il payload specifico in base alla parte del discorso."""

    if pos == "NOUN":
        return build_noun_reference_payload(morphology)

    if pos == "VERB":
        return build_verb_reference_payload(morphology)

    if pos == "ADJ":
        return build_adjective_reference_payload(morphology)

    return build_generic_pos_payload(morphology)


def estimate_record_confidence(
    lemma_source: str,
    pos_confidence: str,
    morphology: MorphologyResult
) -> str:
    """Stimare una confidence complessiva per il record."""

    if lemma_source == "unimorph" and pos_confidence in {"high", "medium"} and morphology.entries:
        return "medium"

    if lemma_source == "spacy" and pos_confidence in {"high", "medium"}:
        return "medium"

    return "low"


# =============================================================================
# TOP-LEVEL LINGUISTIC ENTRY POINT
# =============================================================================
# Questa è la funzione che un orchestratore esterno deve chiamare per ogni
# token/parola da inserire nel reference database. Tutte le decisioni
# linguistiche locali sono concentrate qui: normalizzazione, lemma, POS,
# famiglia lessicale, payload comune, payload specifico per POS e frasi di
# esempio. La funzione restituisce un dataclass immutabile, non effettua I/O
# di persistenza e non assume nulla sullo schema fisico del database.
def build_de_lexical_reference(
    word: str,
    *,
    pos_hint: str | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    allow_download: bool = True,
    use_wiktionary: bool = True,
    examples_count: int = 5
) -> LexicalReferenceRecord:
    """
    Funzione top del modulo.

    Riceve una parola tedesca e restituisce una struttura dati completa,
    pronta per essere salvata da un modulo esterno nel reference database.
    """

    normalized_input = normalize_word(word)

    index = load_unimorph_index(
        cache_dir=cache_dir,
        allow_download=allow_download
    )

    lemma_result = produce_lemma(
        normalized_input,
        index=index,
        cache_dir=cache_dir,
        allow_download=allow_download
    )

    morphology = produce_morphology(
        normalized_input,
        pos_hint=pos_hint,
        cache_dir=cache_dir,
        allow_download=allow_download,
        use_wiktionary=use_wiktionary
    )

    pos, pos_candidates, pos_confidence = choose_primary_pos(
        pos_hint=pos_hint,
        entries=morphology.entries,
        word=normalized_input
    )

    lexical_family = estimate_lexical_family(
        lemma=morphology.lemma,
        index=index
    )

    common = build_common_reference_payload(morphology)
    pos_specific = build_pos_specific_payload(pos, morphology)

    example_sentences = generate_example_sentences(
        normalized_input,
        lemma=morphology.lemma,
        pos_hint=pos,
        index=index,
        cache_dir=cache_dir,
        allow_download=allow_download,
        count=examples_count
    )

    sources = sorted({
        lemma_result.source,
        morphology.source,
        "unimorph" if morphology.entries else "",
        "wiktionary" if morphology.wiktionary_data else "",
    } - {""})

    warnings = list(morphology.warnings)

    if pos is None:
        warnings.append("Parte del discorso non determinata in modo affidabile.")

    confidence = estimate_record_confidence(
        lemma_source=lemma_result.source,
        pos_confidence=pos_confidence,
        morphology=morphology
    )

    return LexicalReferenceRecord(
        language="de",
        input_word=word,
        normalized_input=normalized_input,
        lemma=morphology.lemma,
        lemma_source=lemma_result.source,
        lemma_alternatives=lemma_result.alternatives,
        pos=pos,
        pos_candidates=pos_candidates,
        lexical_family=lexical_family,
        common=common,
        pos_specific=pos_specific,
        example_sentences=example_sentences,
        sources=sources,
        warnings=warnings,
        confidence=confidence,
    )


def lexical_reference_to_dict(record: LexicalReferenceRecord) -> dict:
    """Convertire LexicalReferenceRecord in dizionario serializzabile.

    Questa funzione è l'unico adattatore tecnico verso moduli esterni: non
    salva su SQLite, ma produce un payload facilmente serializzabile in JSON
    o mappabile su tabelle relazionali. Il modulo database potrà decidere se
    normalizzare ulteriormente i campi in più tabelle o salvare una parte del
    payload come JSON.
    """

    return {
        "language": record.language,
        "input_word": record.input_word,
        "normalized_input": record.normalized_input,
        "lemma": record.lemma,
        "lemma_source": record.lemma_source,
        "lemma_alternatives": record.lemma_alternatives,
        "pos": record.pos,
        "pos_candidates": record.pos_candidates,
        "lexical_family": {
            "family_key": record.lexical_family.family_key,
            "base_lemma": record.lexical_family.base_lemma,
            "related_lemmas": record.lexical_family.related_lemmas,
            "derivation_notes": record.lexical_family.derivation_notes,
            "confidence": record.lexical_family.confidence,
        },
        "common": record.common,
        "pos_specific": record.pos_specific,
        "example_sentences": record.example_sentences,
        "sources": record.sources,
        "warnings": record.warnings,
        "confidence": record.confidence,
    }


def morphology_to_dict(result: MorphologyResult) -> dict:
    """Convertire MorphologyResult in dizionario serializzabile."""

    return {
        "input_word": result.input_word,
        "lemma": result.lemma,
        "source": result.source,
        "entries": [
            {
                "lemma": entry.lemma,
                "form": entry.form,
                "features": list(entry.features),
            }
            for entry in result.entries
        ],
        "noun_inflection": [
            {
                "case": row.case,
                "number": row.number,
                "form": row.form,
                "definite_article": row.definite_article,
                "indefinite_article": row.indefinite_article,
                "with_definite_article": row.with_definite_article,
                "with_indefinite_article": row.with_indefinite_article,
            }
            for row in result.noun_inflection
        ],
        "verb_forms": [
            {
                "lemma": entry.lemma,
                "form": entry.form,
                "features": list(entry.features),
            }
            for entry in result.verb_forms
        ],
        "wiktionary_data": result.wiktionary_data,
        "warnings": result.warnings,
    }


def demo(word: str, pos_hint: str | None = None) -> None:
    """Esecuzione dimostrativa da riga di comando."""

    record = build_de_lexical_reference(
        word,
        pos_hint=pos_hint
    )

    print(json.dumps(lexical_reference_to_dict(record), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Lemmatizzazione, flessione e frasi esempio per parole tedesche."
    )
    parser.add_argument("word", help="Parola tedesca da analizzare.")
    parser.add_argument("--pos", default=None, help="Suggerimento POS: NOUN, VERB, ADJ.")

    args = parser.parse_args()

    demo(args.word, pos_hint=args.pos)
