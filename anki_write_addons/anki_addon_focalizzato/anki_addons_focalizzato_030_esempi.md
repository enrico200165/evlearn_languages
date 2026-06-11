Versione completa e rifinita della Lezione 3. Ho mantenuto riferimenti ufficiali aggiornati per Anki, Google Cloud Translation e OpenAI Responses API. ([Google Cloud Documentation][1])

# Lezione 3 - Generare contenuti linguistici con filtri, Google Translate e ChatGPT

## Obiettivo

Nelle lezioni precedenti sono stati introdotti:

* l'architettura generale della pipeline;
* lo sviluppo esterno con `Collection(path)`;
* l'accesso alle collezioni Anki;
* la ricerca di note;
* la lettura e modifica dei campi;
* l'analisi di deck esistenti.

In questa lezione viene introdotto il cuore della pipeline:

```
decidere quali parole elaborare
generare contenuti linguistici
validare i risultati
aggiornare Anki
```

L'obiettivo non è semplicemente tradurre parole.

L'obiettivo è costruire un sistema capace di:

* partire da liste esterne di parole;
* filtrare parole troppo rare;
* chiedere conferma manuale quando necessario;
* generare traduzioni;
* generare frasi di esempio;
* generare coniugazioni;
* generare informazioni grammaticali;
* completare note Anki esistenti;
* preparare dati per nuove note Anki.

Le lingue principali considerate sono:

* tedesco;
* giapponese.

---

## Architettura generale

La pipeline completa è:

```
parola
    ->
normalizzazione
    ->
sistema di filtri preliminari
    ->
cache locale
    ->
Google Translate / ChatGPT / altri servizi
    ->
validazione
    ->
aggiornamento o creazione dati Anki
    ->
report finale
```

Il punto più importante di questa lezione è il sistema di filtri preliminari.

Prima di chiamare servizi esterni costosi o lenti, la pipeline deve decidere se una parola merita davvero di essere elaborata.

---

## Perché servono filtri preliminari

Supporre di avere una lista di 50.000 parole.

Non ha senso inviare tutte le parole a ChatGPT o Google Translate.

Occorre prima eliminare:

* parole troppo rare;
* parole già presenti nel deck;
* parole non adatte al livello di studio;
* parole dubbie;
* parole generate per errore;
* parole che richiedono revisione manuale;
* parole non appartenenti alla lingua prevista.

Il filtro preliminare riduce:

* costi API;
* tempi di elaborazione;
* rumore nel deck;
* errori;
* duplicazioni;
* quantità di materiale inutile.

---

## Caso d'uso reale

Input:

```
gehen
essen
schlafen
überantworten
```

Supponendo:

```
lingua = de
max_rank = 5000
```

La pipeline potrebbe decidere:

```
gehen         -> frequente -> chiedere conferma -> elaborare
essen         -> frequente -> chiedere conferma -> elaborare
schlafen      -> frequente -> chiedere conferma -> elaborare
überantworten -> troppo rara -> ignorare
```

In questa versione della lezione il prompt manuale viene sempre attivato.

La condizione è volutamente:

```
should_ask_user = True
```

In futuro potrà essere sostituita con una condizione più intelligente.

Esempi futuri:

```
chiedere conferma solo se il rank è vicino alla soglia

chiedere conferma solo se la parola è giapponese e ambigua

chiedere conferma solo se la parola non è già nel deck

chiedere conferma solo se la parola è assente dal corpus

chiedere conferma solo se l'IA segnala incertezza
```

---

# Sistema di filtri preliminari

## Obiettivo

Il sistema di filtri deve rispondere a una domanda:

```
questa parola deve essere elaborata?
```

La risposta non deve essere un semplice `True` o `False`.

Deve contenere anche la motivazione.

Esempio:

```
{
    "accepted": True,
    "reason": "frequency_ok_and_user_approved"
}
```

oppure:

```
{
    "accepted": False,
    "reason": "too_rare"
}
```

oppure:

```
{
    "accepted": False,
    "reason": "user_rejected"
}
```

Questo è importante perché la pipeline deve produrre un report finale chiaro.

---

## Architettura consigliata dei filtri

Struttura consigliata:

```
filters/

    frequency_filter.py

    manual_review_filter.py

    word_filter.py
```

