
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


![Image](https://raw.githubusercontent.com/Arthur-Milchior/anki-enhance-main-window/master/example.png)

![Image](https://us1.discourse-cdn.com/flex002/uploads/anki2/original/2X/7/723aeb0828a609c698cb5fa205b5570851ce4107.png)

![Image](https://raw.github.com/AnKing-Memberships/advanced-browser/master/docs/screenshot_info.png)

![Image](https://us1.discourse-cdn.com/flex002/uploads/anki2/original/2X/5/5e9104d5b0d1529db723d799e623ad712e43a268.png)


# sezione: estensioni didattiche
Di seguito una riscrittura con “svolgimento completo” delle implementazioni delle estensioni, spiegando in dettaglio ciò che non è Python standard: API di Anki (aqt/anki), PyQt (Qt widgets, segnali), ciclo di vita dell’add-on, e punti critici (progress, reset, collezione).

La sezione è pensata per essere incollata in una dispensa. Il codice è mostrato con indentazione di 4 spazi (senza backticks).

======================================================================
CONCETTI NON STANDARD: API DI ANKI E PyQt (PRIMA DI CODIFICARE)
===============================================================

1. Cos’è mw e perché è centrale

* In un add-on, “mw” è l’oggetto Main Window di Anki.
* È fornito da aqt (layer GUI di Anki).
* Permette accesso:

  * a mw.form (componenti UI principali: menu, toolbar, ecc.)
  * a mw.col (la collezione: database e logica di note/mazzi/modelli)

Import tipico:
from aqt import mw

2. mw.col: la “collezione”

* mw.col è l’oggetto Collezione di Anki.
* Contiene i metodi per:

  * mazzi (decks)
  * modelli/tipi di nota (models)
  * note (notes)
  * aggiunta note al mazzo (add_note)

Esempi:

* Ottenere elenco mazzi:
  mw.col.decks.all_names_and_ids()
  Restituisce una lista di oggetti con proprietà name e id.

* Ottenere tipi di nota:
  mw.col.models.all()
  Restituisce lista di dict; tipicamente:
  {"name": "...", "id": ...}

* Ottenere un modello specifico:
  mw.col.models.get(model_id)
  Restituisce dict del modello, con chiave "flds" per i campi.

* Creare una nota nuova basata su un modello:
  note = mw.col.new_note(model)
  “note” è un oggetto Note che espone l’accesso ai campi con sintassi:
  note["Front"] = "testo"

* Aggiungere la nota a un mazzo:
  mw.col.add_note(note, deck_id)

3. mw.reset: aggiornare UI e stato

* Dopo modifiche in massa (aggiunta note), chiamare:
  mw.reset()
  per far ricaricare ad Anki UI e contatori.
* È una chiamata “Anki-specific”: serve a non lasciare l’interfaccia in uno stato “vecchio”.

4. Progress bar di Anki

* In operazioni lunghe, usare:
  mw.progress.start(...)
  mw.progress.finish()
  per mostrare feedback e ridurre l’impressione di blocco.
* È specifico di Anki (aqt), non di Python.

5. PyQt: concetti essenziali usati negli add-on

* QWidget / QDialog: finestre e dialog.
* Layout (QVBoxLayout, QHBoxLayout): posizionamento.
* Controlli: QLabel, QPushButton, QComboBox, QCheckBox, QTableWidget.
* Segnali e slot:

  * un bottone emette un segnale “clicked”
  * si collega il segnale a una funzione Python con:
    button.clicked.connect(funzione)

6. Threading

* Questa implementazione resta sul thread UI per semplicità didattica.
* Per file molto grandi sarebbe opportuno spostare l’import in task asincroni; qui non viene fatto per non aumentare complessità.

======================================================================
OBIETTIVO: IMPLEMENTARE TUTTE LE ESTENSIONI DIDATTICHE
======================================================

Estensioni implementate:

1. mappatura colonne → campi con combo box
2. rilevamento automatico intestazione + auto-mappatura
3. modalità “solo anteprima”
4. import in mazzo di test (opzione)
5. report CSV finale riga-per-riga
6. supporto UTF-8 e fallback di lettura

Il progetto add-on completo (cartella in addons21):

```
didactic_importer_pro/
    __init__.py
    gui.py
    preview.py
    importer.py
    logging_utils.py
    config.json
```

======================================================================
FILE: config.json
=================

```
{
    "default_has_header": true,
    "default_preview_only": true,
    "default_strict_columns": false,
    "default_skip_empty_rows": true,
    "default_force_test_deck": false,
    "test_deck_name": "TEST_IMPORT",
    "default_preview_rows": 15,
    "input_encoding_primary": "utf-8",
    "input_encoding_fallback": "latin-1",
    "report_encoding": "utf-8"
}
```

Spiegazione (non standard):

* config.json viene letto tramite mw.addonManager.getConfig(**name**), meccanismo specifico Anki add-on.
* **name** in un add-on punta al modulo; Anki lo usa come chiave di configurazione.

======================================================================
FILE: **init**.py (ENTRY POINT)
===============================

Concetti Anki non standard:

* QAction è Qt (PyQt), serve a creare una voce di menu.
* mw.form.menuTools è il menu “Strumenti” già esistente nella finestra principale.

Codice:

```
from aqt import mw
from aqt.qt import QAction
from .gui import open_import_dialog

action = QAction("Didactic Importer Pro: Importa CSV/TSV", mw)
action.triggered.connect(open_import_dialog)
mw.form.menuTools.addAction(action)
```

======================================================================
FILE: logging_utils.py
======================

Scopo: logging locale non bloccante.

```
import os
import datetime

LOG_NAME = "didactic_importer_pro.log"

def _addon_dir() -> str:
    return os.path.dirname(__file__)

def log_line(message: str) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}\n"
    try:
        with open(os.path.join(_addon_dir(), LOG_NAME), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
```

======================================================================
FILE: preview.py (LETTURA + ANTEPRIMA + HEADER)
===============================================

Qui non c’è API Anki: è “solo Python”, ma si implementa la parte didattica:

* lettura robusta con fallback encoding
* rilevamento header (se abilitato)
* restituzione dati a gui.py per tabella

  import csv
  from typing import List, Optional, Tuple

  def read_preview(
  path: str,
  delimiter: str,
  has_header: bool,
  max_rows: int,
  enc_primary: str,
  enc_fallback: str
  ) -> Tuple[Optional[List[str]], List[List[str]], int]:
  header: Optional[List[str]] = None
  rows: List[List[str]] = []
  max_cols = 0

  ```
    def _open_with_fallback():
        try:
            return open(path, "r", encoding=enc_primary, newline="")
        except UnicodeDecodeError:
            return open(path, "r", encoding=enc_fallback, newline="")

    with _open_with_fallback() as f:
        reader = csv.reader(f, delimiter=delimiter)

        for i, row in enumerate(reader):
            cleaned = [c.strip() for c in row]
            max_cols = max(max_cols, len(cleaned))

            if i == 0 and has_header:
                header = cleaned
                continue

            rows.append(cleaned)
            if len(rows) >= max_rows:
                break

    return header, rows, max_cols
  ```

======================================================================
FILE: importer.py (IMPORT + REPORT + STRICT + TEST DECK)
========================================================

Qui la parte non standard è “Anki API”:

* mw.col.models.get(model_id)
* mw.col.new_note(model)
* note[field] = value (accesso campi Note)
* note.dupeOrEmpty() (utility Anki)
* mw.col.add_note(note, deck_id)
* mw.progress.start/finish
* mw.reset()

Inoltre:

* report riga-per-riga (CSV)
* lettura file con encoding fallback
* modalità preview-only implementata come esecuzione senza scrittura

  import csv
  import os
  import datetime
  from typing import Dict, Optional, List, Tuple

  from aqt import mw
  from .logging_utils import log_line

  def _addon_dir() -> str:
  return os.path.dirname(**file**)

  def *make_report_path() -> str:
  ts = datetime.datetime.now().strftime("%Y%m%d*%H%M%S")
  return os.path.join(*addon_dir(), f"import_report*{ts}.csv")

  def _open_with_fallback(path: str, enc_primary: str, enc_fallback: str):
  try:
  return open(path, "r", encoding=enc_primary, newline="")
  except UnicodeDecodeError:
  return open(path, "r", encoding=enc_fallback, newline="")

  def import_file(
  path: str,
  delimiter: str,
  has_header: bool,
  preview_only: bool,
  deck_id: int,
  model_id: int,
  field_to_col: Dict[str, Optional[int]],
  strict_columns: bool,
  skip_empty_rows: bool,
  enc_primary: str,
  enc_fallback: str,
  report_encoding: str
  ) -> dict:
  result = {
  "rows_total_in_file": 0,
  "rows_processed": 0,
  "created": 0,
  "skipped": 0,
  "errors": 0,
  "report_path": None
  }

  ```
    model = mw.col.models.get(model_id)
    if not model:
        raise RuntimeError("Tipo di nota non valido.")

    fields = [f["name"] for f in model["flds"]]
    if not fields:
        raise RuntimeError("Il tipo di nota non contiene campi.")

    report_path = _make_report_path()
    result["report_path"] = report_path

    mw.progress.start(label="Import in corso...", immediate=True)

    try:
        with _open_with_fallback(path, enc_primary, enc_fallback) as f_in, \
             open(report_path, "w", encoding=report_encoding, newline="") as f_rep:

            reader = csv.reader(f_in, delimiter=delimiter)
            rep = csv.writer(f_rep, delimiter=",")

            rep.writerow(["line_no", "status", "reason", "raw"])

            line_no = 0

            for row in reader:
                line_no += 1
                result["rows_total_in_file"] += 1

                cleaned = [c.strip() for c in row]
                raw_join = " | ".join(cleaned)

                if line_no == 1 and has_header:
                    rep.writerow([line_no, "SKIPPED", "header", raw_join])
                    continue

                result["rows_processed"] += 1

                if skip_empty_rows and (not cleaned or all(c == "" for c in cleaned)):
                    result["skipped"] += 1
                    rep.writerow([line_no, "SKIPPED", "empty_row", raw_join])
                    continue

                if strict_columns:
                    ok = True
                    for field_name in fields:
                        idx = field_to_col.get(field_name, None)
                        if idx is None:
                            continue
                        if idx >= len(cleaned):
                            ok = False
                            break
                    if not ok:
                        result["skipped"] += 1
                        rep.writerow([line_no, "SKIPPED", "missing_columns_strict", raw_join])
                        continue

                if preview_only:
                    result["skipped"] += 1
                    rep.writerow([line_no, "SKIPPED", "preview_only_no_write", raw_join])
                    continue

                try:
                    note = mw.col.new_note(model)

                    for field_name in fields:
                        idx = field_to_col.get(field_name, None)

                        if idx is None:
                            note[field_name] = ""
                            continue

                        if idx < len(cleaned):
                            note[field_name] = cleaned[idx]
                        else:
                            note[field_name] = ""

                    if note.dupeOrEmpty():
                        result["skipped"] += 1
                        rep.writerow([line_no, "SKIPPED", "dupe_or_empty", raw_join])
                        continue

                    mw.col.add_note(note, deck_id)
                    result["created"] += 1
                    rep.writerow([line_no, "CREATED", "ok", raw_join])

                except Exception as e:
                    result["errors"] += 1
                    log_line(f"Errore riga {line_no}: {e}")
                    rep.writerow([line_no, "ERROR", str(e), raw_join])

        mw.reset()
        return result

    finally:
        mw.progress.finish()
  ```

======================================================================
FILE: gui.py (PyQt + API Anki: MENU, SELEZIONE DECK/MODEL, TABLE, MAPPING)
==========================================================================

Qui le parti non standard sono molte:

* PyQt: QDialog, layout, controlli, segnali
* API Anki: mw.col.decks, mw.col.models
* Add-on config: mw.addonManager.getConfig(**name**)

Obiettivi:

* selezione file
* opzioni (header, preview-only, strict, skip empty, force test deck)
* anteprima tabellare (QTableWidget)
* mappatura dinamica campi→colonne (combo box per ogni campo)
* auto-mappatura basata su header
* import con report

  from typing import Optional, Dict, List

  from aqt import mw
  from aqt.qt import (
  QDialog, QVBoxLayout, QHBoxLayout,
  QLabel, QPushButton, QFileDialog,
  QComboBox, QCheckBox,
  QTableWidget, QTableWidgetItem,
  QGroupBox, QWidget
  )
  from aqt.utils import showCritical, showInfo

  from .logging_utils import log_line
  from .preview import read_preview
  from .importer import import_file

  def open_import_dialog() -> None:
  dlg = QDialog(mw)
  dlg.setWindowTitle("Didactic Importer Pro")

  ```
    root = QVBoxLayout()
    dlg.setLayout(root)

    try:
        cfg = mw.addonManager.getConfig(__name__)
    except Exception:
        cfg = {}

    default_has_header = bool(cfg.get("default_has_header", True))
    default_preview_only = bool(cfg.get("default_preview_only", True))
    default_strict = bool(cfg.get("default_strict_columns", False))
    default_skip_empty = bool(cfg.get("default_skip_empty_rows", True))
    default_force_test = bool(cfg.get("default_force_test_deck", False))
    test_deck_name = str(cfg.get("test_deck_name", "TEST_IMPORT"))
    preview_rows = int(cfg.get("default_preview_rows", 15))
    enc_primary = str(cfg.get("input_encoding_primary", "utf-8"))
    enc_fallback = str(cfg.get("input_encoding_fallback", "latin-1"))
    report_encoding = str(cfg.get("report_encoding", "utf-8"))

    state = {
        "path": None,
        "delimiter": "\t",
        "header": None,
        "max_cols": 0,
        "col_names": []
    }

    lbl_path = QLabel("File: (nessuno)")
    btn_pick = QPushButton("Selezionare file CSV/TSV")

    box_opts = QGroupBox("Opzioni")
    lay_opts = QHBoxLayout()
    box_opts.setLayout(lay_opts)

    cb_has_header = QCheckBox("Header presente")
    cb_has_header.setChecked(default_has_header)

    cb_preview_only = QCheckBox("Solo anteprima (non scrivere in Anki)")
    cb_preview_only.setChecked(default_preview_only)

    cb_strict = QCheckBox("Strict columns")
    cb_strict.setChecked(default_strict)

    cb_skip_empty = QCheckBox("Saltare righe vuote")
    cb_skip_empty.setChecked(default_skip_empty)

    cb_force_test = QCheckBox("Forzare import in mazzo di test")
    cb_force_test.setChecked(default_force_test)

    delim_combo = QComboBox()
    delim_combo.addItem("TSV (tab)", "\t")
    delim_combo.addItem("CSV (,)", ",")
    delim_combo.addItem("CSV (;)", ";")

    lay_opts.addWidget(cb_has_header)
    lay_opts.addWidget(cb_preview_only)
    lay_opts.addWidget(cb_strict)
    lay_opts.addWidget(cb_skip_empty)
    lay_opts.addWidget(cb_force_test)
    lay_opts.addWidget(QLabel("Delimitatore"))
    lay_opts.addWidget(delim_combo)

    decks_combo = QComboBox()
    models_combo = QComboBox()

    btn_refresh = QPushButton("Aggiornare anteprima e mappatura")
    btn_run = QPushButton("Eseguire (anteprima o import)")

    btn_refresh.setEnabled(False)
    btn_run.setEnabled(False)

    table = QTableWidget()
    table.setRowCount(0)
    table.setColumnCount(0)

    box_map = QGroupBox("Mappatura colonne -> campi")
    lay_map = QVBoxLayout()
    box_map.setLayout(lay_map)

    mapping_widgets: Dict[str, QComboBox] = {}

    root.addWidget(lbl_path)
    root.addWidget(btn_pick)
    root.addWidget(box_opts)

    root.addWidget(QLabel("Mazzo di destinazione"))
    root.addWidget(decks_combo)

    root.addWidget(QLabel("Tipo di nota"))
    root.addWidget(models_combo)

    root.addWidget(btn_refresh)
    root.addWidget(QLabel("Anteprima"))
    root.addWidget(table)

    root.addWidget(box_map)
    root.addWidget(btn_run)

    def _infer_delimiter(path: str) -> str:
        if path.lower().endswith(".tsv"):
            return "\t"
        if path.lower().endswith(".csv"):
            return ","
        return "\t"

    def load_decks() -> None:
        decks_combo.clear()
        all_decks = mw.col.decks.all_names_and_ids()
        for d in all_decks:
            decks_combo.addItem(d.name, d.id)

    def load_models() -> None:
        models_combo.clear()
        for m in mw.col.models.all():
            models_combo.addItem(m["name"], m["id"])

    def _get_model_fields() -> List[str]:
        mid = models_combo.currentData()
        if mid is None:
            return []
        model = mw.col.models.get(mid)
        if not model:
            return []
        return [f["name"] for f in model["flds"]]

    def pick_file() -> None:
        try:
            path, _ = QFileDialog.getOpenFileName(
                dlg,
                "Selezionare file",
                "",
                "CSV (*.csv);;TSV (*.tsv);;Tutti i file (*.*)"
            )
            if not path:
                return

            state["path"] = path
            lbl_path.setText(f"File: {path}")

            suggested = _infer_delimiter(path)
            if suggested == "\t":
                delim_combo.setCurrentIndex(0)
            elif suggested == ",":
                delim_combo.setCurrentIndex(1)

            btn_refresh.setEnabled(True)
            btn_run.setEnabled(True)

        except Exception as e:
            log_line(f"Errore selezione file: {e}")
            showCritical(str(e))

    def _set_table(header: Optional[List[str]], rows: List[List[str]], max_cols: int) -> None:
        cols = max(max_cols, 1)
        table.setColumnCount(cols)

        if header and len(header) == cols:
            table.setHorizontalHeaderLabels(header)
            state["col_names"] = header[:]
        else:
            col_names = [f"Col {i+1}" for i in range(cols)]
            table.setHorizontalHeaderLabels(col_names)
            state["col_names"] = col_names

        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c in range(cols):
                val = row[c] if c < len(row) else ""
                table.setItem(r, c, QTableWidgetItem(val))

    def _rebuild_mapping_ui() -> None:
        while lay_map.count():
            item = lay_map.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        mapping_widgets.clear()

        fields = _get_model_fields()
        if not fields:
            return

        col_names = state["col_names"]
        max_cols = state["max_cols"]
        max_cols = max(max_cols, 1)

        for field_name in fields:
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            row_widget.setLayout(row_layout)

            lbl = QLabel(f"Campo: {field_name}")
            combo = QComboBox()
            combo.addItem("(vuoto)", None)

            for i in range(max_cols):
                label = col_names[i] if i < len(col_names) else f"Col {i+1}"
                combo.addItem(f"{label}", i)

            row_layout.addWidget(lbl)
            row_layout.addWidget(combo)
            lay_map.addWidget(row_widget)

            mapping_widgets[field_name] = combo

        if cb_has_header.isChecked() and state["header"]:
            header = state["header"]
            lower_to_index = {h.strip().lower(): idx for idx, h in enumerate(header)}
            for field_name in fields:
                idx = lower_to_index.get(field_name.strip().lower())
                if idx is not None:
                    mapping_widgets[field_name].setCurrentIndex(idx + 1)

    def refresh_preview_and_mapping() -> None:
        try:
            path = state["path"]
            if not path:
                showCritical("Selezionare prima un file.")
                return

            delimiter = str(delim_combo.currentData())
            has_header = cb_has_header.isChecked()

            header, rows, max_cols = read_preview(
                path=path,
                delimiter=delimiter,
                has_header=has_header,
                max_rows=preview_rows,
                enc_primary=enc_primary,
                enc_fallback=enc_fallback
            )

            state["delimiter"] = delimiter
            state["header"] = header
            state["max_cols"] = max_cols

            _set_table(header, rows, max_cols)
            _rebuild_mapping_ui()

        except Exception as e:
            log_line(f"Errore refresh preview/mapping: {e}")
            showCritical(str(e))

    def _collect_mapping() -> Dict[str, Optional[int]]:
        mapping: Dict[str, Optional[int]] = {}
        for field_name, combo in mapping_widgets.items():
            mapping[field_name] = combo.currentData()
        return mapping

    def _find_test_deck_id() -> Optional[int]:
        all_decks = mw.col.decks.all_names_and_ids()
        for d in all_decks:
            if d.name.strip().lower() == test_deck_name.strip().lower():
                return int(d.id)
        return None

    def run_action() -> None:
        try:
            path = state["path"]
            if not path:
                showCritical("Selezionare prima un file.")
                return

            deck_id = decks_combo.currentData()
            model_id = models_combo.currentData()
            if deck_id is None or model_id is None:
                showCritical("Selezionare mazzo e tipo di nota.")
                return

            if state["max_cols"] == 0:
                refresh_preview_and_mapping()

            mapping = _collect_mapping()

            if cb_force_test.isChecked():
                test_id = _find_test_deck_id()
                if test_id is None:
                    showCritical(
                        f"Mazzo di test '{test_deck_name}' non trovato.\n"
                        "Creare il mazzo oppure disattivare l’opzione."
                    )
                    return
                deck_id = test_id

            res = import_file(
                path=path,
                delimiter=state["delimiter"],
                has_header=cb_has_header.isChecked(),
                preview_only=cb_preview_only.isChecked(),
                deck_id=int(deck_id),
                model_id=int(model_id),
                field_to_col=mapping,
                strict_columns=cb_strict.isChecked(),
                skip_empty_rows=cb_skip_empty.isChecked(),
                enc_primary=enc_primary,
                enc_fallback=enc_fallback,
                report_encoding=report_encoding
            )

            showInfo(
                "Operazione completata\n\n"
                f"Righe totali nel file: {res['rows_total_in_file']}\n"
                f"Righe processate (escluso header): {res['rows_processed']}\n"
                f"Note create: {res['created']}\n"
                f"Saltate: {res['skipped']}\n"
                f"Errori: {res['errors']}\n\n"
                f"Report CSV:\n{res['report_path']}"
            )

        except Exception as e:
            log_line(f"Errore run_action: {e}")
            showCritical(str(e))

    btn_pick.clicked.connect(pick_file)
    btn_refresh.clicked.connect(refresh_preview_and_mapping)
    btn_run.clicked.connect(run_action)

    def on_model_changed() -> None:
        try:
            if state["max_cols"] > 0:
                _rebuild_mapping_ui()
        except Exception as e:
            log_line(f"Errore cambio modello: {e}")

    models_combo.currentIndexChanged.connect(on_model_changed)

    load_decks()
    load_models()

    dlg.exec()
  ```

======================================================================
COME OGNI ESTENSIONE È REALMENTE IMPLEMENTATA (RICAPITOLAZIONE)
===============================================================

1. Mappatura colonne → campi con combo box

* PyQt: QComboBox creati dinamicamente in base ai campi del modello.
* API Anki: campi ottenuti da mw.col.models.get(model_id)["flds"].
* In importer.py: field_to_col guida l’assegnazione note[field] = row[idx].

2. Rilevamento automatico intestazione

* preview.py: se has_header, prima riga diventa header e non entra nelle righe.
* gui.py: header usato come intestazione della QTableWidget.
* gui.py: auto-mappatura campo->colonna se nome header coincide col nome campo (case-insensitive).
* importer.py: prima riga saltata con motivo “header”.

3. Modalità “solo anteprima”

* gui.py: checkbox cb_preview_only.
* importer.py: se preview_only, non chiamare mw.col.add_note; scrivere report con reason “preview_only_no_write”.

4. Import in mazzo di test

* gui.py: checkbox cb_force_test e nome mazzo test da config.
* API Anki: deck id ricavato con mw.col.decks.all_names_and_ids().
* importer.py: riceve deck_id già risolto (test o normale).

5. Report CSV riga per riga

* importer.py: apertura file report e scrittura status/reason per ogni linea.
* showInfo mostra il path per aprirlo con un file manager.

6. Supporto UTF-8 e fallback

* preview.py e importer.py: open con encoding primary, in caso di UnicodeDecodeError usare encoding fallback.
* Scopo: gestire file reali creati con editor diversi.

======================================================================
NOTE IMPORTANTI PER LO SVILUPPO DI ADD-ON (NON STANDARD)
========================================================

1. Riavvio Anki

* Un add-on viene importato all’avvio. Per testare modifiche, riavviare Anki.

2. Gestione eccezioni in **init**.py

* Evitare qualunque eccezione non gestita nel top-level: impedisce il caricamento dell’add-on.

3. Evitare blocchi lunghi senza progress

* Per import di dimensioni significative, mw.progress.start/finish è essenziale.

4. mw.reset

* Dopo import effettivo, mw.reset serve a vedere subito le note e a mantenere coerenza interna.

Se si desidera, nel passo successivo si può aggiungere un miglioramento “non banale” ma molto richiesto: gestione dei duplicati con aggiornamento della nota esistente (strategia di matching + campo chiave), mantenendo report e modalità test.


# fine estensioni didattiche

Di seguito una **lezione completa e autonoma** che guida **passo passo** alla costruzione di un **add-on didattico “da produzione” per Anki**, dedicato all’**importazione automatica di contenuti**.
La lezione **spiega tutto**: architettura, scelte progettuali, flusso di lavoro, GUI, import, gestione errori, progress bar, report finale.
Il linguaggio è **impersonale**, con indicazioni operative all’infinito.
Nel codice sono incluse **spiegazioni commentate riga per riga** (commenti Python).

---

# Lezione: Add-on didattico per importazione automatica in Anki

## Obiettivo didattico

Costruire un add-on che consenta di:

* selezionare un file di input (CSV o TSV)
* scegliere mazzo e tipo di nota
* mappare colonne del file sui campi del tipo di nota
* mostrare un’anteprima delle righe
* eseguire l’import con progress bar
* gestire duplicati e righe incomplete
* produrre un report finale leggibile

L’add-on è progettato per **uso scolastico** e **laboratori didattici**, con attenzione a sicurezza, robustezza e chiarezza.

---

## Architettura dell’add-on

Struttura consigliata:

```
didactic_importer/
    __init__.py
    gui.py
    importer.py
    preview.py
    logging_utils.py
```

Principi:

* **init**.py contiene solo l’entry point
* gui.py gestisce interfaccia e input utente
* importer.py contiene la logica di import
* preview.py gestisce l’anteprima
* logging_utils.py centralizza il logging

Separare responsabilità rende il codice leggibile, testabile e didatticamente efficace.

---

## Entry point e integrazione con Anki

### File: **init**.py

Responsabilità:

* registrare una voce nel menu Strumenti
* non eseguire logica complessa

  from aqt import mw
  from aqt.qt import QAction
  from .gui import open_import_dialog

  # Creare una QAction collegata alla finestra principale di Anki (mw)

  action = QAction("Didactic Importer: Importa file", mw)

  # Collegare il click all’apertura della finestra di import

  action.triggered.connect(open_import_dialog)

  # Aggiungere la voce al menu Strumenti

  mw.form.menuTools.addAction(action)

Nota didattica:

* se **init**.py solleva eccezioni, l’add-on non viene caricato
* mantenere il codice minimale riduce i rischi

---

## Interfaccia grafica (GUI)

### Obiettivi della GUI

Consentire all’utente di:

* selezionare un file CSV/TSV
* scegliere mazzo di destinazione
* scegliere tipo di nota
* visualizzare i campi del tipo di nota
* avviare anteprima e import

---

### File: gui.py

```
from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog,
    QComboBox, QListWidget
)
from aqt.utils import showCritical, showInfo
from .preview import preview_file
from .importer import import_file
from .logging_utils import log_line

def open_import_dialog() -> None:
    # Creare dialog modale collegato alla finestra principale
    dlg = QDialog(mw)
    dlg.setWindowTitle("Didactic Importer")

    layout = QVBoxLayout()

    # Stato interno minimo per condividere dati tra callback
    state = {
        "path": None,
        "delimiter": "\t"
    }

    # Etichetta che mostra il file selezionato
    lbl_path = QLabel("File: (nessuno)")

    btn_pick = QPushButton("Selezionare file CSV / TSV")
    btn_preview = QPushButton("Anteprima")
    btn_import = QPushButton("Importa")

    btn_preview.setEnabled(False)
    btn_import.setEnabled(False)

    decks_combo = QComboBox()
    models_combo = QComboBox()
    fields_list = QListWidget()

    layout.addWidget(lbl_path)
    layout.addWidget(btn_pick)

    layout.addWidget(QLabel("Mazzo di destinazione"))
    layout.addWidget(decks_combo)

    layout.addWidget(QLabel("Tipo di nota"))
    layout.addWidget(models_combo)

    layout.addWidget(QLabel("Campi del tipo di nota (ordine)"))
    layout.addWidget(fields_list)

    layout.addWidget(btn_preview)
    layout.addWidget(btn_import)

    dlg.setLayout(layout)

    # Caricare mazzi disponibili
    def load_decks() -> None:
        decks_combo.clear()
        for d in mw.col.decks.all_names_and_ids():
            decks_combo.addItem(d.name, d.id)

    # Caricare tipi di nota
    def load_models() -> None:
        models_combo.clear()
        for m in mw.col.models.all():
            models_combo.addItem(m["name"], m["id"])

    # Aggiornare lista campi quando cambia il tipo di nota
    def load_fields() -> None:
        fields_list.clear()
        mid = models_combo.currentData()
        if mid is None:
            return
        model = mw.col.models.get(mid)
        for f in model["flds"]:
            fields_list.addItem(f["name"])

    def pick_file() -> None:
        try:
            path, _ = QFileDialog.getOpenFileName(
                dlg,
                "Selezionare file",
                "",
                "CSV (*.csv);;TSV (*.tsv);;Tutti i file (*.*)"
            )
            if not path:
                return

            state["path"] = path
            state["delimiter"] = "\t" if path.lower().endswith(".tsv") else ","
            lbl_path.setText(f"File: {path}")

            btn_preview.setEnabled(True)
            btn_import.setEnabled(True)
        except Exception as e:
            log_line(f"Errore selezione file: {e}")
            showCritical(str(e))

    def do_preview() -> None:
        try:
            preview_file(
                path=state["path"],
                delimiter=state["delimiter"],
                parent=dlg
            )
        except Exception as e:
            log_line(f"Errore anteprima: {e}")
            showCritical(str(e))

    def do_import() -> None:
        try:
            result = import_file(
                path=state["path"],
                delimiter=state["delimiter"],
                deck_id=int(decks_combo.currentData()),
                model_id=int(models_combo.currentData())
            )

            showInfo(
                "Import completato\n\n"
                f"Righe lette: {result['rows']}\n"
                f"Note create: {result['created']}\n"
                f"Saltate: {result['skipped']}\n"
                f"Errori: {result['errors']}"
            )
        except Exception as e:
            log_line(f"Errore import: {e}")
            showCritical(str(e))

    btn_pick.clicked.connect(pick_file)
    btn_preview.clicked.connect(do_preview)
    btn_import.clicked.connect(do_import)
    models_combo.currentIndexChanged.connect(load_fields)

    load_decks()
    load_models()
    load_fields()

    dlg.exec()
```

Nota didattica:

* lo stato è tenuto in un dizionario semplice
* le callback sono brevi e protette con try/except
* la GUI non contiene logica di import

---

## Anteprima del file

### Obiettivo

Consentire di:

* verificare struttura del file
* individuare errori prima dell’import
* ridurre danni didattici

---

### File: preview.py

```
import csv
from aqt.qt import QDialog, QVBoxLayout, QTextEdit

def preview_file(path: str, delimiter: str, parent) -> None:
    dlg = QDialog(parent)
    dlg.setWindowTitle("Anteprima file (prime 10 righe)")

    layout = QVBoxLayout()
    text = QTextEdit()
    text.setReadOnly(True)

    layout.addWidget(text)
    dlg.setLayout(layout)

    lines = []

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for i, row in enumerate(reader):
            if i >= 10:
                break
            lines.append(" | ".join(row))

    text.setText("\n".join(lines))
    dlg.exec()
```

Nota didattica:

* non si modifica nulla
* l’anteprima è una funzione “sicura”
* il delimitatore viene dedotto in precedenza

---

## Logica di importazione

### Principi di sicurezza

* usare progress bar
* validare ogni riga
* gestire duplicati
* non bloccare la UI senza feedback
* registrare errori su file

---

### File: importer.py

```
import csv
from aqt import mw
from .logging_utils import log_line

def import_file(
    path: str,
    delimiter: str,
    deck_id: int,
    model_id: int
) -> dict:

    result = {
        "rows": 0,
        "created": 0,
        "skipped": 0,
        "errors": 0
    }

    model = mw.col.models.get(model_id)
    if not model:
        raise RuntimeError("Tipo di nota non valido.")

    fields = [f["name"] for f in model["flds"]]

    mw.progress.start(label="Import in corso...", immediate=True)

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter=delimiter)

            for row in reader:
                result["rows"] += 1

                # Saltare righe vuote
                if not row or all(c.strip() == "" for c in row):
                    result["skipped"] += 1
                    continue

                try:
                    note = mw.col.new_note(model)

                    for i, field in enumerate(fields):
                        if i < len(row):
                            note[field] = row[i].strip()
                        else:
                            note[field] = ""

                    # Evitare duplicati o note vuote
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

Nota didattica:

* ogni riga è isolata: un errore non ferma l’import
* dupeOrEmpty evita duplicati comuni
* mw.reset aggiorna l’interfaccia

---

## Logging

### File: logging_utils.py

```
import os
import datetime

LOG_NAME = "didactic_importer.log"

def _addon_dir() -> str:
    return os.path.dirname(__file__)

def log_line(message: str) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}\n"

    try:
        with open(
            os.path.join(_addon_dir(), LOG_NAME),
            "a",
            encoding="utf-8"
        ) as f:
            f.write(line)
    except Exception:
        pass
```

Nota didattica:

* il logging non deve mai bloccare l’add-on
* il file di log è locale all’add-on
* utile per analisi post-laboratorio

---

## Estensioni didattiche consigliate

* mappatura colonne → campi con combo box
* rilevamento automatico intestazione
* modalità “solo anteprima”
* import in mazzo di test
* report CSV finale con esito riga per riga
* supporto UTF-8 e fallback

---

## Checklist finale (uso in classe)

* usare un profilo Anki di test
* mostrare prima l’anteprima
* spiegare struttura file agli studenti
* verificare campi del tipo di nota
* controllare report e log
* solo dopo passare a mazzi reali

---

## Conclusione

Questo add-on rappresenta un **caso reale completo**, adatto a:

* laboratori di informatica
* corsi su Python applicato
* didattica digitale
* automazione di contenuti didattici

Integra concetti di:

* architettura software
* GUI event-driven
* gestione dati
* robustezza applicativa
* responsabilità del codice

Se si desidera, nel passo successivo è possibile:

* aggiungere debugging avanzato con debugpy
* trasformare l’add-on in pacchetto AnkiWeb
* adattarlo a import da Excel
* costruire una versione “studente” e una “docente” separate

# fine sezione

<hr/>

OBIETTIVO DEL “PROSSIMO PASSO”

Procedere trasformando l’add-on “Didactic Importer” in una versione più vicina a un uso reale, aggiungendo:

1. rilevamento intestazione (header) e auto-mappatura per nome campo
2. mappatura grafica colonne -> campi (combo box per ogni campo)
3. anteprima più chiara (tabella)
4. import robusto con report CSV finale “riga per riga”
5. opzioni didattiche: modalità strict, gestione righe vuote, import in mazzo selezionato, log su file

Il risultato rimane “didattico”, ma con scelte progettuali più solide.

======================================================================
STRUTTURA FINALE DELL’ADD-ON
============================

Creare una cartella in addons21:

```
didactic_importer/
```

Contenuto:

```
didactic_importer/
    __init__.py
    gui.py
    importer.py
    preview.py
    logging_utils.py
    config.json
```

Nota operativa
Durante lo sviluppo, copiare la cartella in addons21 e riavviare Anki dopo ogni modifica significativa.

======================================================================
FILE: config.json
=================

Scopo: valori di default per ridurre il carico cognitivo e rendere ripetibile l’uso in laboratorio.

```
{
    "default_has_header": true,
    "default_strict_columns": false,
    "default_skip_empty_rows": true,
    "default_delimiter_csv": ",",
    "default_delimiter_tsv": "\t",
    "default_preview_rows": 15,
    "default_report_encoding": "utf-8"
}
```

======================================================================
FILE: **init**.py
=================

Responsabilità: entry point minimale, registrare una voce nel menu Strumenti.

```
from aqt import mw
from aqt.qt import QAction
from .gui import open_import_dialog

action = QAction("Didactic Importer Pro: Importa CSV/TSV", mw)
action.triggered.connect(open_import_dialog)
mw.form.menuTools.addAction(action)
```

======================================================================
FILE: logging_utils.py
======================

Responsabilità: logging semplice e non bloccante.

```
import os
import datetime

LOG_NAME = "didactic_importer.log"

def _addon_dir() -> str:
    return os.path.dirname(__file__)

def _log_path() -> str:
    return os.path.join(_addon_dir(), LOG_NAME)

def log_line(message: str) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}\n"
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # Il logging non deve mai bloccare l’add-on
        pass
```

======================================================================
FILE: preview.py
================

Responsabilità: leggere una porzione del file e restituire:

* header (se presente)
* righe di anteprima
* numero colonne

Nessuna modifica alla collezione.

```
import csv
from typing import List, Optional, Tuple

def read_preview(
    path: str,
    delimiter: str,
    has_header: bool,
    max_rows: int
) -> Tuple[Optional[List[str]], List[List[str]], int]:
    header = None
    rows: List[List[str]] = []
    max_cols = 0

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)

        for i, row in enumerate(reader):
            if i == 0 and has_header:
                header = [c.strip() for c in row]
                max_cols = max(max_cols, len(header))
                continue

            rows.append([c.strip() for c in row])
            max_cols = max(max_cols, len(row))

            if len(rows) >= max_rows:
                break

    return header, rows, max_cols
```

======================================================================
FILE: importer.py
=================

Responsabilità:

* leggere tutto il file
* creare note in base alla mappatura (campo -> indice colonna)
* gestire righe vuote
* gestire “strict columns”
* produrre report CSV con esito riga per riga

Formato report (CSV):

* line_no: numero riga nel file (1-based, includendo header se presente)
* status: CREATED / SKIPPED / ERROR
* reason: motivazione sintetica
* raw: contenuto riga (join con “ | ”, per ispezione veloce)

  import csv
  import os
  import datetime
  from typing import Dict, Optional, List

  from aqt import mw
  from .logging_utils import log_line

  def _addon_dir() -> str:
  return os.path.dirname(**file**)

  def *make_report_path() -> str:
  ts = datetime.datetime.now().strftime("%Y%m%d*%H%M%S")
  return os.path.join(*addon_dir(), f"import_report*{ts}.csv")

  def import_file(
  path: str,
  delimiter: str,
  has_header: bool,
  deck_id: int,
  model_id: int,
  field_to_col: Dict[str, Optional[int]],
  strict_columns: bool,
  skip_empty_rows: bool,
  report_encoding: str
  ) -> dict:
  result = {
  "rows": 0,
  "created": 0,
  "skipped": 0,
  "errors": 0,
  "report_path": None
  }

  ```
    model = mw.col.models.get(model_id)
    if not model:
        raise RuntimeError("Tipo di nota non valido.")

    fields = [f["name"] for f in model["flds"]]
    if not fields:
        raise RuntimeError("Il tipo di nota non contiene campi.")

    report_path = _make_report_path()
    result["report_path"] = report_path

    mw.progress.start(label="Import in corso...", immediate=True)

    try:
        with open(path, "r", encoding="utf-8", newline="") as f_in, \
             open(report_path, "w", encoding=report_encoding, newline="") as f_rep:

            reader = csv.reader(f_in, delimiter=delimiter)
            rep = csv.writer(f_rep, delimiter=",")

            # Intestazione report
            rep.writerow(["line_no", "status", "reason", "raw"])

            line_no = 0

            for row in reader:
                line_no += 1

                # Saltare la riga di header, se presente
                if line_no == 1 and has_header:
                    rep.writerow([line_no, "SKIPPED", "header", " | ".join(row)])
                    continue

                result["rows"] += 1

                # Normalizzare celle
                row = [c.strip() for c in row]

                # Righe vuote
                if skip_empty_rows and (not row or all(c == "" for c in row)):
                    result["skipped"] += 1
                    rep.writerow([line_no, "SKIPPED", "empty_row", " | ".join(row)])
                    continue

                # Strict columns: richiedere che ogni campo mappato abbia la colonna disponibile
                if strict_columns:
                    ok = True
                    for field_name in fields:
                        idx = field_to_col.get(field_name, None)
                        if idx is None:
                            continue
                        if idx >= len(row):
                            ok = False
                            break
                    if not ok:
                        result["skipped"] += 1
                        rep.writerow([line_no, "SKIPPED", "missing_columns_strict", " | ".join(row)])
                        continue

                try:
                    note = mw.col.new_note(model)

                    # Popolare ogni campo in base alla mappatura
                    for field_name in fields:
                        idx = field_to_col.get(field_name, None)

                        if idx is None:
                            note[field_name] = ""
                            continue

                        if idx < len(row):
                            note[field_name] = row[idx]
                        else:
                            note[field_name] = ""

                    # Dupe o vuota: Anki fornisce questa utility; è comoda e riduce errori didattici
                    if note.dupeOrEmpty():
                        result["skipped"] += 1
                        rep.writerow([line_no, "SKIPPED", "dupe_or_empty", " | ".join(row)])
                        continue

                    mw.col.add_note(note, deck_id)
                    result["created"] += 1
                    rep.writerow([line_no, "CREATED", "ok", " | ".join(row)])

                except Exception as e:
                    result["errors"] += 1
                    log_line(f"Errore riga file {line_no}: {e}")
                    rep.writerow([line_no, "ERROR", str(e), " | ".join(row)])

        # Aggiornare interfaccia Anki: mostra nuove note e ricalcola
        mw.reset()

        return result

    finally:
        mw.progress.finish()
  ```

======================================================================
FILE: gui.py
============

Responsabilità:

* scegliere file CSV/TSV
* scegliere delimitatore in modo guidato
* spuntare “header presente”
* mostrare anteprima tabellare
* costruire mappatura colonne -> campi con combo box
* avviare import e mostrare report

Nota: il codice usa controlli Qt standard già presenti in Anki.

```
from typing import Optional, Dict, List

from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog,
    QComboBox, QListWidget, QCheckBox,
    QTableWidget, QTableWidgetItem, QGroupBox
)
from aqt.utils import showCritical, showInfo

