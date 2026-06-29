# Lezione 1 - Architettura di sviluppo per creare, arricchire e correggere deck Anki

## Obiettivo della lezione

L'obiettivo principale non è creare subito add-on Anki tradizionali.

L'obiettivo è costruire pipeline Python capaci di:

* creare deck Anki partendo da liste esterne di parole;
* leggere parole da file TXT, CSV, JSON o altre sorgenti;
* filtrare le parole in base alla frequenza d'uso;
* generare contenuti linguistici tramite servizi online o IA;
* aggiungere frasi di esempio, traduzioni, definizioni, note grammaticali e coniugazioni;
* esaminare deck Anki già esistenti;
* popolare campi mancanti;
* correggere campi errati;
* aggiornare note esistenti in modo controllato;
* trasformare lo stesso codice, se necessario, in un add-on Anki.

Il punto chiave è questo:

```
prima sviluppare una normale pipeline Python,
poi eventualmente integrarla dentro Anki.
```

Per questo tipo di lavoro Anki deve essere visto soprattutto come:

```
una collezione dati manipolabile da Python
```

e solo in seconda battuta come applicazione desktop da estendere con add-on.

---

## Scenario generale

Un flusso tipico sarà:

```
lista parole esterna
    ->
normalizzazione parole
    ->
controllo frequenza
    ->
filtro lingua
    ->
generazione contenuti con IA o servizi web
    ->
validazione dei dati generati
    ->
creazione o aggiornamento note Anki
    ->
salvataggio della collezione
```

Esempio pratico:

```
input:
    gehen
    essen
    schlafen

elaborazione:
    controllare se ogni verbo è abbastanza frequente
    generare coniugazione
    generare esempi
    generare traduzione italiana
    generare note grammaticali

output:
    note Anki nuove o aggiornate
```

---

## Perché sviluppare prima fuori da Anki

Lavorare direttamente dentro Anki non è il metodo migliore per questo obiettivo.

Quando si sviluppa direttamente come add-on:

* spesso è necessario riavviare Anki dopo modifiche al codice;
* il debugging è più scomodo;
* i test automatici sono più difficili;
* le chiamate a servizi online sono più difficili da controllare;
* eventuali errori possono agire direttamente sulla collezione reale;
* è più facile confondere codice applicativo e codice di integrazione.

Per generazione e correzione massiva di deck è preferibile sviluppare prima script Python esterni.

Uno script esterno può:

* aprire una copia della collezione;
* elaborare migliaia di note;
* usare log dettagliati;
* salvare report;
* essere eseguito più volte;
* essere testato senza aprire Anki;
* essere integrato successivamente in un add-on.

---

## Due modalità di lavoro

Esistono due modalità principali.

## Modalità A - sviluppo esterno

È la modalità consigliata.

In questa modalità il codice Python viene eseguito fuori da Anki.

Si apre direttamente una collezione Anki tramite il modulo `anki`.

Schema:

```
script Python
    ->
Collection(path)
    ->
collection.anki2
    ->
lettura, creazione, modifica note
```

Esempio concettuale:

```
from anki.collection import Collection

col = Collection("collection_test.anki2")

note_ids = col.find_notes("tag:da_controllare")

col.close(save=True)
```

Questa modalità è ideale per:

* creare deck da liste esterne;
* generare note nuove;
* controllare deck esistenti;
* correggere dati;
* usare servizi online;
* usare IA;
* eseguire test;
* lavorare su copie della collezione.

---

## Modalità B - integrazione interna come add-on

In questa modalità il codice viene eseguito dentro Anki.

La collezione è già aperta ed è disponibile tramite:

```
from aqt import mw

col = mw.col
```

Schema:

```
Anki aperto -> add-on -> mw.col -> collezione corrente  
```

Questa modalità è utile solo quando serve:

* aggiungere una voce di menu;
* eseguire una procedura dall'interfaccia di Anki;
* mostrare messaggi all'utente;
* integrare il codice nel flusso normale di uso di Anki.

Per il percorso attuale questa modalità è secondaria.

Prima deve funzionare bene la pipeline esterna.

---

## Differenza fondamentale tra sviluppo esterno e interno

La differenza principale riguarda il modo in cui si ottiene l'oggetto collezione.

Sviluppo esterno:

```
from anki.collection import Collection

col = Collection(path)
```

Sviluppo interno come add-on:

```
from aqt import mw

col = mw.col
```