Significato dei moduli:

```
frequency_filter.py
```

controlla la frequenza della parola.

```
manual_review_filter.py
```

chiede all'utente se la parola deve essere elaborata.

```
word_filter.py
```

combina più filtri e produce la decisione finale.

Questa separazione rende il sistema estendibile.

In futuro sarà possibile aggiungere:

* filtro duplicati;
* filtro per livello linguistico;
* filtro per parte del discorso;
* filtro per lingua;
* filtro per parole già presenti in Anki;
* filtro per parole vietate;
* filtro basato su IA;
* filtro basato su revisione manuale avanzata.

---

# Risultato standard di un filtro

Per evitare codice confuso, tutti i filtri dovrebbero restituire una struttura coerente.

Esempio:

```
def make_filter_result(
    accepted: bool,
    reason: str,
    details: dict | None = None
) -> dict:
    return {
        "accepted": accepted,
        "reason": reason,
        "details": details or {}
    }
```

Questa funzione evita di restituire valori diversi in punti diversi del programma.

---

# Filtro di frequenza

## Obiettivo

Il filtro di frequenza decide se una parola è abbastanza comune.

Interfaccia consigliata:

```
def check_frequency(
    word: str,
    language: str,
    frequency_data: dict,
    max_rank: int
) -> dict:
    ...
```

La funzione deve restituire:

```
accepted = True
```

se la parola è entro la soglia.

```
accepted = False
```

se la parola è troppo rara o non presente nella lista.

---

## Approccio con lista locale

Per elaborazioni massive conviene usare una lista locale.

Esempio file:

```
de_frequency.csv
```

Contenuto:

```
rank,word
1,der
2,die
3,und
523,gehen
841,essen
1200,schlafen
```

Per il giapponese:

```
ja_frequency.csv
```

Contenuto:

```
rank,word
1,の
2,に
3,は
732,食べる
1100,行く
```

---

## Caricare una lista di frequenza

File:

```
filters/frequency_filter.py
```

Codice:

```
import csv


def load_frequency_file(path: str) -> dict:
    """
    Caricare una lista di frequenza da file CSV.

    Il file deve avere almeno due colonne:

        rank
        word

    La funzione restituisce un dizionario:

        {
            "gehen": 523,
            "essen": 841
        }

    Questo dizionario permette di trovare rapidamente
    il rank di una parola.
    """

    result = {}

    with open(
        path,
        "r",
        encoding="utf-8",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            word = (
                row["word"]
                .strip()
            )

            rank = int(
                row["rank"]
            )

            if word:
                result[word] = rank

    return result
```

---

## Controllare la frequenza

File:

```
filters/frequency_filter.py
```

Codice:

```
def check_frequency(
    word: str,
    language: str,
    frequency_data: dict,
    max_rank: int
) -> dict:
    """
    Controllare se una parola è abbastanza frequente.

    Parametri:

        word:
            parola da valutare

        language:
            codice lingua, ad esempio:
            de, ja

        frequency_data:
            dizionario parola -> rank

        max_rank:
            rank massimo accettato

    Esempio:

        max_rank = 5000

    significa:

        accettare solo parole presenti
        tra le prime 5000 del corpus.

    La funzione restituisce sempre un dizionario
    con decisione e motivazione.
    """

    rank = frequency_data.get(
        word
    )

    if rank is None:
        return {
            "accepted": False,
            "reason": "frequency_not_found",
            "details": {
                "word": word,
                "language": language,
                "rank": None,
                "max_rank": max_rank
            }
        }

    if rank > max_rank:
        return {
            "accepted": False,
            "reason": "too_rare",
            "details": {
                "word": word,
                "language": language,
                "rank": rank,
                "max_rank": max_rank
            }
        }

    return {
        "accepted": True,
        "reason": "frequency_ok",
        "details": {
            "word": word,
            "language": language,
            "rank": rank,
            "max_rank": max_rank
        }
    }
```

---

## Tedesco e frequenza

Per il tedesco occorre fare attenzione a:

* sostantivi con iniziale maiuscola;
* forme flesse;
* verbi coniugati;
* participi;
* plurali;
* parole composte.

Esempi:

```
Haus
Häuser

gehen
gehe
geht
ging
gegangen
```

La frequenza può essere calcolata su:

* forma esatta;
* lemma;
* forma normalizzata.

Per una prima versione è accettabile usare la forma esatta.

In una versione successiva si potrà introdurre un modulo:

```
normalizer_de.py
```

con funzioni come:

```
normalize_german_word(word)
```

---

## Giapponese e frequenza

Per il giapponese il problema è più complesso.

Occorre considerare:

* kanji;
* hiragana;
* katakana;
* okurigana;
* forma dizionario;
* forma masu;
* forma te;
* segmentazione.

Esempi:

```
食べる
食べます
食べた
食べて
食べられる
```

Per una prima versione è accettabile usare la forma esatta.

In futuro sarà opportuno introdurre:

```
normalizer_ja.py
```

oppure usare strumenti di segmentazione e lemmatizzazione.

---

# Filtro manuale

## Obiettivo

Il filtro manuale chiede all'utente se una parola deve essere elaborata.

Serve nei casi in cui la decisione automatica non è sufficiente.

In questa versione il filtro manuale viene sempre attivato dopo il filtro di frequenza.

La condizione è:

```
should_ask_user = True
```

Questa condizione è volutamente semplice.

In futuro potrà diventare:

```
should_ask_user = rank > 4500
```

oppure:

```
should_ask_user = language == "ja"
```

oppure:

```
should_ask_user = frequency_result["reason"] == "frequency_not_found"
```

oppure:

```
should_ask_user = word_already_exists_in_deck(word)
```

---

## Implementazione per script esterno

Quando si lavora fuori da Anki si può usare `input()`.

File:

```
filters/manual_review_filter.py
```

Codice:

```
def ask_user_for_word(
    word: str,
    language: str,
    context: dict | None = None
) -> dict:
    """
    Chiedere all'utente se la parola deve essere elaborata.

    Questa versione usa input() perché è pensata
    per lo sviluppo esterno da terminale.

    Risposte accettate:

        s, si, sì, y, yes
            accettare la parola

        n, no
            rifiutare la parola

    Qualunque altra risposta viene trattata come rifiuto,
    per sicurezza.
    """

    context = context or {}

    rank = context.get(
        "rank"
    )

    max_rank = context.get(
        "max_rank"
    )

    print()
    print(
        "Valutazione manuale parola"
    )
    print(
        f"Parola: {word}"
    )
    print(
        f"Lingua: {language}"
    )

    if rank is not None:
        print(
            f"Rank: {rank}"
        )

    if max_rank is not None:
        print(
            f"Soglia massima: {max_rank}"
        )

    answer = input(
        "Elaborare questa parola? [s/N]: "
    ).strip().lower()

    accepted_answers = {
        "s",
        "si",
        "sì",
        "y",
        "yes"
    }

    if answer in accepted_answers:
        return {
            "accepted": True,
            "reason": "user_approved",
            "details": {
                "word": word,
                "language": language,
                "answer": answer
            }
        }

    return {
        "accepted": False,
        "reason": "user_rejected",
        "details": {
            "word": word,
            "language": language,
            "answer": answer
        }
    }
```

---

## Perché non inserire input() direttamente nella pipeline

Non conviene scrivere:

```
answer = input(...)
```

direttamente nella funzione principale della pipeline.

Motivo:

* rende il codice difficile da testare;
* rende difficile sostituire il terminale con una GUI;
* mescola logica di decisione e interazione utente;
* impedisce di riusare lo stesso filtro dentro Anki;
* rende difficile aggiungere altri filtri.

Il prompt manuale deve essere isolato in un modulo dedicato.

---

# Filtro composito

## Obiettivo

Combinare più filtri.

Ordine attuale:

```
1. filtro di frequenza
2. filtro manuale
```

In futuro l'ordine potrà diventare:

```
1. normalizzazione
2. controllo duplicati
3. filtro lingua
4. filtro frequenza
5. filtro livello
6. filtro manuale
7. filtro IA
```

---

## Implementazione

File:

```
filters/word_filter.py
```

Codice:

```
from .frequency_filter import (
    check_frequency
)

from .manual_review_filter import (
    ask_user_for_word
)


def should_ask_user_for_word(
    word: str,
    language: str,
    frequency_result: dict
) -> bool:
    """
    Decidere se attivare il prompt manuale.

    In questa versione la condizione è sempre True.

    Questo è intenzionale.

    In futuro questa funzione potrà essere modificata
    senza cambiare il resto della pipeline.

    Esempi futuri:

        return frequency_result["reason"] == "frequency_not_found"

        return language == "ja"

        return frequency_result["details"].get("rank", 0) > 4500
    """

    return True


def should_process_word(
    word: str,
    language: str,
    frequency_data: dict,
    max_rank: int
) -> dict:
    """
    Decidere se una parola deve essere elaborata.

    La decisione combina:

        - filtro di frequenza
        - eventuale revisione manuale

    La funzione restituisce un dizionario uniforme.

    Esempio accettato:

        {
            "accepted": True,
            "reason": "frequency_ok_and_user_approved",
            "details": {...}
        }

    Esempio rifiutato:

        {
            "accepted": False,
            "reason": "too_rare",
            "details": {...}
        }
    """

    frequency_result = check_frequency(
        word=word,
        language=language,
        frequency_data=frequency_data,
        max_rank=max_rank
    )

    if not frequency_result["accepted"]:
        return {
            "accepted": False,
            "reason": frequency_result["reason"],
            "details": {
                "word": word,
                "language": language,
                "frequency": frequency_result
            }
        }

    ask_user = should_ask_user_for_word(
        word=word,
        language=language,
        frequency_result=frequency_result
    )

    if ask_user:

        manual_result = ask_user_for_word(
            word=word,
            language=language,
            context=frequency_result.get(
                "details",
                {}
            )
        )

        if not manual_result["accepted"]:
            return {
                "accepted": False,
                "reason": manual_result["reason"],
                "details": {
                    "word": word,
                    "language": language,
                    "frequency": frequency_result,
                    "manual": manual_result
                }
            }

        return {
            "accepted": True,
            "reason": "frequency_ok_and_user_approved",
            "details": {
                "word": word,
                "language": language,
                "frequency": frequency_result,
                "manual": manual_result
            }
        }

    return {
        "accepted": True,
        "reason": "frequency_ok",
        "details": {
            "word": word,
            "language": language,
            "frequency": frequency_result
        }
    }
```

---

## Uso del filtro composito

Esempio:

```
from filters.frequency_filter import (
    load_frequency_file
)

from filters.word_filter import (
    should_process_word
)

frequency_data = load_frequency_file(
    "de_frequency.csv"
)

decision = should_process_word(
    word="gehen",
    language="de",
    frequency_data=frequency_data,
    max_rank=5000
)

if not decision["accepted"]:
    print(
        f"Parola ignorata: "
        f"{decision['reason']}"
    )

else:
    print(
        "Parola da elaborare"
    )
```

---

# Report dei filtri

Ogni parola esclusa deve essere registrata.

Esempio report:

```
word,language,status,reason,rank,max_rank
gehen,de,processed,frequency_ok_and_user_approved,523,5000
essen,de,processed,frequency_ok_and_user_approved,841,5000
schlafen,de,skipped,user_rejected,1200,5000
überantworten,de,skipped,too_rare,18420,5000
齎す,ja,skipped,frequency_not_found,,5000
```

Questo report è fondamentale perché permette di controllare:

* parole elaborate;
* parole saltate;
* decisioni automatiche;
* decisioni manuali;
* qualità della lista di frequenza.

---

# Cache locale

## Perché usare una cache

Dopo il filtro, prima di chiamare servizi online, conviene controllare la cache.

Supporre di elaborare la parola:

```
gehen
```

in dieci deck diversi.

Senza cache:

```
10 chiamate API
```

Con cache:

```
1 chiamata API
```

La cache deve stare dopo il filtro.

Schema:

```
parola
    ->
filtro
    ->
cache
    ->
servizi online
```

---

## Struttura semplice

File:

```
cache.json
```

Contenuto:

```
{
    "de:gehen:translation": "andare",
    "de:gehen:examples": [
        "Ich gehe nach Hause.",
        "Wir gehen zur Schule."
    ]
}
```

---

## Codice cache

File:

```
cache.py
```

Codice:

```
import json
import os


def load_cache(path: str) -> dict:
    """
    Caricare la cache da file JSON.

    Se il file non esiste o non è leggibile,
    restituire una cache vuota.

    In questo modo la pipeline può partire sempre.
    """

    if not os.path.exists(path):
        return {}

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except Exception:
        return {}


def save_cache(
    cache: dict,
    path: str
) -> None:
    """
    Salvare la cache in formato JSON.

    ensure_ascii=False è importante per mantenere
    correttamente caratteri tedeschi e giapponesi.
    """

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            cache,
            f,
            ensure_ascii=False,
            indent=2
        )


def make_cache_key(
    language: str,
    word: str,
    task: str
) -> str:
    """
    Creare una chiave cache uniforme.

    Esempi:

        de:gehen:translation

        ja:食べる:examples
    """

    return (
        f"{language}:"
        f"{word}:"
        f"{task}"
    )
```

---

# Google Translate

## Quando usarlo

Google Translate è utile per:

* traduzioni rapide;
* popolamento iniziale di campi;
* controllo di traduzioni mancanti;
* traduzioni base.

Non è lo strumento migliore per:

* spiegazioni grammaticali;
* coniugazioni complete;
* esempi controllati;
* analisi linguistiche articolate.

---

## Endpoint

La chiamata REST usata in questa lezione è basata su Google Cloud Translation API.

Riferimento:

```
Google Cloud Translation API
https://docs.cloud.google.com/translate/docs/reference/rest
```

Endpoint usato:

```
https://translation.googleapis.com/language/translate/v2
```

---

## Funzione

File:

```
translator.py
```

Codice:

```
import requests


def google_translate(
    text: str,
    api_key: str,
    source_language: str,
    target_language: str
) -> str:
    """
    Tradurre un testo usando Google Cloud Translation.

    Questa funzione è indipendente da Anki.

    Può essere usata:

        - da script esterno
        - da pipeline
        - da add-on
    """

    endpoint = (
        "https://translation.googleapis.com/"
        "language/translate/v2"
    )

    response = requests.post(
        endpoint,
        params={
            "key": api_key
        },
        json={
            "q": text,
            "source": source_language,
            "target": target_language,
            "format": "text"
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    try:
        return (
            data["data"]
            ["translations"][0]
            ["translatedText"]
            .strip()
        )

    except Exception as e:
        raise RuntimeError(
            f"Risposta Google Translate non valida: {data}"
        ) from e
```

---

## Test standalone

Prima di usare Anki:

```
from translator import (
    google_translate
)

API_KEY = "INSERIRE_API_KEY"

translated = google_translate(
    text="gehen",
    api_key=API_KEY,
    source_language="de",
    target_language="it"
)

print(translated)
```

Output atteso:

```
andare
```

---

# ChatGPT / OpenAI

## Quando usarlo

ChatGPT è utile per:

* generare frasi semplici;
* generare coniugazioni;
* generare spiegazioni grammaticali;
* generare esempi contestualizzati;
* produrre JSON strutturato;
* controllare o correggere dati già presenti.

---

## Endpoint

La lezione usa OpenAI Responses API.

Riferimento:

```
OpenAI API Reference
https://platform.openai.com/docs/api-reference

OpenAI Responses API
https://platform.openai.com/docs/guides/responses
```

Endpoint:

```
https://api.openai.com/v1/responses
```

---

## Funzione base

File:

```
translator.py
```

Codice:

```
import requests


def chatgpt_process(
    text: str,
    api_key: str,
    model: str,
    instruction: str
) -> str:
    """
    Inviare un testo a OpenAI Responses API.

    Questa funzione è generica.

    Non sa nulla di:

        - Anki
        - deck
        - note
        - campi

    Riceve testo e istruzioni,
    restituisce testo.
    """

    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization":
                f"Bearer {api_key}",
            "Content-Type":
                "application/json"
        },
        json={
            "model": model,
            "input": [
                {
                    "role": "system",
                    "content": instruction
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        },
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    output = data.get(
        "output_text"
    )

    if not output:
        raise RuntimeError(
            f"Risposta OpenAI non valida: {data}"
        )

    return output.strip()
```

---

## Nota sui modelli

