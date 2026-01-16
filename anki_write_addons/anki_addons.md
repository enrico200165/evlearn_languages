
## Cos’è un add-on di Anki

Un add-on di Anki è un **modulo Python** che estende o modifica il comportamento dell’applicazione desktop di Anki.
Gli add-on consentono di:

* aggiungere voci di menu
* modificare l’interfaccia grafica
* automatizzare operazioni ripetitive
* interagire con mazzi, note e campi
* intercettare eventi (hook)

Un add-on **non è un plugin isolato**, ma viene caricato **dentro il processo di Anki** e ne condivide l’ambiente Python.

---

## Architettura generale di Anki (lato add-on)

### Linguaggio e stack

Anki Desktop è basato su:

* Python
* Qt (tramite PyQt / PyQt6)
* SQLite (collezione)

Gli add-on sono **script Python caricati dinamicamente** all’avvio di Anki.

---

### Dove risiedono gli add-on

Gli add-on sono collocati nella directory:

* Windows
  `%APPDATA%\Anki2\addons21\`

* Linux
  `~/.local/share/Anki2/addons21/`

* macOS
  `~/Library/Application Support/Anki2/addons21/`

Ogni add-on ha una **cartella propria**, identificata da:

* un ID numerico (se installato da AnkiWeb)
* oppure un nome arbitrario (per sviluppo locale)

---

## Struttura minima di un add-on

Struttura tipica:

```
my_addon/
    __init__.py
    config.json
    utils.py
    gui.py
```

Il file ****init**.py** è obbligatorio ed è il punto di ingresso.

---

## Ciclo di vita di un add-on

1. avvio di Anki
2. scansione directory addons21
3. import di ogni **init**.py
4. esecuzione del codice top-level
5. registrazione di hook, menu, azioni

Un errore in fase di import **disabilita l’add-on**.

---

## API fondamentali per add-on

Gli add-on interagiscono con Anki tramite moduli interni.

Import comuni:

```
from aqt import mw
from aqt.utils import showInfo, showCritical
from aqt.qt import QAction
```

Dove:

* `mw` è la Main Window di Anki
* `aqt` è il layer GUI
* `anki` è il layer logico (collezione, note, schedulazione)

---

## Aggiungere una voce di menu

### Concetto

Per estendere l’interfaccia, si aggiunge una QAction a un menu esistente.

---

### Esempio concettuale

```
from aqt import mw
from aqt.qt import QAction
from aqt.utils import showInfo

def on_click():
    showInfo("Add-on attivo")

action = QAction("Mia azione", mw)
action.triggered.connect(on_click)

mw.form.menuTools.addAction(action)
```

---

### Elementi chiave

* QAction rappresenta un comando UI
* `triggered.connect` lega evento a funzione
* `menuTools` è il menu Strumenti

---

## Interazione con la collezione

La collezione è accessibile tramite:

```
mw.col
```

Contiene:

* mazzi
* note
* modelli
* database SQLite

---

### Accedere alle note

Esempio concettuale:

```
for nid in mw.col.find_notes(""):
    note = mw.col.get_note(nid)
```

---

### Accedere ai campi

```
valore = note["Front"]
note["Back"] = "nuovo contenuto"
note.flush()
```

---

## Hook: intercettare eventi di Anki

### Cos’è un hook

Un hook è un punto di estensione che consente di:

* eseguire codice prima o dopo un evento
* modificare comportamenti standard

---

### Esempio di hook

```
from aqt import gui_hooks

def on_note_will_be_added(note, deck_id):
    pass

gui_hooks.note_will_be_added.append(on_note_will_be_added)
```

---

### Tipi di hook comuni

* apertura editor
* salvataggio nota
* risposta a una card
* caricamento collezione

---

## Interfacce grafiche negli add-on

### Uso di PyQt

Anki usa PyQt; le finestre personalizzate sono QWidget, QDialog, ecc.

Esempio concettuale:

```
from aqt.qt import QDialog, QVBoxLayout, QLabel

dlg = QDialog(mw)
layout = QVBoxLayout()
layout.addWidget(QLabel("Test"))
dlg.setLayout(layout)
dlg.exec()
```

---

### Buone pratiche GUI

* evitare finestre bloccanti inutili
* usare dialog modali solo se necessario
* mantenere interfacce semplici
* gestire correttamente chiusure ed eccezioni

---

## Configurazione dell’add-on

### File config.json

Anki supporta configurazioni JSON per add-on.

Esempio:

```
{
    "campo_origine": "Front",
    "campo_destinazione": "Back"
}
```

Accesso:

```
from aqt import mw
config = mw.addonManager.getConfig(__name__)
```

---

## Logging e debug

### Logging su file

È buona pratica creare un log locale:

```
import logging