from .logging_utils import log_line
from .preview import read_preview
from .importer import import_file

def open_import_dialog() -> None:
    dlg = QDialog(mw)
    dlg.setWindowTitle("Didactic Importer Pro")

    layout = QVBoxLayout()
    dlg.setLayout(layout)

    # Caricare config (se assente, usare fallback)
    try:
        cfg = mw.addonManager.getConfig(__name__)
    except Exception:
        cfg = {}

    default_has_header = bool(cfg.get("default_has_header", True))
    default_strict = bool(cfg.get("default_strict_columns", False))
    default_skip_empty = bool(cfg.get("default_skip_empty_rows", True))
    preview_rows = int(cfg.get("default_preview_rows", 15))
    report_encoding = str(cfg.get("default_report_encoding", "utf-8"))

    state = {
        "path": None,
        "delimiter": "\t",
        "header": None,
        "max_cols": 0,
        "preview_rows": [],
        "col_names": []
    }

    # Sezione: file
    lbl_path = QLabel("File: (nessuno)")
    btn_pick = QPushButton("Selezionare file CSV / TSV")

    # Sezione: opzioni parsing
    opt_box = QGroupBox("Opzioni file")
    opt_layout = QHBoxLayout()
    opt_box.setLayout(opt_layout)

    cb_has_header = QCheckBox("Header presente (prima riga)")
    cb_has_header.setChecked(default_has_header)

    cb_strict = QCheckBox("Strict: richiedere colonne presenti per campi mappati")
    cb_strict.setChecked(default_strict)

    cb_skip_empty = QCheckBox("Saltare righe vuote")
    cb_skip_empty.setChecked(default_skip_empty)

    delim_combo = QComboBox()
    delim_combo.addItem("TSV (tab)", "\t")
    delim_combo.addItem("CSV (,)", ",")
    delim_combo.addItem("CSV (;)", ";")

    opt_layout.addWidget(cb_has_header)
    opt_layout.addWidget(cb_strict)
    opt_layout.addWidget(cb_skip_empty)
    opt_layout.addWidget(QLabel("Delimitatore"))
    opt_layout.addWidget(delim_combo)

    # Sezione: scelta mazzo e modello
    decks_combo = QComboBox()
    models_combo = QComboBox()

    # Sezione: preview tabella
    table = QTableWidget()
    table.setRowCount(0)
    table.setColumnCount(0)

    # Sezione: mappatura
    map_box = QGroupBox("Mappatura colonne -> campi del tipo di nota")
    map_layout = QVBoxLayout()
    map_box.setLayout(map_layout)

    # Qui verranno inserite righe: Label campo + combo selezione colonna
    mapping_widgets: Dict[str, QComboBox] = {}

    # Pulsanti azione
    btn_preview = QPushButton("Aggiornare anteprima e mappatura")
    btn_import = QPushButton("Importare")
    btn_preview.setEnabled(False)
    btn_import.setEnabled(False)

    layout.addWidget(lbl_path)
    layout.addWidget(btn_pick)
    layout.addWidget(opt_box)

    layout.addWidget(QLabel("Mazzo di destinazione"))
    layout.addWidget(decks_combo)

    layout.addWidget(QLabel("Tipo di nota"))
    layout.addWidget(models_combo)

    layout.addWidget(btn_preview)
    layout.addWidget(QLabel("Anteprima"))
    layout.addWidget(table)

    layout.addWidget(map_box)
    layout.addWidget(btn_import)

    def load_decks() -> None:
        decks_combo.clear()
        for d in mw.col.decks.all_names_and_ids():
            decks_combo.addItem(d.name, d.id)

    def load_models() -> None:
        models_combo.clear()
        for m in mw.col.models.all():
            models_combo.addItem(m["name"], m["id"])

    def _infer_delimiter_from_path(path: str) -> str:
        # Euristica semplice: .tsv -> tab, altrimenti virgola
        if path.lower().endswith(".tsv"):
            return "\t"
        if path.lower().endswith(".csv"):
            return ","
        return "\t"

    def pick_file() -> None:
        try:
            path, _ = QFileDialog.getOpenFileName(
                dlg,
                "Selezionare file",
                "",
                "CSV (*.csv);;TSV (*.tsv);;Tutti i file (*.*)"
            )
            if not path:
                return

            state["path"] = path
            lbl_path.setText(f"File: {path}")

            # Impostare delimitatore suggerito
            suggested = _infer_delimiter_from_path(path)
            if suggested == "\t":
                delim_combo.setCurrentIndex(0)
            elif suggested == ",":
                delim_combo.setCurrentIndex(1)

            btn_preview.setEnabled(True)
            btn_import.setEnabled(True)

        except Exception as e:
            log_line(f"Errore selezione file: {e}")
            showCritical(str(e))

    def _get_model_fields() -> List[str]:
        mid = models_combo.currentData()
        if mid is None:
            return []
        model = mw.col.models.get(mid)
        if not model:
            return []
        return [f["name"] for f in model["flds"]]

    def _set_table(header: Optional[List[str]], rows: List[List[str]], max_cols: int) -> None:
        # Impostare colonne
        table.setColumnCount(max_cols if max_cols > 0 else 1)

        # Header visivo: se presente, usarlo; altrimenti “Col 1..n”
        if header and len(header) == max_cols:
            table.setHorizontalHeaderLabels(header)
            state["col_names"] = header[:]
        else:
            col_names = [f"Col {i+1}" for i in range(max_cols)]
            table.setHorizontalHeaderLabels(col_names)
            state["col_names"] = col_names

        table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            for c in range(max_cols):
                val = row[c] if c < len(row) else ""
                table.setItem(r, c, QTableWidgetItem(val))

    def _rebuild_mapping_ui() -> None:
        # Svuotare UI mappatura
        while map_layout.count():
            item = map_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        mapping_widgets.clear()

        fields = _get_model_fields()
        if not fields:
            return

        # Creare una combo per ciascun campo
        # Opzioni combo:
        # - (vuoto) -> None
        # - Col 1..N
        # Se header presente e coerente, mostrare i nomi delle colonne
        col_names = state["col_names"]
        max_cols = state["max_cols"]

        for field_name in fields:
            row_box = QGroupBox()
            row_layout = QHBoxLayout()
            row_box.setLayout(row_layout)

            lbl = QLabel(f"Campo: {field_name}")
            combo = QComboBox()
            combo.addItem("(vuoto)", None)

            for i in range(max_cols):
                label = col_names[i] if i < len(col_names) else f"Col {i+1}"
                combo.addItem(f"{label}  (indice {i})", i)

            row_layout.addWidget(lbl)
            row_layout.addWidget(combo)
            map_layout.addWidget(row_box)

            mapping_widgets[field_name] = combo

        # Auto-mappatura se header presente: se un nome colonna coincide con un campo
        if cb_has_header.isChecked() and state["header"]:
            header = state["header"]
            if header:
                lower_to_index = {h.strip().lower(): idx for idx, h in enumerate(header)}
                for field_name in fields:
                    idx = lower_to_index.get(field_name.strip().lower(), None)
                    if idx is not None:
                        mapping_widgets[field_name].setCurrentIndex(idx + 1)

    def do_preview_and_mapping() -> None:
        try:
            path = state["path"]
            if not path:
                showCritical("Selezionare prima un file.")
                return

            delimiter = str(delim_combo.currentData())
            has_header = cb_has_header.isChecked()

            header, rows, max_cols = read_preview(
                path=path,
                delimiter=delimiter,
                has_header=has_header,
                max_rows=preview_rows
            )

            state["delimiter"] = delimiter
            state["header"] = header
            state["preview_rows"] = rows
            state["max_cols"] = max_cols

            _set_table(header, rows, max_cols)
            _rebuild_mapping_ui()

        except Exception as e:
            log_line(f"Errore preview/mapping: {e}")
            showCritical(str(e))

    def _collect_mapping() -> Dict[str, Optional[int]]:
        mapping: Dict[str, Optional[int]] = {}
        for field_name, combo in mapping_widgets.items():
            mapping[field_name] = combo.currentData()
        return mapping

    def do_import() -> None:
        try:
            path = state["path"]
            if not path:
                showCritical("Selezionare prima un file.")
                return

            deck_id = decks_combo.currentData()
            model_id = models_combo.currentData()
            if deck_id is None or model_id is None:
                showCritical("Selezionare mazzo e tipo di nota.")
                return

            # Forzare un preview prima dell’import se non è stato fatto
            if state["max_cols"] == 0:
                do_preview_and_mapping()

            mapping = _collect_mapping()

            res = import_file(
                path=path,
                delimiter=state["delimiter"],
                has_header=cb_has_header.isChecked(),
                deck_id=int(deck_id),
                model_id=int(model_id),
                field_to_col=mapping,
                strict_columns=cb_strict.isChecked(),
                skip_empty_rows=cb_skip_empty.isChecked(),
                report_encoding=report_encoding
            )

            showInfo(
                "Import completato\n\n"
                f"Righe lette (escluso header): {res['rows']}\n"
                f"Note create: {res['created']}\n"
                f"Saltate: {res['skipped']}\n"
                f"Errori: {res['errors']}\n\n"
                f"Report CSV:\n{res['report_path']}"
            )

        except Exception as e:
            log_line(f"Errore import: {e}")
            showCritical(str(e))

    btn_pick.clicked.connect(pick_file)
    btn_preview.clicked.connect(do_preview_and_mapping)
    btn_import.clicked.connect(do_import)

    # Ricaricare i campi e ricostruire mapping UI quando cambia modello
    def on_model_changed() -> None:
        try:
            # Se esiste già un’anteprima, ricostruire la mappatura
            if state["max_cols"] > 0:
                _rebuild_mapping_ui()
        except Exception as e:
            log_line(f"Errore cambio modello: {e}")

    models_combo.currentIndexChanged.connect(on_model_changed)

    load_decks()
    load_models()

    dlg.exec()
