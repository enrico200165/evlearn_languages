# Obiettivi

Gli obiettivi sono:
- generare decks a partire da una lista di parole  


## Tipologie di deck da generare

Sono utili più tipologie di deck, perché l’apprendimento linguistico non riguarda solo la memorizzazione di parole isolate, ma anche il riconoscimento dell’uso reale delle parole nelle frasi e la comprensione delle strutture grammaticali.

Una prima distinzione fondamentale è tra deck orientati ai lemmi e deck orientati alle frasi.

**deck orientati ai lemmi**  
hanno come unità principale la parola o il lemma. 
Servono a costruire progressivamente il vocabolario di base e possono contenere informazioni come significato, categoria grammaticale, frequenza, pronuncia, forme principali, traduzione, esempi brevi e note grammaticali essenziali. Questa tipologia è particolarmente utile per organizzare il lessico secondo criteri di frequenza, livello, lingua, argomento o difficoltà.

**deck orientati alle frasi**   
hanno invece come unità principale una frase completa. 
Servono a mostrare le parole nel loro contesto reale d’uso e permettono di allenare comprensione, sintassi, collocazioni, reggenze, ordine delle parole, particelle, preposizioni e costruzioni idiomatiche. Le frasi consentono di evitare che il lessico venga appreso in modo troppo astratto o isolato.

**deck orientati alle strutture grammaticali o ai pattern**. 
non sono centrati su una singola parola né su una frase generica, ma su una costruzione linguistica ricorrente. Possono riguardare, per esempio, una reggenza verbale, l’uso di una particella, la posizione del verbo, una forma verbale, una costruzione con ausiliare o un pattern sintattico.

La distinzione tra lemmi, frasi e strutture è utile perché separa tre obiettivi didattici diversi: - acquisire vocabolario, 
- osservare l’uso in contesto,  
- comprendere i meccanismi grammaticali.  

Senza questa distinzione, si rischierebbe di inserire troppa grammatica nei deck lessicali o di usare i deck di frasi per scopi troppo diversi tra loro.

Per lingue come il tedesco e il giapponese questa separazione è particolarmente importante.  
Nel tedesco occorre gestire genere, plurale, casi, reggenze, preposizioni e posizione del verbo.  Nel giapponese occorre invece prestare attenzione a particelle, forme verbali, livelli di cortesia, kanji, kana e segmentazione delle frasi.  


## Pipeline generale per la preparazione dell’input dei deck

### Macrofase: estrazione raw-input + metadati

Questa macro-fase avrà lo scopo di estrarre il testo da fonti eterogenee, come audio, video, sottotitoli, documenti e file testuali, in formati intermedi semplici, controllabili e riutilizzabili.

Le tipologie di deck considerate nella progettazione generale saranno almeno tre: 
deck orientati ai lemmi, deck orientati alle frasi e deck orientati alle strutture grammaticali.   Nella prima fase di sviluppo l’attenzione sarà posta soprattutto sui deck di lemmi e sui deck di frasi, ma l’architettura dovrà essere sufficientemente generale da poter supportare in seguito anche i deck grammaticali o strutturali.

La pipeline può essere organizzata in una sequenza di passi.

#### 1. Acquisizione della fonte

La fonte iniziale potrà essere costituita da file audio, video, file di sottotitoli, documenti strutturati, pagine HTML, file Markdown, file DOCX oppure normali file di testo. In questa fase il sistema dovrà solo identificare il tipo di input e prepararlo per il passo successivo.

#### 2. Speech-to-text, quando necessario

Se l’input è un file audio o video, il primo passo sarà il riconoscimento automatico del parlato.  L’output preferibile di questo passaggio non dovrebbe essere un semplice file di testo, ma un file di sottotitoli, perché i sottotitoli permettono di conservare anche la segmentazione temporale del parlato.