logging.basicConfig(
    filename="addon.log",
    level=logging.INFO
)
```

---

### Debug degli errori

* usare la console di debug di Anki
* controllare Anki > Aiuto > Mostra log
* isolare il codice in moduli separati

---

## Compatibilità e versioni di Anki

Aspetti critici:

* Anki aggiorna frequentemente PyQt e API
* hook e nomi possono cambiare
* evitare API interne non documentate
* testare su versioni recenti

È consigliato:

* controllare la versione con `mw.appVersion`
* documentare la versione minima supportata

---

## Distribuzione dell’add-on

Modalità:

* cartella manuale (sviluppo)
* pacchetto zip
* pubblicazione su AnkiWeb

Per AnkiWeb sono richiesti:

* ID univoco
* descrizione
* compatibilità dichiarata
* assenza di codice dannoso

---

## Limiti e responsabilità

Un add-on:

* può corrompere la collezione se mal progettato
* gira con pieni permessi dell’utente
* deve gestire con attenzione operazioni di scrittura
* non deve bloccare il thread UI

---

## Conclusione

La scrittura di add-on per Anki richiede:

* buona conoscenza di Python
* comprensione dell’architettura di Anki
* attenzione alla stabilità
* uso corretto degli hook
* separazione tra logica e interfaccia

Gli add-on consentono di trasformare Anki in uno **strumento altamente personalizzato**, soprattutto in ambito didattico, linguistico e tecnico.

---

## Alcuni riferimenti

Anki Add-on Documentation
[https://addon-docs.ankiweb.net/](https://addon-docs.ankiweb.net/)

Anki GitHub Repository
[https://github.com/ankitects/anki](https://github.com/ankitects/anki)

Anki Add-ons Portal
[https://ankiweb.net/shared/addons](https://ankiweb.net/shared/addons)

PyQt Documentation
[https://www.riverbankcomputing.com/static/Docs/PyQt6/](https://www.riverbankcomputing.com/static/Docs/PyQt6/)


---  

SEZIONE AGGIUNTIVA: setup ambiente di sviluppo con Visual Studio Code

1. Obiettivo dell’ambiente di sviluppo
   Creare un progetto locale dell’add-on in una cartella separata, ottenere:

* completamento automatico e type hints delle API Anki
* linting e type checking (opzionale ma molto utile)
* workflow rapido di test in Anki (copia o symlink nella cartella addons21)

Le add-on docs indicano che è possibile usare Visual Studio Code, anche se viene citato PyCharm come soluzione “più comoda” in alcuni casi. [https://addon-docs.ankiweb.net/editor-setup.html](https://addon-docs.ankiweb.net/editor-setup.html) ([addon-docs.ankiweb.net][1])

2. Prerequisiti

* Visual Studio Code installato
* Estensione VS Code “Python” (Microsoft)
* Python 64-bit installato localmente (serve per avere type hints e strumenti; l’add-on però viene eseguito dentro Anki, non nel venv) [https://addon-docs.ankiweb.net/editor-setup.html](https://addon-docs.ankiweb.net/editor-setup.html) ([addon-docs.ankiweb.net][1])

3. Creare un progetto add-on in VS Code
   3.1 Creare una cartella di lavoro, ad esempio:

* D:\dev\anki_addons\mio_addon\

3.2 Creare struttura minima:

* mio_addon\

  * **init**.py
  * config.json (opzionale)
  * README.txt (opzionale)

3.3 Aprire la cartella in VS Code.

4. Creare un ambiente Python per completamento e type hints (consigliato)
   Scopo: installare i pacchetti “aqt” e “anki” (bundle Anki pubblicato su PyPI) solo per:

* import risolti
* autocompletamento
* mypy (facoltativo)

Le add-on docs mostrano un esempio di installazione con:

* mypy
* aqt[qt6]
  [https://addon-docs.ankiweb.net/editor-setup.html](https://addon-docs.ankiweb.net/editor-setup.html) ([addon-docs.ankiweb.net][1])

Procedura tipica (da terminale di VS Code nella cartella progetto):
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install mypy "aqt[qt6]"

Nota importante:

* l’add-on non va eseguito con “Run Python File” di VS Code: deve essere caricato da Anki. [https://addon-docs.ankiweb.net/editor-setup.html](https://addon-docs.ankiweb.net/editor-setup.html) ([addon-docs.ankiweb.net][1])

5. Selezionare l’interprete in VS Code
   In VS Code:

* Command Palette
* “Python: Select Interpreter”
* selezionare .venv

6. Impostazioni consigliate (facoltative ma utili)
   6.1 Type checking (esempio concettuale di settings.json)
   Creare:

* .vscode\settings.json

Contenuto tipico:
{
"python.defaultInterpreterPath": "${workspaceFolder}\.venv\Scripts\python.exe",
"python.analysis.typeCheckingMode": "basic",
"python.analysis.autoImportCompletions": true
}

7. Collegare la cartella di sviluppo alla cartella addons21 di Anki
   Opzioni:

* copiare la cartella mio_addon dentro addons21
* su macOS/Linux creare un symlink (workflow spesso preferibile)

Le add-on docs descrivono copia o symlink nella cartella degli add-on. [https://addon-docs.ankiweb.net/addon-folders.html](https://addon-docs.ankiweb.net/addon-folders.html) ([addon-docs.ankiweb.net][2])

SEZIONE AGGIUNTIVA: debugging da Visual Studio Code

Qui conviene distinguere 3 livelli, dal più semplice (quello che funziona sempre) al più “IDE-like”.

LIVELLO 1 (consigliato): vedere stdout/stderr e warning mentre Anki gira

1. Perché serve
   Anki è una GUI: print() su stdout non è visibile di default. Le add-on docs consigliano di rendere visibile la console durante lo sviluppo, anche perché Anki stampa warning di deprecazione utili. [https://addon-docs.ankiweb.net/console-output.html](https://addon-docs.ankiweb.net/console-output.html) ([addon-docs.ankiweb.net][3])

2. Come mostrare la console
   2.1 Windows
   Avviare Anki con il launcher “console” in modo da aprire una finestra console separata e vedere print() e warning.
   Le docs citano “anki-console.bat” e percorsi tipici. [https://addon-docs.ankiweb.net/console-output.html](https://addon-docs.ankiweb.net/console-output.html) ([addon-docs.ankiweb.net][3])
   Nota: sulle versioni più recenti di Anki su Windows il nome può essere cambiato in “anki-console.exe” (c’è una discussione di aggiornamento documentazione). [https://github.com/ankitects/anki-manual/issues/435](https://github.com/ankitects/anki-manual/issues/435) ([GitHub][4])

2.2 macOS / Linux
Avviare Anki da terminale per vedere stdout/stderr (comandi indicati nelle docs). [https://addon-docs.ankiweb.net/console-output.html](https://addon-docs.ankiweb.net/console-output.html) ([addon-docs.ankiweb.net][3])

3. In VS Code
   Aprire un terminale integrato e lanciare Anki “console”.
   Vantaggio: output visibile direttamente in VS Code, senza cambiare strumenti.
   Limitazione: non è ancora debugging con breakpoint, ma è già molto efficace.

4. Buone pratiche

* evitare print massivi in loop: rallenta Anki, anche se la console non è mostrata. [https://addon-docs.ankiweb.net/console-output.html](https://addon-docs.ankiweb.net/console-output.html) ([addon-docs.ankiweb.net][3])

LIVELLO 2: strumenti di debug interni ad Anki (REPL e pdb)

1. Debug Console (REPL) di Anki
   Anki include una console interattiva per eseguire codice e ispezionare oggetti (mw, reviewer, ecc.). [https://addon-docs.ankiweb.net/debugging.html](https://addon-docs.ankiweb.net/debugging.html) ([addon-docs.ankiweb.net][5])
   Uso tipico:

* aprire la Debug Console
* stampare oggetti e proprietà
* provare snippet di codice senza riavviare l’app

2. PDB (debugger testuale)
   Le docs indicano che, su Linux o eseguendo Anki da sorgenti, è possibile attivare pdb inserendo nel codice:
   from aqt.qt import debug; debug()
   Oppure impostando la variabile d’ambiente DEBUG=1 per entrare nel debugger su eccezioni non gestite. [https://addon-docs.ankiweb.net/debugging.html](https://addon-docs.ankiweb.net/debugging.html) ([addon-docs.ankiweb.net][5])

Questo livello è molto utile perché:

* consente stop “interattivi” nel punto desiderato
* non richiede integrazione IDE
* funziona anche quando il debug “grafico” è complesso da ottenere

LIVELLO 3: debugging con breakpoint in VS Code (approccio “attach”)
Questo è il risultato più simile al debugging classico (F5, breakpoints, step, variabili). La documentazione generale di VS Code spiega i concetti di configurazioni di debug e attach. [https://code.visualstudio.com/docs/debugtest/debugging](https://code.visualstudio.com/docs/debugtest/debugging) ([Visual Studio Code][6])

Idea di base:

* far partire Anki normalmente
* far aprire una porta di debug Python dentro il processo Anki
* collegare VS Code con una configurazione “Python: Attach”

Avvertenza tecnica (importante):

* per usare questo approccio serve che il modulo “debugpy” sia disponibile nell’ambiente Python usato da Anki oppure che venga incluso/gestito dall’add-on stesso.
* su installazioni standard, non è garantito che debugpy sia disponibile senza interventi; per questo è da considerare “avanzato”.

Esempio concettuale (da inserire temporaneamente nell’add-on, solo per sviluppo):
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()

Poi creare una configurazione in .vscode/launch.json (concetto):
{
"version": "0.2.0",
"configurations": [
{
"name": "Attach ad Anki (debugpy)",
"type": "python",
"request": "attach",
"connect": {
"host": "127.0.0.1",
"port": 5678
}
}
]
}

Uso:

* avviare Anki
* attivare il punto in cui l’add-on esegue debugpy.listen()
* avviare “Attach ad Anki (debugpy)” da VS Code
* mettere breakpoint nel codice dell’add-on

Se l’obiettivo è fare debugging soprattutto del frontend (webview)
Le docs indicano la possibilità di abilitare il remote debugging di QtWebEngine impostando:

* QTWEBENGINE_REMOTE_DEBUGGING=8080
  e poi aprire:
* [http://localhost:8080](http://localhost:8080)
  per ispezionare le webview in Chrome.
  [https://addon-docs.ankiweb.net/debugging.html](https://addon-docs.ankiweb.net/debugging.html) ([addon-docs.ankiweb.net][5])

## Alcuni riferimenti

Writing Anki Add-ons – Editor Setup
[https://addon-docs.ankiweb.net/editor-setup.html](https://addon-docs.ankiweb.net/editor-setup.html)

Writing Anki Add-ons – Console Output
[https://addon-docs.ankiweb.net/console-output.html](https://addon-docs.ankiweb.net/console-output.html)

Writing Anki Add-ons – Debugging
[https://addon-docs.ankiweb.net/debugging.html](https://addon-docs.ankiweb.net/debugging.html)

Visual Studio Code – Debugging documentation
[https://code.visualstudio.com/docs/debugtest/debugging](https://code.visualstudio.com/docs/debugtest/debugging)

Anki manual issue su anki-console.exe (Windows recenti)
[https://github.com/ankitects/anki-manual/issues/435](https://github.com/ankitects/anki-manual/issues/435)

[1]: https://addon-docs.ankiweb.net/editor-setup.html "Editor Setup - Writing Anki Add-ons"
[2]: https://addon-docs.ankiweb.net/addon-folders.html?utm_source=chatgpt.com "Add-on Folders - Writing Anki Add-ons"
[3]: https://addon-docs.ankiweb.net/console-output.html "Console Output - Writing Anki Add-ons"
[4]: https://github.com/ankitects/anki-manual/issues/435?utm_source=chatgpt.com "Add new anki-console location (for post-25.07) · Issue #435"
[5]: https://addon-docs.ankiweb.net/debugging.html "Debugging - Writing Anki Add-ons"
[6]: https://code.visualstudio.com/docs/debugtest/debugging "Debug code with Visual Studio Code"

---  

SVILUPPARE UN ADD-ON COMPLETO PASSO PASSO

Obiettivo
Realizzare un add-on semplice ma “completo”: aggiungere una voce di menu, aprire una finestra, leggere una configurazione, eseguire un’azione sulla collezione, gestire errori e logging.

Passo 0: preparare una copia di sicurezza
Prima di fare test che scrivono nella collezione, creare un backup (Anki ha backup automatici, ma è preferibile fare anche una copia manuale del profilo o almeno lavorare su un profilo di test).

Passo 1: creare la cartella dell’add-on
Creare una cartella dentro addons21, ad esempio:
my_first_addon/

Dentro creare almeno:
my_first_addon/
**init**.py

Passo 2: aggiungere una voce nel menu Strumenti
Scrivere in **init**.py:

```
from aqt import mw
from aqt.qt import QAction
from aqt.utils import showInfo