Dopo aver ottenuto `col`, molte operazioni sono simili:

```
col.find_notes(...)

col.get_note(...)

note["Campo"]

note["Campo"] = valore

note.flush()
```

Questa somiglianza permette di scrivere codice riutilizzabile.

Il codice migliore non dovrebbe dipendere direttamente da `mw`.  
Dovrebbe ricevere una collezione come parametro.

Esempio:

```
def process_collection(col, query):
    note_ids = col.find_notes(query)

    for note_id in note_ids:
        note = col.get_note(note_id)
        ...
```

La stessa funzione potrà essere usata:

* da uno script esterno;
* da un add-on Anki.

---

## Installazione dell'ambiente Python

Per lavorare fuori da Anki serve installare il pacchetto Python ufficiale.

Comando minimo:

```
pip install anki
```

Per sviluppo add-on, completamento automatico e ambiente più completo:

```
pip install "aqt[qt6]"
```

Riferimento ufficiale:

https://addon-docs.ankiweb.net/editor-setup.html

La documentazione Anki indica che i pacchetti Python precompilati possono essere usati anche per creare script da riga di comando che modificano file `.anki2` tramite le librerie Python di Anki.

Riferimento: https://github.com/ankitects/anki/blob/main/docs/development.md  

Nota importante:  
installare `anki` o `aqt` non significa avere Anki desktop aperto.  
Significa avere accesso alle librerie Python necessarie per lavorare su una collezione.  

---

## Aprire una collezione Anki fuori da Anki

Una collezione Anki si trova normalmente nel file: `collection.anki2`

Esempio Windows:

```
C:\Users\NOME_UTENTE\AppData\Roaming\Anki2\NOME_PROFILO\collection.anki2
```

Durante lo sviluppo non conviene aprire direttamente la collezione reale.  
Conviene creare una copia.

Esempio:

```
import shutil
from pathlib import Path

original_collection = Path(
    r"C:\Users\NOME_UTENTE\AppData\Roaming\Anki2\Profilo\collection.anki2"
)

test_collection = Path(
    r"D:\anki_dev\collection_test.anki2"
)

test_collection.parent.mkdir(
    parents=True,
    exist_ok=True
)

shutil.copy2(
    original_collection,
    test_collection
)
```

Ora si può aprire la copia:

```
from anki.collection import Collection

col = Collection(str(test_collection))

try:
    note_ids = col.find_notes("")
    print(f"Note trovate: {len(note_ids)}")
finally:
    col.close(save=False)
```

---

## Regola di sicurezza principale

Non aprire la stessa collezione reale mentre Anki è già aperto sullo stesso profilo.

Durante lo sviluppo usare sempre:

```
una copia della collezione
```

oppure:

```
un profilo Anki di test
```

oppure:

```
una collezione temporanea dedicata
```

Non modificare direttamente il database SQLite con `sqlite3`.

Usare sempre le API Anki.

Riferimento ufficiale sul modulo Python Anki:

https://addon-docs.ankiweb.net/the-anki-module.html

---

## Architettura consigliata del progetto

Per il tipo di attività previsto, una struttura realistica è:

```
anki_language_pipeline/

    main_external.py

    settings.json

    input_words/
        words_de.txt
        words_ja.txt

    reports/

    src/
        anki_collection.py
        word_loader.py
        frequency_filter.py
        content_generator.py
        deck_writer.py
        deck_reviewer.py
        cache.py
        logging_utils.py

    tests/
```

Significato dei moduli.

```
main_external.py
```

Script principale da eseguire fuori da Anki.

```
settings.json
```

Configurazione del progetto.

```
word_loader.py
```

Legge parole da TXT, CSV, JSON o altre sorgenti.

```
frequency_filter.py
```

Decide se una parola è abbastanza frequente per essere elaborata.

```
content_generator.py
```

Chiama servizi online o IA per generare frasi, traduzioni, definizioni e coniugazioni.

```
deck_writer.py
```

Crea nuove note o aggiorna note esistenti.

```
deck_reviewer.py
```

Analizza deck esistenti per trovare campi mancanti o dati incoerenti.

```
cache.py
```

Evita di richiamare servizi online per parole già elaborate.

```
logging_utils.py
```

Gestisce log e report.

```
tests/
```

Contiene test automatici.

---

## Flusso operativo consigliato

## Fase 1 - Preparare input esterno