L’output consigliato di questo passo è quindi un file di sottotitoli, per esempio in formato SRT o VTT. 
Al momento si sceglie .srt per semplicità.
In seguito sarà possibile estrarre il testo, ma mantenere inizialmente le informazioni temporali è utile per eventuali controlli, revisioni, allineamenti audio-testo o generazione di esempi collegati al punto esatto del video o dell’audio.

#### 3. Estrazione del testo dai formati sorgente

Il passo successivo consiste nell’estrarre testo leggibile dai diversi formati supportati: sottotitoli, DOCX, Markdown, HTML, TXT e altri formati testuali o documentali.

L’output di questo passo può essere un file plain text in UTF-8. 
UTF-8 è adatto per rappresentare testi in lingue diverse, compresi tedesco e giapponese.  
È però opportuno prevedere alcune regole tecniche: usare UTF-8 senza BOM, normalizzare Unicode quando necessario, conservare correttamente gli a-capo e gestire in modo esplicito eventuali caratteri di controllo, spazi anomali o simboli non testuali.  

Questo primo testo estratto non dovrebbe ancora essere considerato materiale didattico pronto.  
È semplicemente il contenuto testuale ottenuto dalla fonte.

#### 4. Normalizzazione del testo

Dopo l’estrazione è opportuno prevedere un passaggio di normalizzazione. Questo passaggio serve a rendere il testo più stabile e più adatto alle elaborazioni successive.

La normalizzazione può includere la conversione coerente degli spazi, la rimozione di elementi tecnici non linguistici, la gestione degli a-capo, la normalizzazione Unicode, l’eliminazione di markup residuo e la correzione di artefatti tipici dei sottotitoli o dell’OCR, se presenti.

Per il giapponese occorre particolare attenzione alla normalizzazione Unicode, alla punteggiatura, agli spazi eventualmente introdotti artificialmente e alla successiva segmentazione in token.  
Per il tedesco occorre preservare correttamente maiuscole, umlaut, ß, segni di punteggiatura e apostrofi significativi.

#### 5. Segmentazione in unità linguistiche

Il testo normalizzato deve poi essere segmentato in unità linguistiche adatte alle diverse tipologie di deck.

Per i deck di frasi, l’unità principale sarà la frase o un segmento testuale equivalente. Nei sottotitoli non sempre una riga corrisponde a una frase completa; quindi occorre prevedere una fase di ricostruzione o almeno di controllo dei segmenti. L’obiettivo è produrre unità abbastanza complete da avere senso come esempi didattici.

Per i deck di lemmi, l’unità principale sarà invece il token o il lemma.  
Il testo dovrà quindi essere tokenizzato e, quando possibile, lemmatizzato. In questa fase non è opportuno rimuovere automaticamente le stopword, perché parole funzionali come articoli, pronomi, preposizioni, particelle, ausiliari e connettivi sono importanti nelle liste lessicali di base. La rimozione o il filtraggio delle stopword potrà essere eventualmente previsto come opzione successiva, non come comportamento predefinito.

#### 6. Estrazione dei target per tipologia di deck

A questo punto la pipeline dovrà produrre file di target separati per ciascuna tipologia di deck.


Per i deck di lemmi, il formato iniziale può essere un file UTF-8 con un elemento per riga.  
Ogni riga rappresenta un token, una parola o un lemma candidato. In questa fase il file contiene solo i target lessicali, non ancora informazioni arricchite. Per esempio, non contiene ancora traduzioni, frequenze, esempi, coniugazioni o spiegazioni grammaticali.


Per i deck di frasi, il formato iniziale può essere un file UTF-8 con una frase o un segmento per riga. 
Ogni riga rappresenta una frase candidata per la generazione di carte. Anche in questo caso la frase non contiene ancora necessariamente informazioni arricchite, come traduzione, analisi grammaticale, parole chiave o note didattiche.
Va tenuta presente la possibilità di generare piccoli files audio corrispondenti a ogni frase di testo, il nome file potrebbe essere uno dei metadati che seguono il marker.


