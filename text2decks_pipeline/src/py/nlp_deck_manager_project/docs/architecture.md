# Architettura

## Visione generale

Il sistema è primariamente un gestore di deck linguistici.

Il Reference DB è uno strumento di supporto per ridurre replicazioni accidentali e documentare quelle intenzionali.

    @startuml
    artifact "Input" as Input
    component "Reader" as Reader
    component "NLP" as NLP
    database "Reference DB" as RefDb
    component "Deck Manager" as DeckManager
    component "Note Processor Pipeline" as Pipeline
    artifact "CSV / APKG" as Output

    Input --> Reader
    Reader --> NLP
    NLP --> RefDb
    RefDb --> DeckManager
    DeckManager --> Pipeline
    Pipeline --> Output
    @enduml

## Regola Core

I deck Core sono progressivi e non si sovrappongono:

    Core 1000 = rank 1-1000
    Core 2000 = rank 1001-2000
    Core 3000 = rank 2001-3000
    Core 4000 = rank 3001-4000
    Core 5000 = rank 4001-5000

## Deck contestuali

Un deck contestuale contiene parole specifiche non già presenti nei Core.

Una duplicazione è ammessa solo se intenzionale e descritta nella relazione lemma-deck.

## Tedesco

Le note tedesche devono essere predisposte per:

- flessione completa con articoli
- coniugazione completa dei verbi
- 5 frasi colloquiali frequenti

La pipeline vanilla crea campi e placeholder, non inventa dati linguistici.

## Tabella info_lemma

La tabella `info_lemma` serve a memorizzare informazioni persistenti associate ai lemmi.

Lo scopo principale è evitare chiamate ripetute a API, dizionari online, traduttori e servizi AI.

    @startuml
    entity Lemma
    entity InfoLemma

    Lemma ||--o{ InfoLemma
    @enduml

Schema logico:

    info_lemma
        id
        vocab_id
        nome_informazione
        informazione
        origine
        tstamp

`nome_informazione` è una stringa libera.

Esempi:

    flessione
    coniugazione
    frasi esempio
    traduzione
    articolo

`informazione` è un campo TEXT, adatto anche a contenere JSON lunghi, per esempio la coniugazione completa di un verbo.

`origine` descrive da dove arriva l'informazione.

Esempi:

    API
    sito web
    Wiktionary
    OpenAI
    revisione manuale

`tstamp` contiene data e ora dell'ultima creazione o aggiornamento della riga.

Regola operativa:

    prima di chiamare una API, un processor deve consultare info_lemma
    se l'informazione esiste, deve riusarla
    se l'informazione non esiste, può chiamare la API
    dopo la chiamata, deve salvare il risultato in info_lemma

Questa tabella non sostituisce i campi delle note. È una cache lessicale persistente, collegata al lemma, che può essere riutilizzata da più deck e più processor.