def _hello() -> None:
    showInfo("Add-on caricato e funzionante.")

action = QAction("My First Add-on: Hello", mw)
action.triggered.connect(_hello)
mw.form.menuTools.addAction(action)
```

Riavviare Anki, poi aprire Strumenti e verificare la voce.

Passo 3: introdurre una struttura “a moduli” (pulizia e manutenibilità)
Evitare di mettere tutto in **init**.py. Creare:

```
my_first_addon/
    __init__.py
    gui.py
    logic.py
    logging_utils.py
```

Esempio di **init**.py minimale:

```
from aqt import mw
from aqt.qt import QAction
from .gui import open_main_dialog

action = QAction("My First Add-on: Finestra", mw)
action.triggered.connect(open_main_dialog)
mw.form.menuTools.addAction(action)
```

Passo 4: creare una finestra (QDialog) con un’azione reale
Esempio gui.py:

```
from aqt import mw
from aqt.qt import QDialog, QVBoxLayout, QLabel, QPushButton
from aqt.utils import showCritical
from .logic import count_notes
from .logging_utils import log_line

def open_main_dialog() -> None:
    try:
        dlg = QDialog(mw)
        dlg.setWindowTitle("My First Add-on")

        layout = QVBoxLayout()
        label = QLabel("Eseguire una semplice operazione sulla collezione.")
        btn = QPushButton("Contare note (query vuota)")

        def _on_click() -> None:
            try:
                n = count_notes("")
                log_line(f"count_notes: {n}")
                label.setText(f"Numero note trovate: {n}")
            except Exception as e:
                log_line(f"ERRORE count_notes: {e}")
                showCritical(f"Errore: {e}")

        btn.clicked.connect(_on_click)

        layout.addWidget(label)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec()
    except Exception as e:
        log_line(f"ERRORE open_main_dialog: {e}")
        showCritical(f"Errore add-on: {e}")