Esempio file:

```
input_words/words_de.txt
```

Contenuto:

```
gehen
essen
Haus
sprechen
machen
```

Esempio file:

```
input_words/words_ja.txt
```

Contenuto:

```
食べる
行く
見る
学校
話す
```

---

## Fase 2 - Normalizzare le parole

Prima di interrogare servizi online o IA è necessario normalizzare.

Per il tedesco possono essere rilevanti:

* maiuscole e minuscole;
* sostantivi con iniziale maiuscola;
* forme flesse;
* verbi all'infinito;
* parole composte.

Per il giapponese possono essere rilevanti:

* forma in kanji;
* forma in kana;
* okurigana;
* segmentazione;
* lemma;
* forma di dizionario.

Questa fase non deve essere sottovalutata.

La parola che appare in una lista può non coincidere con la forma da usare per cercare frequenza, esempi e coniugazioni.

---

## Fase 3 - Controllare la frequenza

Il filtro di frequenza è un requisito centrale.

Serve a evitare di generare contenuti per parole troppo rare.

Esempio:

```
se la parola è tra le prime N più frequenti:
    elaborare

altrimenti:
    ignorare e registrare nel log
```

Questa scelta consente di:

* ridurre costi API;
* ridurre tempi di elaborazione;
* concentrarsi sulle parole più utili;
* evitare deck pieni di parole poco rilevanti.

Funzione concettuale:

```
def is_frequent_enough(
    word: str,
    language: str,
    max_rank: int
) -> bool:
    ...
```

Esempio d'uso:

```
if not is_frequent_enough(
    word="gehen",
    language="de",
    max_rank=5000
):
    return
```

Per tedesco e giapponese il filtro di frequenza può essere basato su:

* liste locali pre-scaricate;
* dataset ordinati parola-rank;
* librerie Python;
* servizi online.

Per elaborazioni massive, la soluzione più robusta è spesso una lista locale.

---

## Fase 4 - Generare contenuti

Solo dopo il filtro di frequenza ha senso chiamare IA o servizi online.

Esempi di contenuti generabili:

Per una parola tedesca:

```
parola
articolo
plurale
traduzione italiana
pronuncia
livello indicativo
5 frasi semplici
note grammaticali
parole correlate
```

Per un verbo tedesco:

```
infinito
presente
Präteritum
Perfekt
participio passato
imperativo
esempi
```

Per una parola giapponese:

```
kanji
lettura kana
romaji
traduzione italiana
5 frasi semplici
furigana se disponibile
note d'uso
livello indicativo
esempi
```

Per un verbo giapponese:

```
forma dizionario
forma masu
forma te
forma nai
forma ta
forma potenziale
forma volitiva
esempi
```

---

## Fase 5 - Validare i dati generati

I dati prodotti da IA o servizi web non devono essere accettati ciecamente.

Occorre prevedere almeno:

* controllo che i campi obbligatori non siano vuoti;
* controllo che la risposta sia JSON valido se si richiede JSON;
* controllo che le liste abbiano il numero atteso di elementi;
* controllo che il testo non contenga messaggi di errore;
* log degli errori;
* eventuale salvataggio in report per revisione manuale.

Esempio:

```
def validate_generated_entry(entry: dict) -> bool:
    required = [
        "word",
        "translation",
        "examples"
    ]

    for field in required:
        if not entry.get(field):
            return False

    return True
```

---

## Fase 6 - Scrivere o aggiornare Anki

La pipeline può fare due cose diverse.

## Caso A - Creare nuove note

Esempio:

```
parola nuova -> generare contenuti -> creare nuova nota
```

## Caso B - Aggiornare note esistenti

Esempio:

```
nota già esistente -> campo Esempi vuoto ->  
generare esempi -> popolare campo Esempi
```

La logica deve distinguere bene:

* creazione;
* aggiornamento;
* correzione;
* salto;
* errore.

---

## Fase 7 - Salvare report

Ogni esecuzione dovrebbe produrre un report.

Esempio report CSV:

```
word,language,status,reason
gehen,de,created,ok
schlafen,de,updated,examples_added
überantworten,de,skipped,too_rare
食べる,ja,created,ok
齎す,ja,skipped,too_rare
```

Il report permette di sapere:

* quali parole sono state elaborate;
* quali parole sono state ignorate;
* quali note sono state create;
* quali note sono state aggiornate;
* quali errori sono avvenuti.