```

======================================================================
COME USARE L’ADD-ON IN CLASSE (PROCEDURA OPERATIVA)
===================================================

1. Preparare un profilo Anki di test (raccomandato)
   Creare un profilo dedicato e importare su quello, almeno in fase di prova.

2. Preparare un file TSV semplice (consigliato)
   Esempio (header presente):

   Front    Back
   Capitale Italia    Roma
   Capitale Francia   Parigi

Nota: tra “Front” e “Back” deve esserci un TAB reale.

3. In Anki

* aprire Strumenti
* avviare “Didactic Importer Pro: Importa CSV/TSV”
* selezionare file
* impostare “Header presente” se il file ha intestazione
* selezionare mazzo e tipo di nota
* cliccare “Aggiornare anteprima e mappatura”
* verificare anteprima tabellare
* verificare mappatura (auto-mappatura se header e campi coincidono)
* cliccare “Importare”
* leggere il riepilogo
* aprire il percorso del report CSV mostrato nel messaggio finale

4. Leggere il report CSV
   Il report è utile per:

* vedere quali righe sono state create
* capire quali sono state saltate e perché
* individuare righe con errore

======================================================================
NOTE DIDATTICHE IMPORTANTI (SCELTE PROGETTUALI)
===============================================

1. Perché usare una mappatura “campo -> colonna”
   Consente di adattare qualunque file a qualunque tipo di nota senza riscrivere codice.

2. Perché un report riga-per-riga
   In classe l’errore più comune è “file non allineato”: il report rende l’errore osservabile e valutabile.

3. Perché l’auto-mappatura per header
   Riduce carico cognitivo, ma non è obbligatoria: la mappatura resta modificabile manualmente.

4. Perché la modalità strict
   Serve quando si vuole garantire che certe colonne esistano davvero; utile per verifiche e standardizzazione.

======================================================================
PROSSIMO MIGLIORAMENTO POSSIBILE (SE SI VUOLE PROSEGUIRE)
=========================================================

1. Supporto “prima colonna = Deck” (import in mazzi diversi)
2. Supporto aggiornamento note esistenti (non solo skip)
3. Supporto import da XLSX (richiede openpyxl, gestione extra)
4. Task in background per file molto grandi (approccio più avanzato)

Se si desidera, nel passo successivo si può aggiungere una modalità “aggiornamento se duplicato” con una strategia chiara (chiave di ricerca e campo di merge), mantenendo sempre report e log.