```

Esempio logic.py:

```
from aqt import mw

def count_notes(query: str) -> int:
    nids = mw.col.find_notes(query)
    return len(nids)
```

Passo 5: aggiungere logging su file
Esempio logging_utils.py (log minimale, non invasivo):

```
import os
import datetime

ADDON_LOG = "my_first_addon.log"

def _addon_dir() -> str:
    return os.path.dirname(__file__)

def _log_path() -> str:
    return os.path.join(_addon_dir(), ADDON_LOG)

def log_line(message: str) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}\n"
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
```

Passo 6: usare la progress bar per operazioni pesanti
Se si fa un’operazione lunga (import, scansioni, modifiche di massa), usare:
mw.progress.start()
...
mw.progress.finish()
e, al termine, aggiornare la UI con:
mw.reset()

Passo 7: aggiungere configurazione (facoltativo ma tipico)
Creare config.json (semplice):

```
{
    "default_query": ""
}
```

Leggere config con:
cfg = mw.addonManager.getConfig(**name**)
Oppure gestire un file JSON interno all’add-on (approccio semplice e controllabile).

Passo 8: checklist di “add-on pronto”

* nessuna eccezione non gestita in import (fase di caricamento)
* funzioni principali protette con try/except e log
* operazioni di scrittura fatte in modo atomico e con UI reset
* eventuale profilo di test per sviluppo

ANALIZZARE UN ADD-ON REALE ESISTENTE

Obiettivo
Imparare “come si fa davvero” leggendo un add-on esistente e ricostruendo:

* struttura
* entry point
* pattern usati
* interazione con GUI e collezione
* compatibilità e scelte progettuali

Metodo pratico (ripetibile su qualunque add-on)

1. Identificare la cartella dell’add-on
   Dentro addons21 individuare la cartella (ID numerico o nome).

2. Leggere **init**.py per capire il punto di ingresso
   Cercare subito:

* aggiunte a menu (menuTools, menuEdit, ecc.)
* registrazioni hook (gui_hooks.*.append)
* monkey patch (override di funzioni Anki, da trattare con cautela)
* import di moduli interni dell’add-on

3. Mappare la struttura dei file
   Tipicamente si trovano:

* gui.py (dialog, azioni UI)
* models.py o data.py (strutture dati)
* services.py (logica e operazioni)
* config e migrazioni (gestione impostazioni)

4. Individuare il flusso principale (entry -> azione)
   Costruire mentalmente la catena:

* menu/hook chiama funzione A
* A apre una finestra o avvia una procedura
* la procedura usa mw.col per leggere/scrivere

5. Capire come gestisce il “tempo lungo”
   Controllare se usa:

* mw.progress
* task in background (in alcune versioni Anki ha utilità per task asincroni)
* blocco UI (da evitare per operazioni pesanti)

6. Valutare robustezza ed error handling
   Verificare se:

* usa showCritical/showInfo
* scrive log su file
* valida input dell’utente (percorsi file, campi, ecc.)

7. Verificare API usate e compatibilità
   Cercare:

* import di funzioni interne (rischio di rottura con update)
* commenti su versioni minime supportate
* uso di hook recenti (migliore rispetto a patch invasive)

8. Esercizio didattico utile
   Scegliere una feature piccola dell’add-on (per esempio “aggiungere un comando al menu” o “modificare un campo nota”) e riscriverla in un proprio add-on minimale.
   Questo consente di:

* isolare l’idea
* ridurre dipendenze
* apprendere i punti critici (salvataggio note, refresh UI, ecc.)

COSTRUIRE UN ADD-ON DIDATTICO PER IMPORTAZIONE AUTOMATICA

Obiettivo didattico
Creare un add-on che importi automaticamente note da un file (CSV o TSV) e le inserisca in un mazzo, scegliendo:

* mazzo di destinazione
* tipo di nota (note type)
* mappatura colonne -> campi
* comportamento su righe incomplete
* anteprima e report finale

Scenario tipico
File TSV con due colonne:

* colonna 1: Front
* colonna 2: Back

Struttura dell’add-on (consigliata)
didactic_importer/
**init**.py
gui.py
importer.py
logging_utils.py

Parte 1: entry point (menu)
**init**.py:

```
from aqt import mw
from aqt.qt import QAction
from .gui import open_import_dialog