Il nome del modello deve rimanere configurabile.

Non conviene scrivere in modo rigido nel codice:

```
gpt-...
```

È preferibile usare:

```
settings.json
```

Esempio:

```
{
    "openai_model": "INSERIRE_MODELLO"
}
```

I nomi dei modelli possono cambiare nel tempo.

---

# Generare esempi con ChatGPT

## Prompt consigliato

Per ottenere dati facilmente validabili, conviene chiedere JSON.

Esempio per il tedesco:

```
Genera 5 frasi molto semplici in tedesco
che contengano la parola indicata.

Rispondi solo in JSON valido.

Formato richiesto:

{
    "examples": [
        "...",
        "...",
        "...",
        "...",
        "..."
    ]
}
```

---

## Funzione

File:

```
content_generator.py
```

Codice:

```
import json

from translator import (
    chatgpt_process
)


def parse_json_response(
    text: str
) -> dict:
    """
    Convertire una risposta testuale in JSON.

    Se la risposta non è JSON valido,
    sollevare un errore.
    """

    try:
        return json.loads(
            text
        )

    except Exception as e:
        raise RuntimeError(
            f"Risposta non JSON valida: {text}"
        ) from e


def validate_examples(
    data: dict,
    expected_count: int = 5
) -> None:
    """
    Validare la struttura degli esempi.

    La funzione non restituisce True/False.

    Se i dati non sono validi,
    solleva un errore esplicito.
    """

    if "examples" not in data:
        raise RuntimeError(
            "Campo examples mancante"
        )

    examples = data["examples"]

    if not isinstance(
        examples,
        list
    ):
        raise RuntimeError(
            "examples non è una lista"
        )

    if len(examples) != expected_count:
        raise RuntimeError(
            f"Numero esempi errato: "
            f"{len(examples)}"
        )

    for example in examples:

        if (
            not isinstance(
                example,
                str
            )
            or
            not example.strip()
        ):
            raise RuntimeError(
                "Esempio vuoto o non testuale"
            )


def generate_examples(
    word: str,
    language: str,
    api_key: str,
    model: str
) -> dict:
    """
    Generare 5 frasi semplici per una parola.

    La lingua viene usata per costruire il prompt.
    """

    if language == "de":
        language_name = "tedesco"

    elif language == "ja":
        language_name = "giapponese"

    else:
        language_name = language

    instruction = (
        f"Genera 5 frasi molto semplici in {language_name} "
        f"che contengano la parola indicata. "
        f"Rispondi solo in JSON valido nel formato: "
        f'{{"examples": ["...", "...", "...", "...", "..."]}}'
    )

    response_text = chatgpt_process(
        text=word,
        api_key=api_key,
        model=model,
        instruction=instruction
    )

    data = parse_json_response(
        response_text
    )

    validate_examples(
        data
    )

    return data
```

---

# Generare coniugazioni

## Tedesco

Prompt concettuale:

```
Fornisci la coniugazione del verbo tedesco indicato.

Rispondi solo in JSON valido.

Includi:

- infinito
- presente
- Präteritum
- Perfekt
- participio passato
- imperativo
- 3 frasi semplici
```

Esempio output atteso:

```
{
    "infinitive": "gehen",
    "present": {
        "ich": "gehe",
        "du": "gehst",
        "er_sie_es": "geht",
        "wir": "gehen",
        "ihr": "geht",
        "sie_Sie": "gehen"
    },
    "praeteritum": "ging",
    "perfect": "ist gegangen",
    "past_participle": "gegangen",
    "imperative": {
        "du": "geh",
        "ihr": "geht",
        "Sie": "gehen Sie"
    },
    "examples": [
        "...",
        "...",
        "..."
    ]
}
```

---

## Giapponese

Prompt concettuale:

```
Analizza il verbo giapponese indicato.

Rispondi solo in JSON valido.

Includi:

- forma dizionario
- hiragana
- romaji
- traduzione italiana
- forma masu
- forma te
- forma nai
- forma ta
- forma potenziale
- 3 esempi semplici
```

Esempio output atteso:

```
{
    "dictionary_form": "食べる",
    "hiragana": "たべる",
    "romaji": "taberu",
    "translation_it": "mangiare",
    "masu_form": "食べます",
    "te_form": "食べて",
    "nai_form": "食べない",
    "ta_form": "食べた",
    "potential_form": "食べられる",
    "examples": [
        "...",
        "...",
        "..."
    ]
}
```

---

# Processo completo su parole esterne

## Schema

```
caricare parole
    ->
filtrare parola
    ->
controllare cache
    ->
generare contenuto
    ->
validare
    ->
scrivere o aggiornare Anki
    ->
registrare report
```

---

## Esempio completo di pipeline

File:

```
main_external.py
```

Codice:

```
from anki.collection import Collection

from filters.frequency_filter import (
    load_frequency_file
)

from filters.word_filter import (
    should_process_word
)

from content_generator import (
    generate_examples
)

from cache import (
    load_cache,
    save_cache,
    make_cache_key
)


COLLECTION_PATH = (
    "collection_test.anki2"
)

FREQUENCY_PATH = (
    "de_frequency.csv"
)

CACHE_PATH = (
    "cache.json"
)

LANGUAGE = "de"

MAX_RANK = 5000

OPENAI_API_KEY = (
    "INSERIRE_API_KEY"
)

OPENAI_MODEL = (
    "INSERIRE_MODELLO"
)


def load_words(
    path: str
) -> list[str]:
    """
    Caricare una lista semplice di parole.

    Il file contiene una parola per riga.
    """

    words = []

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            word = line.strip()

            if word:
                words.append(
                    word
                )

    return words


def main():

    words = load_words(
        "words_de.txt"
    )

    frequency_data = load_frequency_file(
        FREQUENCY_PATH
    )

    cache = load_cache(
        CACHE_PATH
    )

    col = Collection(
        COLLECTION_PATH
    )

    try:

        for word in words:

            decision = should_process_word(
                word=word,
                language=LANGUAGE,
                frequency_data=frequency_data,
                max_rank=MAX_RANK
            )

            if not decision["accepted"]:
                print(
                    f"SKIP {word}: "
                    f"{decision['reason']}"
                )
                continue

            cache_key = make_cache_key(
                language=LANGUAGE,
                word=word,
                task="examples"
            )

            if cache_key in cache:

                generated = cache[
                    cache_key
                ]

            else:

                generated = generate_examples(
                    word=word,
                    language=LANGUAGE,
                    api_key=OPENAI_API_KEY,
                    model=OPENAI_MODEL
                )

                cache[
                    cache_key
                ] = generated

                save_cache(
                    cache,
                    CACHE_PATH
                )

            print(
                f"OK {word}: "
                f"{generated}"
            )

            # In una lezione successiva questa parte
            # verrà sostituita da create_or_update_note().
            #
            # Qui ci si limita a mostrare il punto
            # in cui i dati validati entrano in Anki.

        col.save()

    finally:

        col.close(
            save=True
        )

        save_cache(
            cache,
            CACHE_PATH
        )


if __name__ == "__main__":
    main()
```

---

# Integrazione con note Anki esistenti

## Caso tipico

Una nota contiene:

```
Word = gehen
Examples = ""
```

La pipeline deve:

```
leggere Word
filtrare gehen
generare esempi
scrivere Examples
```

---

## Funzione di aggiornamento

File:

```
collection_processor.py
```

Codice:

```
def enrich_notes_with_examples(
    col,
    query,
    language,
    frequency_data,
    max_rank,
    generate_examples_function
) -> dict:
    """
    Arricchire note esistenti aggiungendo esempi.

    Questa funzione non conosce ChatGPT.

    Riceve una funzione esterna:

        generate_examples_function

    In questo modo rimane testabile e riutilizzabile.
    """

    result = {
        "found": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0
    }

    note_ids = col.find_notes(
        query
    )

    result["found"] = len(
        note_ids
    )

    for note_id in note_ids:

        try:

            note = col.get_note(
                note_id
            )

            if (
                "Word"
                not in note.keys()
            ):
                result["skipped"] += 1
                continue

            if (
                "Examples"
                not in note.keys()
            ):
                result["skipped"] += 1
                continue

            word = (
                note["Word"]
                .strip()
            )

            if not word:
                result["skipped"] += 1
                continue

            if (
                note["Examples"]
                .strip()
            ):
                result["skipped"] += 1
                continue

            # Il filtro composito decide se elaborare
            # la parola oppure saltarla.
            decision = should_process_word(
                word=word,
                language=language,
                frequency_data=frequency_data,
                max_rank=max_rank
            )

            if not decision["accepted"]:
                result["skipped"] += 1
                continue

            generated = generate_examples_function(
                word
            )

            examples = generated[
                "examples"
            ]

            note["Examples"] = (
                "\n".join(
                    examples
                )
            )

            note.add_tag(
                "examples_generated"
            )

            note.flush()

            result["updated"] += 1

        except Exception:

            result["errors"] += 1

    return result
```

