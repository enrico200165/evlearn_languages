# Prospettiva e Obiettivi

Alcuni esempi informali di obiettivi sono
- generare un deck con i N vocaboli più frequenti in assoluto (cioè secondo una fonte che non ci interessa dato che le frequenze non saranno mai veramente assolute)  
- dato un testo generare un deck con i vocaboli che in esso hanno frequenza fra M+1 e N, entrambe inclusive
- dato un video/film/audio generare un deck con i vocaboli che in esso hanno frequenza fra M+1 e N, entrambe inclusive
- dato un testo generare un deck con le frasi che in esso hanno frequenza fra M+1 e N, entrambe inclusive
- dato un testo generare un deck con le frasi che in esso hanno frequenza fra M+1 e N, entrambe inclusive
- dato un video/film/audio generare un deck le frasi che in esso hanno frequenza fra M+1 e N, entrambe inclusive


Questi obiettivi sono ridondanti e a complessità molto alta,  superiore anche a quella stimata da informatici senior senza competenze elaborazione di testo e linguaggi, quindi:
- vanno scomposti in sottobiettivi focalizzati, cioè steps di elaborazione che siano:   
  - modulari e riusabili, 
  - con input e output generali e standard, definiti con cura (si implementa dopo analisi)
- gli steps vanno inquadrati in una pipeline il più generale possibile (senza esagerare e fallire costruendo qualcosa di troppo generale e quindi con complessità non gestibile)  
  - nella pipeline alcuni steps saranno opzionali, per alcuni steps saranno possibii elaborazioni alternative, l'importante è che **ogni step abbia input ed output standard** generali e flessibili. 
  - In alcuni casi sarà necessario più di un formato ma i formati dovranno sempre in numero minimo, ogni formato giustificato da logica di "business", non per semplificazione tecnica, 
  - formati utili a fini tecnici sono ammessi solo all'interno di eventuali sottosteps, come formati intermedi non standard.


## Comportamenti e Parametrizzazzioni generali  

Tutto ciò che segue deve essere applicato in modo ortogonale.

#### Presenza in altri decks
In tutte le generazione di decks dovrebbe essere possibile scegliere se avere
- vocali non già presenti in una lista di altri decks. 
  - La lista deve essere individuabile tramite un'espressione regolare sul nome o includere tutti i decks.  
Ciò richiede una registrazione centralizzata, indipendente dal singolo deck, della presenza di una data entry nei vari decks.
    - probabilmente si implementerà come relazione 1:N "è presente" fra entry e deck, relazione con un attributo: una stringa di descrizione opaca  

#### Range di frequenze
- entries con frequenze fra m+1 e n con riferimento a informazioni di frequenze. Ciò richiede
  - necessità di definire un formato standard per le frequenze 
  - passare le informazioni di frequenza come input alla generazione del deck  
    - per il momento per le informazioni sulla frequenza si ipotizza un file di testo letto direttamente in RAM (in una hash table) dato che le entries non saranno più di qualche migliaio

#### Molteplici input 
Quando in una directory si trova più di un file di input dello stesso tipo si genererà un deck top level con un sottodeck per ogni file. 
Solo i sotto-deck conterranno entries, quelle del file a cui sono relative

## Obiettivi: fonti contenuti  


- decks **da documenti di testo**  

- decks da files di **sottotitoli**

- decks da **audio**

- decks **video**


## Obiettivi tecnici  

### Estrazione di contenuti da multimedia

Se si considera tutto ciò che si può avere disponibile o non disponibile, ciò che si può produrre, ci si trova in una molteplicità di situazioni, che probabilmente ma non sicuramente può essere forzata in una pipeline con passi sequenziali controllati da "if then else", Un'analisi molto accurata è necessaria per evitare di sprecare lavoro.


##### Esempi di situazioni
Si può avere a disposizione:
- video con sottotitoli o senza sottotitoli
- audio con sottotitoli o senza sottotitoli
- documenti di testo
- Etc. Etc. Ect.

Analisi in sezione dedicata,** non qui!**  


### Database informazioni linguistiche (per linguaggio)

Contiene, per ogni tipo di entry (sostantivo, aggettivo, preposizione) 
- informazioni linguistiche indipendenti dalla tecnologia 
- informazioni tecniche utili alla produzione di decks (entry già presente in altri decks, frequenza entry in un determinato contesto Etc.)