action = QAction("Didactic Importer: Importa file", mw)
action.triggered.connect(open_import_dialog)
mw.form.menuTools.addAction(action)
```

Parte 2: GUI essenziale (scelta file, mazzo, note type, mappatura campi)
gui.py (versione semplificata ma funzionale come base):

```
from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QComboBox, QListWidget, QListWidgetItem
)
from aqt.utils import showCritical, showInfo
from .importer import import_tsv
from .logging_utils import log_line

def open_import_dialog() -> None:
    dlg = QDialog(mw)
    dlg.setWindowTitle("Didactic Importer")

    layout = QVBoxLayout()

    path_label = QLabel("File: (nessuno)")
    btn_pick = QPushButton("Selezionare file TSV")
    decks_combo = QComboBox()
    models_combo = QComboBox()
    fields_list = QListWidget()
    btn_run = QPushButton("Eseguire import")
    btn_run.setEnabled(False)

    layout.addWidget(path_label)
    layout.addWidget(btn_pick)
    layout.addWidget(QLabel("Mazzo di destinazione:"))
    layout.addWidget(decks_combo)
    layout.addWidget(QLabel("Tipo di nota:"))
    layout.addWidget(models_combo)
    layout.addWidget(QLabel("Campi del tipo di nota (ordine):"))
    layout.addWidget(fields_list)
    layout.addWidget(btn_run)

    dlg.setLayout(layout)

    state = {"path": None}

    def _load_decks() -> None:
        decks_combo.clear()
        for d in mw.col.decks.all_names_and_ids():
            decks_combo.addItem(d.name, d.id)

    def _load_models() -> None:
        models_combo.clear()
        for m in mw.col.models.all():
            models_combo.addItem(m["name"], m["id"])

    def _load_fields_for_selected_model() -> None:
        fields_list.clear()
        mid = models_combo.currentData()
        if mid is None:
            return
        model = mw.col.models.get(mid)
        for f in model["flds"]:
            item = QListWidgetItem(f["name"])
            fields_list.addItem(item)

    def _pick_file() -> None:
        try:
            path, _ = QFileDialog.getOpenFileName(
                dlg,
                "Selezionare file TSV",
                "",
                "TSV (*.tsv);;Tutti i file (*.*)"
            )
            if not path:
                return
            state["path"] = path
            path_label.setText(f"File: {path}")
            btn_run.setEnabled(True)
        except Exception as e:
            log_line(f"ERRORE pick_file: {e}")
            showCritical(f"Errore: {e}")

    def _run_import() -> None:
        try:
            path = state["path"]
            if not path:
                showCritical("Selezionare prima un file.")
                return

            deck_id = decks_combo.currentData()
            mid = models_combo.currentData()
            if deck_id is None or mid is None:
                showCritical("Selezionare mazzo e tipo di nota.")
                return

            result = import_tsv(
                path=path,
                deck_id=int(deck_id),
                model_id=int(mid),
                strict_columns=False
            )

            showInfo(
                "Import completato.\n"
                f"Righe lette: {result['rows']}\n"
                f"Note create: {result['created']}\n"
                f"Saltate: {result['skipped']}\n"
                f"Errori: {result['errors']}"
            )
        except Exception as e:
            log_line(f"ERRORE run_import: {e}")
            showCritical(f"Errore import: {e}")

    btn_pick.clicked.connect(_pick_file)
    btn_run.clicked.connect(_run_import)
    models_combo.currentIndexChanged.connect(_load_fields_for_selected_model)

    _load_decks()
    _load_models()
    _load_fields_for_selected_model()

    dlg.exec()