---

## Modello architetturale generale

Il cuore del progetto dovrebbe essere indipendente da Anki desktop.

Schema:

```
parole esterne
    ->
word_loader
    ->
frequency_filter
    ->
content_generator
    ->
validator
    ->
deck_writer
    ->
report
```

Anki entra solo nella fase:

```
deck_writer
```

e può essere usato in due modi:

```
Collection(path)
```

oppure:

```
mw.col
```

---

## Esempio minimo di pipeline esterna

```
from anki.collection import Collection

from src.word_loader import load_words
from src.frequency_filter import is_frequent_enough
from src.content_generator import generate_content
from src.deck_writer import create_or_update_note
from src.logging_utils import log_line

COLLECTION_PATH = r"D:\anki_dev\collection_test.anki2"
WORDS_PATH = r"input_words\words_de.txt"

LANGUAGE = "de"
MAX_RANK = 5000

def main():
    col = Collection(COLLECTION_PATH)

    try:
        words = load_words(WORDS_PATH)

        for word in words:
            if not is_frequent_enough(
                word=word,
                language=LANGUAGE,
                max_rank=MAX_RANK
            ):
                log_line(
                    f"{word}: ignorata perché non abbastanza frequente"
                )
                continue

            generated = generate_content(
                word=word,
                language=LANGUAGE
            )

            create_or_update_note(
                col=col,
                generated=generated
            )

        col.save()

    finally:
        col.close(save=True)

if __name__ == "__main__":
    main()
```

Questo esempio non è ancora un programma completo.

Serve a mostrare l'architettura.

Le lezioni successive approfondiranno i moduli uno alla volta.

---

## Quando creare davvero un add-on

Un add-on diventa utile solo quando si vuole eseguire la procedura da dentro Anki.

Esempi:

* selezionare un deck e arricchirlo con un comando;
* correggere le note aperte nel browser;
* aggiungere un comando nel menu Strumenti;
* mostrare un riepilogo finale nell'interfaccia;
* far usare la procedura ad altri utenti non tecnici.

Anche in questo caso la logica principale non dovrebbe stare in `__init__.py`.

L'add-on dovrebbe limitarsi a:

```
ottenere mw.col
chiamare la pipeline
mostrare risultato
```

Esempio concettuale:

```
from aqt import mw
from aqt.qt import QAction
from aqt.utils import showInfo, showCritical

from .pipeline import run_pipeline

def run_from_anki():
    try:
        result = run_pipeline(
            col=mw.col
        )
        mw.reset()
        showInfo(
            f"Operazione completata: {result}"
        )
    except Exception as e:
        showCritical(
            f"Errore: {e}"
        )

action = QAction(
    "Arricchisci deck con IA",
    mw
)

action.triggered.connect(
    run_from_anki
)

mw.form.menuTools.addAction(
    action
)
```

---

## Cosa deve contenere questa prima lezione

Questa prima lezione non deve spiegare ancora tutti i dettagli delle API Anki.

Deve fissare l'architettura mentale:

```
non partire dall'add-on,
partire dalla pipeline.
```

Le API specifiche verranno trattate dopo.

---

## Regole pratiche

1. Lavorare sempre prima fuori da Anki.

2. Usare copie della collezione durante lo sviluppo.

3. Non modificare direttamente il database SQLite.

4. Separare sempre:

   * caricamento parole;
   * filtro frequenza;
   * generazione contenuti;
   * scrittura Anki;
   * report.

5. Non chiamare IA o servizi online prima di aver filtrato le parole.

6. Rendere esplicita la lingua.

7. Per tedesco e giapponese prevedere normalizzazione diversa.

8. Registrare nel log ogni parola saltata.

9. Produrre sempre un report finale.

10. Trasformare la pipeline in add-on solo quando serve davvero.

---

## Alcuni riferimenti

Writing Anki Add-ons - The anki Module  
https://addon-docs.ankiweb.net/the-anki-module.html

Writing Anki Add-ons - Editor Setup  
https://addon-docs.ankiweb.net/editor-setup.html

Writing Anki Add-ons - Add-on Config  
https://addon-docs.ankiweb.net/addon-config.html

Anki development documentation - pre-built Python wheels  
https://github.com/ankitects/anki/blob/main/docs/development.md

Anki Python API documentation  
https://dev-docs.ankiweb.net/en/latest/api-python-modules.html

read: 1
