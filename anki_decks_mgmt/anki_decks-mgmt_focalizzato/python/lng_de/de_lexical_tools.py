#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
german_lexical_tools.py

Scopo
-----
Funzioni di supporto per pipeline Anki / studio del tedesco:

- produrre il lemma di una parola tedesca;
- recuperare forme flesse da una risorsa morfologica locale/cache;
- produrre flessioni nominali con articoli quando il genere è noto;
- produrre coniugazioni verbali quando presenti nel dataset;
- generare 5 frasi di esempio semplici usando parole frequenti.

Strategia tecnica
-----------------
1. UniMorph German come fonte principale per lemma e forme flesse.
   Il dataset viene scaricato una volta e salvato in cache locale.

2. spaCy come fallback opzionale per la lemmatizzazione.
   Richiede:
       python -m pip install spacy
       python -m spacy download de_core_news_sm

3. Wiktionary tedesco come fallback opzionale per provare a ricavare
   genere e forme nominali da wikitext. Il parser è volutamente prudente:
   se non trova dati affidabili, restituisce campi vuoti invece di inventare.

Avvertenze
----------
- Per il tedesco, la flessione corretta di un nome richiede il genere.
  Se il genere non è noto, gli articoli possono essere restituiti come None.
- Le forme derivate da UniMorph sono buone per lookup morfologico, ma non
  sostituiscono una revisione didattica quando si generano carte Anki.
- Le frasi di esempio sono generate con template controllati e lessico comune.
  Sono semplici, non letterarie, e servono come base da arricchire/verificare.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal


DEFAULT_CACHE_DIR = Path("./lexical_cache")
UNIMORPH_DEU_URL = "https://raw.githubusercontent.com/unimorph/deu/master/deu"
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

    morphology = produce_morphology(
        word,
        pos_hint=pos_hint
    )

    print(json.dumps(morphology_to_dict(morphology), ensure_ascii=False, indent=2))

    print("\nFrasi di esempio:")
    for sentence in generate_example_sentences(
        word,
        lemma=morphology.lemma,
        pos_hint=pos_hint
    ):
        print(f"- {sentence}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Lemmatizzazione, flessione e frasi esempio per parole tedesche."
    )
    parser.add_argument("word", help="Parola tedesca da analizzare.")
    parser.add_argument("--pos", default=None, help="Suggerimento POS: NOUN, VERB, ADJ.")

    args = parser.parse_args()

    demo(args.word, pos_hint=args.pos)