```

Parte 3: import reale (lettura TSV, creazione note)
importer.py (base robusta, con log e progress):

```
import csv
from aqt import mw
from aqt.utils import showCritical
from .logging_utils import log_line

def import_tsv(path: str, deck_id: int, model_id: int, strict_columns: bool) -> dict:
    result = {"rows": 0, "created": 0, "skipped": 0, "errors": 0}

    model = mw.col.models.get(model_id)
    if not model:
        raise RuntimeError("Tipo di nota non trovato.")

    fields = [f["name"] for f in model["flds"]]
    if len(fields) == 0:
        raise RuntimeError("Il tipo di nota non ha campi.")

    mw.progress.start(label="Import in corso...", immediate=True)

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                result["rows"] += 1

                if not row or all((c.strip() == "" for c in row)):
                    result["skipped"] += 1
                    continue

                if strict_columns and len(row) != len(fields):
                    log_line(f"Riga {result['rows']} saltata: colonne {len(row)} != campi {len(fields)}")
                    result["skipped"] += 1
                    continue

                try:
                    note = mw.col.new_note(model)
                    for i, field_name in enumerate(fields):
                        if i < len(row):
                            note[field_name] = row[i].strip()
                        else:
                            note[field_name] = ""

                    if note.dupeOrEmpty():
                        result["skipped"] += 1
                        continue

                    mw.col.add_note(note, deck_id)
                    result["created"] += 1
                except Exception as e:
                    result["errors"] += 1
                    log_line(f"Errore riga {result['rows']}: {e}")

        mw.reset()
        return result
    finally:
        mw.progress.finish()