Nota tecnica:

la funzione precedente usa `should_process_word()` ma non mostra l'import per mantenere breve l'esempio. In un file reale andrebbe aggiunto:

```
from filters.word_filter import (
    should_process_word
)
```

---

# Prompt manuale dentro Anki

La versione con `input()` è adatta allo sviluppo esterno da terminale.

Dentro Anki non conviene usare `input()`.

In futuro si potrà creare un filtro manuale alternativo basato su messagebox.

Esempio concettuale:

```
from aqt.utils import askUser

accepted = askUser(
    "Elaborare la parola gehen?"
)
```

Per mantenere il sistema flessibile, la pipeline non deve dipendere direttamente da `input()` o da `askUser()`.

La pipeline deve dipendere solo da una funzione:

```
ask_user_for_word(...)
```

In questo modo si potranno avere due implementazioni:

```
terminal_manual_review_filter.py
```

per sviluppo esterno.

```
anki_manual_review_filter.py
```

per add-on.

---

# Report finale

Ogni esecuzione deve produrre un report.

Campi consigliati:

```
word
language
status
reason
rank
max_rank
action
```

Esempio:

```
word,language,status,reason,rank,max_rank,action
gehen,de,processed,frequency_ok_and_user_approved,523,5000,examples_generated
essen,de,processed,frequency_ok_and_user_approved,841,5000,examples_generated
schlafen,de,skipped,user_rejected,1200,5000,
überantworten,de,skipped,too_rare,18420,5000,
齎す,ja,skipped,frequency_not_found,,5000,
```

Il report serve a capire perché una parola è stata elaborata o ignorata.

---

# Regole pratiche

1. Applicare sempre il filtro prima delle chiamate API.

2. Il filtro deve restituire anche la motivazione.

3. Il prompt manuale non deve stare nella pipeline principale.

4. La condizione del prompt manuale deve essere isolata in una funzione modificabile.

5. Per ora usare:

   ```
   return True
   ```

   nella funzione `should_ask_user_for_word()`.

6. Registrare sempre le parole saltate.

7. Usare cache locale per ridurre costi e tempi.

8. Validare sempre le risposte di ChatGPT.

9. Richiedere JSON quando serve una struttura dati.

10. Separare sempre:

    ```
    filtro
    generazione
    validazione
    scrittura Anki
    ```

11. Tenere configurabile il modello OpenAI.

12. Tenere configurabile il limite di frequenza.

13. Per tedesco e giapponese prevedere normalizzazioni diverse.

14. Usare il prompt manuale come strumento temporaneo di controllo qualità.

15. In futuro sostituire il prompt manuale continuo con condizioni più selettive.

---

## Alcuni riferimenti

Google Cloud Translation API

[https://docs.cloud.google.com/translate/docs/reference/rest](https://docs.cloud.google.com/translate/docs/reference/rest)

OpenAI API Reference

[https://platform.openai.com/docs/api-reference](https://platform.openai.com/docs/api-reference)

OpenAI Responses API

[https://platform.openai.com/docs/guides/responses](https://platform.openai.com/docs/guides/responses)

Anki Python Module

[https://addon-docs.ankiweb.net/the-anki-module.html](https://addon-docs.ankiweb.net/the-anki-module.html)

Leipzig Corpora Collection

[https://wortschatz.uni-leipzig.de/en](https://wortschatz.uni-leipzig.de/en)

Wiktionary Frequency Lists

[https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists](https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists)

[1]: https://docs.cloud.google.com/translate/docs/reference/rest?utm_source=chatgpt.com "Cloud Translation API"
