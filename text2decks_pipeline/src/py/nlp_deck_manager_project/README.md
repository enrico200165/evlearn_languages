# NLP Deck Management Platform

## Obiettivo

Il progetto è un gestore di deck linguistici con Reference DB per lingua.

L'obiettivo operativo è produrre deck di alta qualità, senza ridondanze accidentali, oppure con ridondanze intenzionali e documentate.

Le lingue di interesse primario sono:

- Tedesco (`de`)
- Giapponese (`ja`)

## Stato del progetto

Questa versione completa la pipeline end-to-end minima:

- lettura input testuali e sottotitoli
- NLP con spaCy se disponibile, fallback semplice se spaCy non è installato
- aggiornamento Reference DB SQLite
- produzione CSV Core
- creazione deck Core senza overlap tra bande
- creazione deck contestuali evitando duplicati Core non intenzionali
- creazione notes locali nel DB
- processor vanilla e custom
- export CSV compatibile con import Anki
- export APKG se `genanki` è installato

## Installazione

    python -m pip install -e .

Per NLP con spaCy:

    python -m pip install -e .[nlp]
    python -m spacy download de_core_news_sm
    python -m spacy download ja_core_news_sm

Per export APKG:

    python -m pip install -e .[anki]

## Esempio: generare deck Core tedesco

    python -m nlp_deck_manager.cli build-core \
        --input examples/sample_de.srt \
        --language de \
        --analyzer auto \
        --output-dir out_de_core \
        --max-rank 5000 \
        --run-default-processors

Output principali:

    out_de_core/lemma_frequencies_full_de.csv
    out_de_core/core_0001_5000_de.csv
    out_de_core/core_1000_de.csv
    out_de_core/core_0001_1000_de.csv
    out_de_core/deck_build_report_de.csv
    out_de_core/DE_Core_1000_anki.csv

## Costruzione progressiva dei deck Core

La costruzione dei deck Core è senza overlap:

    Core 1000: rank 1-1000
    Core 2000: rank 1001-2000, senza lemmi del Core 1000
    Core 3000: rank 2001-3000, senza lemmi dei Core 1000 e 2000
    Core 4000: rank 3001-4000, senza lemmi dei Core precedenti
    Core 5000: rank 4001-5000, senza lemmi dei Core precedenti

Il controllo è garantito dal ranking su `normalized_lemma` e dal report:

    core_overlap_report_<lang>.csv

## Esempio: generare deck contestuale

    python -m nlp_deck_manager.cli build-context \
        --input examples/sample_context_it_work_de.txt \
        --language de \
        --deck-name "German IT Work" \
        --output-dir out_de_it_work \
        --intentional-duplicates-csv examples/intentional_duplicates_de.csv \
        --run-default-processors

Il deck contestuale esclude i lemmi già presenti in deck Core, salvo duplicazione intenzionale documentata.

## Processor custom

Un processor custom deve estendere `NoteProcessor` e definire una classe `CustomProcessor`.

Esempio:

    processors_custom/custom_processor_example.py

Uso:

    python -m nlp_deck_manager.cli process-deck \
        --language de \
        --deck-name "German IT Work" \
        --default-processors \
        --custom-processor processors_custom/custom_processor_example.py \
        --export-csv

## Tedesco

Per il tedesco la pipeline predispone sempre campi per:

- articolo
- genere
- plurale
- flessione completa con articoli
- coniugazione completa per i verbi
- 5 frasi colloquiali frequenti di esempio

La versione vanilla non inventa questi dati. Inserisce placeholder espliciti da completare con:

- codice custom
- dizionari online
- traduttori
- AI
- revisione manuale

## Giapponese

Per il giapponese la pipeline predispone campi per:

- kanji
- kana
- romaji
- furigana
- livello JLPT
- 5 frasi colloquiali frequenti di esempio

Anche in questo caso la versione vanilla non inventa letture o traduzioni.

## Export Anki

CSV:

    python -m nlp_deck_manager.cli export-deck \
        --language de \
        --deck-name "DE Core 1000" \
        --output-dir out_export

APKG:

    python -m nlp_deck_manager.cli export-deck \
        --language de \
        --deck-name "DE Core 1000" \
        --output-dir out_export \
        --export-apkg

Richiede:

    python -m pip install genanki

## Cache delle informazioni per lemma: tabella info_lemma

Per evitare chiamate ripetute a API, dizionari online, traduttori o servizi AI, il Reference DB contiene la tabella `info_lemma`.

La tabella memorizza informazioni testuali associate a un lemma.

Campi principali:

    vocab_id
    nome_informazione
    informazione
    origine
    tstamp

Esempi di `nome_informazione`:

    flessione
    coniugazione
    frasi esempio
    traduzione
    articolo

Esempi di `origine`:

    API Duden
    Wiktionary
    OpenAI
    DeepL
    revisione manuale

Il campo `informazione` è TEXT, quindi può contenere testi lunghi o JSON, per esempio la coniugazione completa di un verbo in tutti i tempi e modi.

Salvare una informazione:

    python -m nlp_deck_manager.cli lemma-info-set \
        --language de \
        --lemma arbeiten \
        --info-name coniugazione \
        --origin "revisione manuale" \
        --info-file examples/arbeiten_coniugazione.json

Leggere le informazioni di un lemma:

    python -m nlp_deck_manager.cli lemma-info-get \
        --language de \
        --lemma arbeiten

Leggere una specifica informazione:

    python -m nlp_deck_manager.cli lemma-info-get \
        --language de \
        --lemma arbeiten \
        --info-name coniugazione

La pipeline dei processor include `CachedLemmaInfoProcessor`, che viene eseguito prima dei placeholder vanilla quando si usa `--run-default-processors` o `--default-processors`.

Il comportamento previsto per i processor custom è:

    1. cercare prima in info_lemma
    2. se l'informazione è presente, usarla senza chiamare API
    3. se l'informazione è assente, chiamare il servizio esterno
    4. salvare il risultato in info_lemma
    5. aggiornare la note

Esempio di processor custom con cache:

    processors_custom/cached_api_processor_example.py