```

Parte 4: logging_utils.py (come nella sezione precedente)
Riutilizzare lo stesso logging_utils.py mostrato sopra, adattando il nome file log.

Estensioni didattiche consigliate (progressive)

1. Anteprima import
   Leggere le prime N righe e mostrarle in tabella nella finestra prima di importare.

2. Mappatura colonne -> campi
   Invece di imporre “ordine fisso”, creare una lista di combo box, una per ogni campo, che permetta di selezionare quale colonna assegnare.

3. Gestione duplicati
   Opzioni:

* saltare se duplicato
* aggiornare nota esistente (più complesso: serve trovare nota e modificarla con criterio)

4. Validazioni

* impedire import se mancano campi obbligatori
* segnalare righe con colonne insufficienti

5. Report finale su file
   Scrivere un file CSV con righe “OK / SKIPPED / ERROR” e motivazione.

6. Modalità “profilo di test”
   Importare in un mazzo di test selezionabile rapidamente, per evitare danni su mazzi reali.

Checklist qualità e sicurezza (import)

* import in un profilo Anki di test
* log dettagliato per righe problematiche
* progress bar attiva su file grandi
* mw.reset() al termine
* evitare blocchi UI prolungati senza feedback

Se si desidera, nel prossimo passo è possibile trasformare il “Didactic Importer” in un add-on più “da produzione” con:

* scelta delimitatore (CSV/TSV)
* rilevamento automatico intestazione
* mappatura grafica colonne-campi
* import incrementale e annullabile (più avanzato)