Per i futuri deck grammaticali o strutturali, il sistema dovrà prevedere la possibilità di estrarre pattern o costruzioni ricorrenti. In questa fase non è necessario implementare completamente tale funzione, ma l’architettura non deve impedirla. Per questo motivo è importante conservare, quando possibile, il legame tra frase, fonte, posizione nel testo ed eventuali metadati.

#### 7. Conservazione dei metadati

Anche se l’output principale dei primi passi può essere un file plain text UTF-8, è utile prevedere la conservazione dei metadati, perché questi dati permettono controlli, debug, revisione manuale, tracciabilità e generazione futura di carte più ricche.

Per esempio, una frase estratta da un sottotitolo può avere informazioni come file sorgente, numero del sottotitolo, tempo iniziale, tempo finale, lingua, eventuale file audio collegato e qualità stimata della trascrizione. Una frase estratta da un documento può avere informazioni come nome file, titolo, sezione o posizione approssimativa. Questi dati non sono sempre necessari per generare il deck, ma possono diventare importanti nelle fasi successive di arricchimento e revisione.

##### Ipotesi: header e metadati in-line

Si ipotizza di usare file testuali UTF-8 auto-descrittivi.

Le righe di header saranno opzionali e saranno identificate dal prefisso:

    /#/

I file dovranno comunque essere elaborabili anche senza header.

Una riga di header potrà dichiarare il marker usato nel file per separare il contenuto principale dai metadati della riga. Per esempio:

    /#/ marker: #1#

In questo esempio il marker `#1#` specifica che, in quel file, tutto ciò che precede `#1#` è il contenuto principale, mentre tutto ciò che segue `#1#` contiene dati o metadati relativi alla riga.

Il marker sarà quindi configurabile file per file. Dovrà essere una breve sequenza di caratteri ASCII base, scelta in modo da avere probabilità molto bassa di comparire nel testo naturale.

I file dovranno essere elaborabili anche senza marker. In questo caso ogni riga dati sarà interpretata come contenuto puro, senza metadati di riga.

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

Il formato dei metadati non viene fissato in questa fase. Potrà essere definito successivamente. Le alternative principali sono:

- coppie `key=value` separate da punto e virgola;
- JSON compatto;
- formato YAML-like;
- una struttura simile al frontmatter;
- altro formato strutturato.

Per i metadati di riga, la soluzione tecnicamente più robusta sembra JSON compatto, perché è standard, facilmente validabile, supportato da tutti i principali linguaggi di programmazione e meno ambiguo rispetto a formati liberi basati su `;` o `=`.

Esempio con JSON compatto:

    Ich gehe morgen zur Schule. #1# {"source":"film1.srt","start":"00:01:12.500","end":"00:01:15.200","audio":"sent_0001.mp3","lang":"de"}

Per i metadati globali del file si potrà invece valutare in futuro una struttura simile al frontmatter. Il frontmatter è adatto a descrivere l’intero file, ma non è la scelta più naturale per descrivere i metadati di ogni singola riga.

Una possibile evoluzione del formato potrà quindi prevedere:

- header iniziale per i metadati globali del file;
- marker dichiarato nell’header;
- righe dati con contenuto principale e metadati di riga;
- metadati di riga preferibilmente in JSON compatto.

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

#### 8. Formati intermedi consigliati

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

#### 9. Obiettivo della macro-sezione elaborativa

L’obiettivo della macro-sezione non è ancora generare direttamente le carte Anki complete. L’obiettivo è preparare input puliti, coerenti e separati per le diverse tipologie di deck.

La generazione delle carte, con aggiunta di informazioni come traduzioni, spiegazioni, esempi, pronuncia, categoria grammaticale, frequenza, note d’uso o audio, dovrà appartenere a una fase successiva della pipeline.

Questa separazione consente di mantenere il sistema più controllabile: prima si estraggono e normalizzano i target, poi si arricchiscono, poi si generano le carte.