#### obiettivo:  
Fungere da reference linguistica e operativa
- linguistica  
Conterra le informazioni relative ad un lemma (flessione sostantivi tedeschi, coniugazione verbi, frasi di esempio)
- operativa  
  - sapere in quali decks è eventualmente presente un'entry
  - Evitare ripetizioni chiamate remote o elaborazioni lente/costose per procurarsi informazioni linguistiche (prima si consulta il DB, se non ha già le informazioni queste vengono ottenute e memorizzate nel DB)


Tipologie informazioni identificate finora 
(esempi, analisi precisa in sezione dedicata al DB):  
- informazioni relative all'entry  
  - tipologia sostantivo, verbo ...
    - informazioni relative alla tipologia ...
- presenza entry in decks (come rel. 1:N fra entry e deck, con attributo testo opaco)
- frequenza entry in un determinato contesto (relazione 1:n fra entry e contesto, con attributo testo opaco)
- ...  

Il sw cerca le info nel database e fa chiamate solo se le informazioni non sono presenti, con le informazioni popola il database

#### Flag completezza entry

Si ipotizza popolamento incrementale,  può essere utile sapere se un'entry è completa, potrebbe essere quindi utile un flag di completezza per evitare un'analisi di completezza.
Dato che il concetto di completezza può variare nel tempo si ipotizza di utilizzare un campo timestamp contenente il timestamp dell'ultimo completamento


#### Requisiti tecnici HL (da migrare in sezione dedicata quando sarà sviluppata)

Il codice che procura informazioni linguistiche deve loggare, almeno su files, 
- quali informazioni prende (ex. flessione sostantivo Artz)
- quale sorgente (ex. chatGPT, PONS Online Dictionary API)

#### Popolamento reference DB, requisiti funzionali HL 
liste di tokens, in generale raw input

il programma di popolamento 
- normalizza l'input
- controlla se l'entry normalizzata è già presente
  - se non è presente inserisce l'entry normalizzata
- controlla se l'entry è completa


## Tipologie di deck da generare

Sono utili più tipologie di deck, perché l’apprendimento linguistico non riguarda solo la memorizzazione di parole isolate, ma anche il riconoscimento dell’uso reale delle parole nelle frasi e la comprensione delle strutture grammaticali.

Una prima distinzione fondamentale è tra deck orientati ai lemmi e deck orientati alle frasi.

### **deck orientati ai lemmi**  
hanno come unità principale la parola o il lemma. 
Servono a costruire progressivamente il vocabolario di base e possono contenere informazioni come significato, categoria grammaticale, frequenza, pronuncia, forme principali, traduzione, esempi brevi e note grammaticali essenziali. Questa tipologia è particolarmente utile per organizzare il lessico secondo criteri di frequenza, livello, lingua, argomento o difficoltà.

### **deck orientati alle frasi**   
Hanno invece come unità principale una frase completa, ho gruppi di poche frasi tipicament usate assieme come singola interazione comunicativa.
Servono a mostrare le parole nel loro contesto reale d’uso e permettono di allenare comprensione, sintassi, collocazioni, reggenze, ordine delle parole, particelle, preposizioni e costruzioni idiomatiche. Le frasi consentono di evitare che il lessico venga appreso in modo troppo astratto o isolato.

### **deck orientati alle strutture grammaticali o ai pattern**. 
non sono centrati su una singola parola né su una frase generica, ma su una costruzione linguistica ricorrente. Possono riguardare, per esempio, una reggenza verbale, l’uso di una particella, la posizione del verbo, una forma verbale, una costruzione con ausiliare o un pattern sintattico.

La distinzione tra lemmi, frasi e strutture è utile perché separa tre obiettivi didattici diversi:  
- acquisire vocabolario,  
- osservare l’uso in contesto,  
- comprendere i meccanismi grammaticali.  

Senza questa distinzione, si rischierebbe di inserire troppa grammatica nei deck lessicali o di usare i deck di frasi per scopi troppo diversi tra loro.

Per lingue come il tedesco e il giapponese questa separazione è particolarmente importante.  
Nel tedesco occorre gestire genere, plurale, casi, reggenze, preposizioni e posizione del verbo.  
Nel giapponese occorre invece prestare attenzione a particelle, forme verbali, livelli di cortesia, kanji, kana e segmentazione delle frasi.  


## Pipeline 

### Formati

I formati dei dati utilizzati nella pipeline devono essere standardizzati, si ipotizza quanto segue:

##### Formato files .txt
UTF-8 senza BOM, 
- normalizzare Unicode quando necessario,  
- conservare correttamente gli a-capo e gestire in modo esplicito eventuali caratteri di controllo, spazi anomali o simboli non testuali.  

##### Formato sottotitoli primario: 
VTT


### Pipeline - Overview sequenza steps

Si tenterà di applicare, ad alto livello una sequenza **concettuale** standard.   
A livello tecnico tale sequenza potrebbe rilevarsi non la migliore e non si esclude di implementare una pipeline leggermente diversa.

Al momento è la seguente: 

- 10 identificazione delle fonti 
- 20 import fonti
- 30 estrazione dati e metadati  
- 40 normalizzazione dati
- 50 arricchimento e popolamento DB
- 60 generazione

### Conservazione dei metadati negli I/O della pipeline

Anche se l’output principale dei primi passi può essere un file plain text UTF-8, è utile prevedere la conservazione dei metadati, perché questi dati permettono controlli, debug, revisione manuale, tracciabilità e generazione futura di carte più ricche.

Per esempio,  
- una frase estratta da un sottotitolo può avere informazioni come file sorgente, numero del sottotitolo, tempo iniziale, tempo finale, lingua, eventuale file audio collegato e qualità stimata della trascrizione.   
- Una frase estratta da un documento può avere informazioni come nome file, titolo, sezione o posizione approssimativa.  
Questi dati non sono sempre necessari per generare il deck, ma possono diventare importanti nelle fasi successive di arricchimento e revisione.  


##### Ipotesi: header e metadati

Per i dati in formato testo si ipotizza che
- può essere presente un header opzionale per metadati relativo all'intero file. 
- ogni riga può includere metadati relativi unicamente allìentry in essa contenuta  

Per l'header si potrà invece valutare in futuro una struttura simile al frontmatter **se e solo se consente i principi dichiarati in questo documento**



I file dovranno essere elaborabili anche senza headerper sviluppare passi di pipeline in grado di prendere in input anche files non prodotti dalla pipeline, quindi l'header è:  
- opzionale per files esterni ma 
- obbligatorio per i file prodotti dalla pipelien. 

L'header non deve forzare una struttura globale ma essere composto di singole linee, opzionali, utilizzabili autonomamente.  

Le righe di header saranno opzionali e saranno identificate dal prefisso:  
    /#/


Una riga di header potrà dichiarare il marker usato nel file per separare il contenuto principale dai metadati della riga. 
Il marker sarà quindi configurabile file per file. Dovrà essere una breve sequenza di caratteri ASCII base, scelta in modo da avere probabilità molto bassa di comparire nel testo naturale.
Si ipotizza:
    /#/ marker: #1#

*In questo esempio il marker `#1#` specifica che, in quel file, tutto ciò che precede `#1#` è il contenuto principale, mentre tutto ciò che segue `#1#` contiene dati o metadati relativi alla riga.
*

I file dovranno essere elaborabili anche senza marker di riga.  
In questo caso ogni riga dati sarà interpretata come contenuto puro, senza metadati di riga.

Esempio di file di frasi:

    /#/ format: anki-targets-v1
    /#/ type: sentence
    /#/ language: de
    /#/ marker: #1#
    /#/ metadata-format: undefined

    Ich gehe morgen zur Schule. #1# source=film1.srt; start=00:01:12.500; end=00:01:15.200; audio=sent_0001.mp3
    Das ist ein gutes Beispiel. #1# source=film1.srt; start=00:03:01.100; end=00:03:04.000; audio=sent_0002.mp3

Esempio di file di lemmi:

    /#/ format: anki-targets-v1
    /#/ type: lemma
    /#/ language: ja
    /#/ marker: #1#
    /#/ metadata-format: undefined

    食べる #1# source=lesson01.txt; count=8; pos=VERB
    学校 #1# source=lesson01.txt; count=5; pos=NOUN

Il formato dei metadati non viene fissato in questa fase. 
Potrà essere definito successivamente. Le alternative principali sono:

- coppie `key=value` separate da punto e virgola;
- JSON compatto;
- formato YAML-like;
- una struttura simile al frontmatter;
- altro formato strutturato.

Per i metadati di riga, la soluzione tecnicamente più robusta sembra JSON compatto, perché è standard, facilmente validabile, supportato da tutti i principali linguaggi di programmazione e meno ambiguo rispetto a formati liberi basati su `;` o `=`.

Esempio con JSON compatto:

    Ich gehe morgen zur Schule. #1# {"source":"film1.srt","start":"00:01:12.500", "end":"00:01:15.200","audio":"sent_0001.mp3","lang":"de"}


##### Regole minime di parsing

Il parser dovrà applicare alcune regole minime:

- una riga di header inizia sempre con `/#/`;
- il marker può essere dichiarato nell’header;
- il marker vale solo per il file corrente;
- se non è presente header, il file deve essere comunque elaborabile;
- se non è dichiarato un marker, ogni riga dati deve essere considerata contenuto puro;
- se una riga dati non contiene il marker dichiarato, deve essere considerata contenuto puro senza metadati;
- se il marker compare più di una volta nella stessa riga, il parser dovrà usare la prima occorrenza come separatore;
- il formato dei metadati dovrà essere dichiarato nell’header quando verrà stabilizzato;
- eventuali errori nei metadati non dovranno impedire necessariamente l’estrazione del contenuto principale.

Questa struttura consente di mantenere i file semplici, leggibili e modificabili manualmente, ma allo stesso tempo sufficientemente formali per essere elaborati automaticamente.

Il vantaggio principale è che il formato non dipende da un marker globale fisso. Ogni file può dichiarare il proprio marker, riducendo il rischio di conflitti con il contenuto. Inoltre, lo stesso schema può essere usato per file di lemmi, frasi e, in futuro, strutture grammaticali.

#### Formati intermedi consigliati

Per la massima semplicità, i file di target potranno essere normali file di testo UTF-8.

Per i lemmi, il formato minimo sarà:

    lemma_o_token_1
    lemma_o_token_2
    lemma_o_token_3

Per le frasi, il formato minimo sarà:

    frase candidata 1
    frase candidata 2
    frase candidata 3

Il formato minimo deve rimanere supportato, perché è semplice da generare, leggere e modificare manualmente.

Quando servono metadati, si userà invece il formato con header opzionale e marker dichiarato nel file.

Esempio minimo con header e marker:

    /#/ format: anki-targets-v1
    /#/ type: sentence
    /#/ language: de
    /#/ marker: #1#
    /#/ metadata-format: json

    Ich gehe morgen zur Schule. #1# {"source":"film1.srt","start":"00:01:12.500","end":"00:01:15.200"}
    Das ist ein gutes Beispiel. #1# {"source":"film1.srt","start":"00:03:01.100","end":"00:03:04.000"}

In sintesi, il sistema dovrà supportare due livelli:

- formato semplice, con una voce per riga e senza metadati;
- formato auto-descrittivo, con header opzionale, marker configurabile e metadati in-line.

Questa scelta permette di mantenere semplice l’uso iniziale, ma lascia spazio a informazioni più ricche quando saranno necessarie.

### Passi della pipeline  
#### Fase 10: Identificazione di fonti e input  

Ricerca di siti e input (video, corpus, files di testo Etc. )

La fonte iniziale potrà essere costituita da 
- file audio, 
- file video, 
- dati testuali:
  - files di sottotitoli, 
  - documenti strutturati, 
  - pagine HTML, 
  - file Markdown, 
  - file DOCX 
  - normali file di testo. 
 
In questa fase il sistema dovrà solo 
- eventualmente cercare fonti, eventualmente supportato dall'AI
- identificare il tipo di input   
- quando possibile validare la correttezza (non corrotto) prima dell'import (raramente possibile?)


#### Fase 20: import input  
- importare
- validare (contiene contenuti attesi, non è corrotta)
- eventualmente popolare una struttura dati interna di situazione iniziale per consentire la scelta dei passi di elaborazione da effettuare


#### Fase 30: estrazione dati e metadati

##### Obiettivo:  
L’obiettivo 
- non è ancora generare direttamente contenuti didattici per l'utente finale. 
- è preparare dati di input di buona qualità, niente di più. 

##### Azioni  

Esempi: 
estrarre audio da video, generare sottotitoli da audio o video etc. 

I dati estratti verranno scritti in formati standard (per la pipeline), relativamente semplici, generali e flessibili, autodescrittivi e riutilizzabili.

Nel software che elabora la pipeline eventuale aggiornamento di struttura du memoria relativa alla situazione globale degli input disponibili  


##### Indentificazione Primitive

//ev:finoqui

Tentativo di identificare primitive riusabili

- se presente video 
  - se non presente audio 
    - estrarre audio da video

- se presente audio o video
  - se non presenti sottotitoli l2 
    - da audio generare sottotitoli l2
  - produrre sottotitoli l1 relativi a dialoghi atomici
  - se non presenti sottotitoli l1
    - da sottotitoli l1 generare sottotitoli l2

def. dialogo atomico:
- singola frase oppure 
- più frasi che hanno senso didattico studiato assieme, come singolo "scambio" di comunicazione
In pratica si tratterò di files di sottotitoli dove più fasi sono aggregate quando ha senso
- Va analizzato quale formato di sottotitoli si presta meglio a questo, utile un formato che consenta commenti 
produzione dialoghi atomici
  - da uno o più files, anche in lungue parallete estrazione di dialoghi atomici
    - viene prodotto un nuovo file di sottotitoli
    - per produrre dialoghi atomici per il momento verranno usati solo files di sottotitoli, non normali files di testo
Nomi file per brani testuali:  
    probabilmente **&lt;nome file audio&gt;_&lt;timestamp&gt;_&lt;primi 20 caratteri testo&gt;**


- se richiesti fotogrammi AND presenti video AND presenti sottotitoli l2:
  - da video estrarre fotogrammi, in coincidenza di uno specifico file di sottotitoli, default l2

- se richiesti brani atomici in file e disponibili file di sottotitoli/dialoghi atomici:
  - da file di sottotitoli/scambi-a estrarre testo entry in un file dedicato
  - da file audio estrarre testo entry in un file dedicato


#### Fase 40: Normalizzazione dati 

##### Applicabilità:
Testi prodotti dalla pipeline

Bisogna distinguere fra parole singole e frasi

Serve a rendere il testo più stabile e più adatto alle elaborazioni successive.

La normalizzazione può includere: 
- la conversione coerente degli spazi, 
- la rimozione di elementi tecnici non linguistici, 
- la gestione degli a-capo, 
- la normalizzazione Unicode, 
- l’eliminazione di markup residuo e 
- la correzione di artefatti tipici dei sottotitoli o dell’OCR, se presenti.

Per il giapponese: 
occorre particolare attenzione alla normalizzazione Unicode, alla punteggiatura, agli spazi eventualmente introdotti artificialmente e alla successiva segmentazione in token.  

Per il tedesco: 
occorre preservare correttamente maiuscole, umlaut, ß, segni di punteggiatura e apostrofi significativi.


##### Normalizzazione per deck di lemmi  

Il testo dovrà  essere tokenizzato e, quando possibile, lemmatizzato. 

In questa fase non è opportuno rimuovere automaticamente le stopword, perché parole funzionali come articoli, pronomi, preposizioni, particelle, ausiliari e connettivi sono importanti nelle liste lessicali di base. 

La rimozione o il filtraggio delle stopword potrà essere eventualmente previsto come opzione successiva, non come comportamento predefinito.

##### Normalizzazione per deck di frasi  

L’unità principale sarà la frase o un segmento testuale equivalente.  

Nei sottotitoli non sempre una riga corrisponde a una frase completa; quindi occorre prevedere una fase di ricostruzione o almeno di controllo dei segmenti.  
Questa elaborazione peerò potrebbe essere parte della costruzione delle interazioni linguistiche nel passo di arricchimento.

L’obiettivo è produrre unità abbastanza complete da avere senso come esempi didattici.


#### Fase 50:Arricchimento

##### Fase 50: arricchimento lemmi  
Per i deck di lemmi, il formato iniziale può essere un file UTF-8 con un elemento per riga.  
Ogni riga rappresenta un token, una parola o un lemma candidato. 
In questa fase il file contiene solo i target lessicali, non ancora informazioni arricchite. Per esempio, non contiene ancora traduzioni, frequenze, esempi, coniugazioni o spiegazioni grammaticali.


##### Fase 50: arricchimento frasi  
Per i deck di frasi, il formato iniziale può essere un file UTF-8 con una frase o un segmento per riga. 
Ogni riga rappresenta una frase candidata per la generazione di carte. Anche in questo caso la frase non contiene ancora necessariamente informazioni arricchite, come traduzione, analisi grammaticale, parole chiave o note didattiche.
Va tenuta presente la possibilità di generare piccoli files audio corrispondenti a ogni frase di testo, il nome file potrebbe essere uno dei metadati che seguono il marker.


Per i futuri deck grammaticali o strutturali, il sistema dovrà prevedere la possibilità di estrarre pattern o costruzioni ricorrenti. In questa fase non è necessario implementare completamente tale funzione, ma l’architettura non deve impedirla. Per questo motivo è importante conservare, quando possibile, il legame tra frase, fonte, posizione nel testo ed eventuali metadati.


letto: 3
