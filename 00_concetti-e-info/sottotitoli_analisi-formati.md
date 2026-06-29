## Formati di sottotitoli per pipeline software e apprendimento linguistico

Destinatari:  
programmatori esperti che devono progettare strumenti di generazione, parsing, conversione, traduzione, sincronizzazione e visualizzazione di sottotitoli.

Obiettivo:  
scegliere il formato corretto in base al modello dati che si vuole conservare, cioè in base alle funzionalità che si vuole avere la possibilità di di implementare.

---

## Contenuti/funzionalità files sottotitoli    

Un file di sottotitoli non contiene solo testo. Può contenere, a seconda del formato:

* timestamp di inizio e fine;
* testo visibile;
* lingua;
* parlante;
* posizione sullo schermo;
* stile grafico;
* livelli sovrapposti;
* note non visualizzate;
* metadati temporizzati;
* informazioni per accessibilità;
* allineamento parola per parola;
* più tracce o più lingue.

Per progettare una pipeline software occorre distinguere tre livelli:

1. Formato sorgente/interno  
   Deve contenere/conservare più informazione possibile. E' il master data.

2. Formato di editing
   Deve essere comodo da correggere e sincronizzare.

3. Formato di distribuzione
   Deve funzionare nei player, nei browser o nelle piattaforme finali.
  


Errore comune:  
usare SRT come formato interno principale.  
È comodo, ma perde quasi tutte le informazioni strutturate.

---

## 2. I 5 formati più adatti

Per un sistema moderno, soprattutto se orientato ad apprendimento linguistico, i cinque formati più utili sono:

1. WebVTT
2. ASS/SSA
3. SRT
4. TTML/IMSC
5. JSON/TSV strutturato, in particolare output Whisper o formato interno custom

Il quinto non è un formato “classico” da player video, ma è spesso il più importante lato programmazione.  

Serve come formato intermedio ricco, da cui esportare poi SRT, VTT, ASS o TTML.

---

## WebVTT (.vtt)  

WebVTT è il formato più adatto quando il target è

* web e HTML5;
* applicazioni didattiche;
* player custom;
* ambienti in cui servono più tracce temporizzate associate allo stesso audio o video.

Un file WebVTT inizia con l’intestazione `WEBVTT`, seguita da uno o più cue temporizzati:

```
WEBVTT

00:00:01.000 --> 00:00:04.000
Hello, how are you?
```

Fonte: MDN - https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API/Web_Video_Text_Tracks_Format

#### WebVTT: Modello dati

WebVTT lavora con cue temporizzati.
Un cue è un blocco associato a un intervallo temporale.

Rispetto a SRT, WebVTT può gestire meglio:

* parlanti;
* classi;
* note;
* regioni;
* posizionamento;
* metadati temporizzati;
* capitoli;
* integrazione con HTML, CSS e JavaScript.

Esempio concettuale con parlante:

```
WEBVTT

00:00:01.000 --> 00:00:04.000
<v John>Hello, how are you?
```

L’indicazione `<v John>` segnala che il cue è pronunciato dal parlante John. Questa informazione può essere usata dal browser, dal player o da codice JavaScript/CSS, ma non tutti i player la mostrano nello stesso modo.

### Uso da parte di piattaforme e tool

WebVTT è usato nel web tramite l’elemento HTML `<track>`.

Un elemento `<track>` non è il file dei sottotitoli. È un tag HTML inserito dentro `<video>` o `<audio>` per collegare il media a una traccia testuale temporizzata.

Nella forma più comune, il tag `<track>` punta a un file esterno `.vtt` tramite l’attributo `src`.

Esempio minimo:

```
<video controls src="lezione.mp4">
    <track
        kind="subtitles"
        src="sottotitoli-it.vtt"
        srclang="it"
        label="Italiano"
        default>
</video>
```

In questo esempio:

* `lezione.mp4` è il file video;
* `sottotitoli-it.vtt` è il file WebVTT esterno;
* `<track>` è l’elemento HTML che collega il video alla traccia di sottotitoli;
* `kind="subtitles"` indica che la traccia contiene sottotitoli;
* `srclang="it"` indica la lingua della traccia;
* `label="Italiano"` è il nome mostrato all’utente nel menu del player;
* `default` indica la traccia da attivare automaticamente, salvo preferenze diverse dell’utente.

Esempio di file `sottotitoli-it.vtt`:

```
WEBVTT

00:00:00.000 --> 00:00:03.000
Benvenuti alla lezione.

00:00:03.000 --> 00:00:06.000
In questo video si parla di sottotitoli WebVTT.
```

Un video HTML può avere più elementi `<track>`, per esempio uno per l’italiano, uno per l’inglese, uno per il tedesco, uno per captions accessibili e uno per metadati temporizzati.

Esempio con più lingue:

```
<video controls src="lezione.mp4">
    <track
        kind="subtitles"
        src="sottotitoli-it.vtt"
        srclang="it"
        label="Italiano"
        default>

    <track
        kind="subtitles"
        src="subtitles-en.vtt"
        srclang="en"
        label="English">

    <track
        kind="subtitles"
        src="untertitel-de.vtt"
        srclang="de"
        label="Deutsch">
</video>
```

In questo caso il video è uno solo, ma le tracce testuali sono tre file separati.

Esempio con captions:

```
<video controls src="intervista.mp4">
    <track
        kind="captions"
        src="captions-it.vtt"
        srclang="it"
        label="Italiano per non udenti"
        default>
</video>
```

`kind="subtitles"` si usa di norma per sottotitoli destinati a chi sente l’audio ma non capisce la lingua.

`kind="captions"` si usa per trascrizioni più complete, spesso nella stessa lingua dell’audio, che possono includere anche indicazioni come `[musica]`, `[applausi]`, `[rumore di porta]`.

Esempio con metadati:

```
<video controls src="lezione.mp4">
    <track
        kind="metadata"
        src="capitoli.vtt"
        label="Capitoli">
</video>
```

Una traccia `metadata` normalmente non viene mostrata come sottotitolo. Può però essere letta via JavaScript per sincronizzare eventi con il video, per esempio mostrare titoli di capitoli, immagini, quiz o note.

Il fatto che HTML usi `<track>` non significa che ogni piattaforma esponga sempre un file `.vtt` separato all’utente. Nel caso standard HTML/WebVTT, la traccia è normalmente un file esterno indicato con `src`. Piattaforme video più complesse possono invece gestire sottotitoli e captions internamente, tramite interfacce proprie, API o sistemi di conversione.

MDN documenta l’uso di WebVTT per sottotitoli, captions, capitoli e tracce temporizzate.
Fonte: MDN - https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API/Web_Video_Text_Tracks_Format

MDN documenta anche l’elemento HTML `<track>`, usato dentro `<video>` e `<audio>` per associare al media una o più tracce testuali temporizzate.
Fonte: MDN - https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/track

Vimeo supporta file SRT e WebVTT per captions e sottotitoli, e raccomanda WebVTT.
Fonte: Vimeo Help - https://help.vimeo.com/hc/en-us/articles/21956884955537-How-to-add-captions-or-subtitles-to-my-video

YouTube supporta WebVTT, ma con limitazioni rispetto allo styling: il posizionamento è supportato, mentre lo styling è limitato.
Fonte: YouTube Help - https://support.google.com/youtube/answer/2734698?hl=en

### Librerie Python

Librerie e strumenti utili:

* webvtt-py;
* pycaption;
* pysubs2;
* parser custom basati su parsing testuale;
* Whisper e strumenti di speech-to-text capaci di esportare trascrizioni in VTT.

`webvtt-py` è una libreria Python specifica per leggere, scrivere e convertire file WebVTT.
Fonte: webvtt-py - https://webvtt-py.readthedocs.io/

`pycaption` è una libreria Python orientata alla conversione tra formati di caption e sottotitoli. Supporta WebVTT, ma alcune informazioni di styling possono essere perse o semplificate durante la conversione.
Fonte: pycaption - https://pycaption.readthedocs.io/en/stable/supported_formats.html

`pysubs2` supporta WebVTT come formato time-based simile a SubRip, ma non implementa pienamente tutte le feature specifiche di WebVTT, come styling e alignment.
Fonte: pysubs2 - https://pysubs2.readthedocs.io/en/latest/supported-formats.html

Whisper può generare output in formato VTT, ma è uno strumento di trascrizione speech-to-text, non una libreria specializzata nella manipolazione completa di WebVTT.
Fonte: OpenAI Whisper CLI - https://openai-whisper.mintlify.app/guides/cli-usage

### Vantaggi per programmatori

WebVTT è ottimo se si vuole:

* integrare sottotitoli in un player web;
* manipolare tracce via JavaScript;
* associare più tracce allo stesso video;
* creare metadati temporizzati;
* costruire esercizi linguistici sincronizzati con audio/video.

### Limiti

Il singolo file WebVTT non è il modo più pulito per contenere molte lingue parallele nello stesso documento.
Il modello naturale è: più file, uno per traccia.

Per esempio:

```
video_en.vtt
video_it.vtt
video_de.vtt
video_glossary.vtt
```

Il player o l’applicazione devono poi decidere cosa mostrare.

In HTML standard, questo significa associare più elementi `<track>` allo stesso video:

```
<video controls src="video.mp4">
    <track kind="subtitles" src="video_en.vtt" srclang="en" label="English">
    <track kind="subtitles" src="video_it.vtt" srclang="it" label="Italiano">
    <track kind="subtitles" src="video_de.vtt" srclang="de" label="Deutsch">
    <track kind="metadata" src="video_glossary.vtt" label="Glossario">
</video>
```

### Valutazione

WebVTT è il formato migliore per applicazioni web didattiche multilingua, soprattutto quando servono più tracce sincronizzate con lo stesso audio o video, integrazione con player HTML5 e possibilità di usare JavaScript per costruire attività interattive.

---

## ASS/SSA (.ass, .ssa)

ASS/SSA è il formato più potente per  
- layout grafico,  
- sottotitoli sovrapposti,  
- doppia lingua visibile contemporaneamente e  
- karaoke.  

È il formato naturale di Aegisub, tool gratuito e open source per creare, sincronizzare e stilizzare sottotitoli.  
Fonte: Aegisub - [https://aegisub.org/](https://aegisub.org/)

pysubs2 documenta ASS/SSA come formato nativo e indica supporto a rich text formatting, animazioni e grafica vettoriale.  
Fonte: pysubs2 - [https://pysubs2.readthedocs.io/en/latest/supported-formats.html](https://pysubs2.readthedocs.io/en/latest/supported-formats.html)

### Modello dati

Un file ASS contiene sezioni. Le più importanti sono:

* Script Info;
* Styles;
* Events.

Gli eventi contengono righe di dialogo con:

* layer;
* start;
* end;
* style;
* name;
* margin;
* effect;
* text.

Esempio concettuale:

```
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,English,,0,0,0,,Hello, how are you?
Dialogue: 1,0:00:01.00,0:00:04.00,Italian,,0,0,0,,Ciao, come stai?
```

Questa struttura permette di mostrare due lingue nello stesso intervallo temporale con stili e posizioni diverse.

### Uso da parte di piattaforme e tool

ASS/SSA è molto usato in:

* Aegisub;
* VLC;
* mpv;
* MKV;
* fansub;
* anime;
* video con sottotitoli hardcoded;
* pipeline FFmpeg.

Non è però il formato ideale per piattaforme web standard o social media.  
Molte piattaforme ignorano lo styling o richiedono conversione.  

### Librerie Python

La libreria più adatta è pysubs2.

Con pysubs2 si può:

* leggere ASS;
* modificare eventi;
* modificare stili;
* convertire tra ASS, SRT, WebVTT e altri formati;
* fare retiming;
* creare sottotitoli multilingua visivamente separati.

### Vantaggi per programmatori

ASS/SSA è ideale se si vuole produrre un output finale visivamente ricco:

* **lingua originale in alto traduzione in basso**;  
* **parole evidenziate**;
* **colori diversi per parti del discorso**;
* karaoke sillabico;
* **note grammaticali laterali**;
* parlanti con stili diversi;
* sovrapposizioni controllate.

### Limiti

ASS/SSA è eccellente per rendering, non per interoperabilità universale.

La conversione da ASS a SRT è fortemente lossy:

* si perdono stili;
* si perdono livelli;
* si perde posizionamento;
* si perdono animazioni;
* si appiattiscono eventi paralleli.

### Valutazione

ASS/SSA è il **formato migliore per mostrare due o più lingue contemporaneamente in un singolo file di sottotitoli**.

---

## SRT / SubRip (.srt)

SRT è il formato **più diffuso e più semplice**.  
È utile come formato di esportazione universale, **non è utile come formato interno ricco**.

YouTube raccomanda SRT come formato base per chi inizia, ma precisa che viene supportata solo la versione semplice, in UTF-8 e senza riconoscimento dello stile.
Fonte: YouTube Help - [https://support.google.com/youtube/answer/2734698?hl=en](https://support.google.com/youtube/answer/2734698?hl=en)

Esempio:

```
1
00:00:01,000 --> 00:00:04,000
Hello, how are you?
```

### Modello dati

SRT contiene essenzialmente:

* indice;
* inizio;
* fine;
* testo.

Non contiene in modo standard:

* lingua;
* parlante;
* stile complesso;
* layer;
* metadati;
* relazioni tra traduzione e originale;
* allineamento parola-parola.

### Uso da parte di piattaforme e tool

SRT è accettato quasi ovunque:

* YouTube;
* VLC;
* Vimeo;
* software di editing;
* player desktop;
* tool web;
* pipeline di generazione automatica.

### Librerie Python

Librerie utili:

* srt;
* pysrt;
* pysubs2;
* pycaption.

La libreria srt è molto semplice e adatta a parsing, modifica, compose, sorting e reindexing.  
Fonte: srt documentation - [https://srt.readthedocs.io/en/latest/api.html](https://srt.readthedocs.io/en/latest/api.html)

OpenAI Whisper può produrre direttamente SRT.  
Fonte: OpenAI Whisper - [https://github.com/openai/whisper](https://github.com/openai/whisper)

### Vantaggi per programmatori

SRT è ottimo per:

* export finale;
* compatibilità massima;
* debugging manuale;
* prototipi rapidi;
* dataset semplici;
* conversione verso formati più ricchi, quando non servono stili.

### Limiti

Per apprendimento linguistico SRT è debole.

È possibile scrivere due righe nello stesso blocco:

```
I went home.
Sono andato a casa.
```

Ma il file non conserva semanticamente che:

* la prima riga è inglese;
* la seconda è italiano;
* le due righe sono traduzioni;
* le parole corrispondono;
* esistono lemmi, glossari o note.

Quindi SRT è adatto come output, non come modello dati principale.

### Valutazione

SRT è il formato migliore per compatibilità, ma non per ricchezza informativa.

---

## TTML / IMSC (.ttml, .dfxp, .xml)

TTML è un formato XML per timed text.  
IMSC è un profilo TTML pensato per interoperabilità professionale nella consegna di sottotitoli e captions.  

W3C descrive IMSC come profilo per subtitle e caption delivery, con profili text-only e image-only.  
Fonte: W3C IMSC - [https://www.w3.org/TR/ttml-imsc1.1/](https://www.w3.org/TR/ttml-imsc1.1/)

### Modello dati

TTML/IMSC è più vicino a un documento XML strutturato che a un file di sottotitoli semplice.

Può rappresentare:

* gerarchie;
* regioni;
* stili;
* metadati;
* profili di rendering;
* vincoli di distribuzione;
* Unicode;
* contenuti testuali o image-based;
* informazioni utili per accessibilità.

Esempio concettuale:

```
<tt xmlns="http://www.w3.org/ns/ttml">
  <body>
    <div xml:lang="en">
      <p begin="00:00:01.000" end="00:00:04.000">
        Hello, how are you?
      </p>
    </div>
  </body>
</tt>
```

### Uso da parte di piattaforme e tool

TTML/IMSC è adatto a:

* broadcast;
* piattaforme OTT;
* workflow professionali;
* archiviazione;
* consegna a servizi che richiedono standard formali;
* conversione fra formati professionali.

YouTube supporta TTML in modo parziale, con supporto a styling e positioning.  
Fonte: YouTube Help - [https://support.google.com/youtube/answer/2734698?hl=en](https://support.google.com/youtube/answer/2734698?hl=en)  

### Librerie Python

Librerie utili:

* pycaption;
* pysubs2, con supporto base;
* lxml;
* xml.etree.ElementTree;
* validatori XML/TTML specifici.

pycaption legge e scrive DFXP/TTML e documenta supporto a più lingue.  
Fonte: pycaption - [https://pycaption.readthedocs.io/en/stable/supported_formats.html](https://pycaption.readthedocs.io/en/stable/supported_formats.html)

pysubs2 supporta TTML, ma avverte che il formato è complesso e che l’advanced styling non è completamente supportato dal parser.  
Fonte: pysubs2 - [https://pysubs2.readthedocs.io/en/latest/supported-formats.html](https://pysubs2.readthedocs.io/en/latest/supported-formats.html)

### Vantaggi per programmatori

TTML/IMSC è utile quando servono:

* validazione formale;
* scambio professionale;
* integrazione con workflow broadcast;
* conservazione strutturata;
* metadati;
* compatibilità con standard.

### Limiti

Per una piattaforma didattica custom è spesso troppo pesante.

Inoltre, il supporto delle librerie Python non è sempre completo.  
Manipolare TTML direttamente come XML è possibile, ma bisogna conoscere il profilo esatto.  

### Valutazione

TTML/IMSC è il formato migliore per interoperabilità professionale e archiviazione strutturata, ma non è il più agile per sviluppo rapido.

---

## JSON / TSV strutturato come formato intermedio

Questo non è un formato standard di sottotitoli per player, ma è spesso la scelta migliore come formato interno per programmatori esperti.

OpenAI Whisper supporta output JSON e TSV oltre a SRT e VTT.  
Fonte: OpenAI Whisper - [https://github.com/openai/whisper/blob/main/whisper/transcribe.py](https://github.com/openai/whisper/blob/main/whisper/transcribe.py)  

### Perché includerlo tra i 5 formati più adatti

Perché SRT, VTT, ASS e TTML sono formati di distribuzione o editing.
Un’applicazione didattica seria ha bisogno di un formato interno più ricco.

Un formato interno JSON può contenere:

* segmenti;
* parole;
* timestamp parola per parola;
* lingua originale;
* traduzioni multiple;
* note lessicali;
* note grammaticali;
* lemmi;
* livello CEFR;
* parlante;
* confidenza del modello ASR;
* fonte della traduzione;
* stato di revisione umana;
* riferimenti al video;
* relazioni tra parola originale e parola tradotta.

Esempio concettuale:

```
{
  "media_id": "lesson_001",
  "source_language": "en",
  "tracks": [
    {
      "language": "en",
      "kind": "transcription",
      "segments": [
        {
          "start": 1.0,
          "end": 4.0,
          "speaker": "John",
          "text": "I went home.",
          "words": [
            {"text": "I", "start": 1.0, "end": 1.1, "lemma": "I"},
            {"text": "went", "start": 1.2, "end": 1.6, "lemma": "go"},
            {"text": "home", "start": 1.7, "end": 2.1, "lemma": "home"}
          ]
        }
      ]
    },
    {
      "language": "it",
      "kind": "translation",
      "segments": [
        {
          "start": 1.0,
          "end": 4.0,
          "text": "Sono andato a casa."
        }
      ]
    }
  ]
}
```

### Uso da parte di tool e pipeline

Whisper può generare JSON e TSV.
faster-whisper, WhisperX e stable-ts possono produrre segmenti con timestamp, in alcuni casi anche a livello parola.
Fonti:

OpenAI Whisper
[https://github.com/openai/whisper](https://github.com/openai/whisper)

faster-whisper
[https://github.com/SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)

WhisperX
[https://github.com/m-bain/whisperx](https://github.com/m-bain/whisperx)

stable-ts
[https://github.com/jianfch/stable-ts](https://github.com/jianfch/stable-ts)

### Librerie Python

Per JSON/TSV non servono librerie specifiche per sottotitoli:

* json;
* csv;
* pandas;
* pydantic;
* sqlite3;
* SQLAlchemy;
* dataclasses;
* pathlib.

Per traduzione:

* Argos Translate, offline/open source;
* deep-translator, wrapper verso più motori;
* API DeepL/OpenAI/Gemini, se si accetta dipendenza esterna.

Fonti:

Argos Translate
[https://argos-translate.readthedocs.io/](https://argos-translate.readthedocs.io/)

deep-translator
[https://deep-translator.readthedocs.io/en/stable/README.html](https://deep-translator.readthedocs.io/en/stable/README.html)

### Vantaggi per programmatori

Un formato interno JSON/SQLite permette di esportare senza perdere il dato sorgente:

* SRT per compatibilità;
* WebVTT per web;
* ASS per doppia lingua visibile;
* TTML/IMSC per workflow professionale.

Questo approccio evita di usare SRT come “database povero”.

### Limiti

JSON/TSV non è direttamente caricabile come sottotitolo standard nella maggior parte dei player. Serve un exporter.

### Valutazione

JSON/TSV strutturato è il miglior formato interno per pipeline software, soprattutto se si lavora con ASR, NLP, traduzione e apprendimento linguistico.

---

## Confronto architetturale

| Formato   | Ruolo migliore                | Punti forti                                           | Punti deboli                  | Uso consigliato               |
| --------- | ----------------------------- | ----------------------------------------------------- | ----------------------------- | ----------------------------- |
| WebVTT    | Distribuzione web/interattiva | Track HTML, metadata, capitoli, più lingue via player | Supporto feature non uniforme | Player didattico web          |
| ASS/SSA   | Rendering ricco               | Doppia lingua, stili, layer, karaoke                  | Meno adatto al web standard   | Video con due lingue visibili |
| SRT       | Export universale             | Compatibilità massima, semplicità                     | Perdita di semantica e stile  | Output finale base            |
| TTML/IMSC | Workflow professionale        | XML, validazione, metadati, standard                  | Complessità alta              | Broadcast/OTT/archivi         |
| JSON/TSV  | Formato interno               | Conserva dati ricchi, timestamp parola, NLP           | Non è formato player          | Database/pipeline sorgente    |

---

## 9. Conversioni e perdita di informazione

Le conversioni non sono simmetriche.

Conversione quasi sicura:

```
JSON interno -> SRT
```

Ma con perdita di:

* speaker;
* lemmi;
* note;
* traduzioni multiple;
* confidence;
* allineamento parola;
* stili.

Conversione ricca:

```
JSON interno -> WebVTT
```

Permette di conservare almeno:

* cue;
* parlanti;
* metadati;
* tracce multiple;
* capitoli.

Conversione visiva:

```
JSON interno -> ASS
```

Permette di costruire:

* doppia lingua;
* layout controllato;
* evidenziazione;
* livelli paralleli.

Conversione professionale:

```
JSON interno -> TTML/IMSC
```

Permette di produrre:

* XML validabile;
* regioni;
* stili;
* metadati;
* output per workflow broadcast/OTT.

Conversione rischiosa:

```
ASS -> SRT
```

Perde quasi tutto ciò che rende ASS utile.

Conversione rischiosa:

```
WebVTT ricco -> SRT
```

Perde:

* classi;
* voice tags;
* metadati;
* regioni;
* cue settings.

---

## 10. Pipeline consigliata

Per un sistema di apprendimento linguistico si può usare questa architettura:

```
Video/audio sorgente
    |
    v
ASR: Whisper / faster-whisper / WhisperX / stable-ts
    |
    v
JSON interno con segmenti, parole, lingue, traduzioni, lemmi, note
    |
    +--> SRT per compatibilità
    |
    +--> WebVTT per player web
    |
    +--> ASS per doppia lingua visibile
    |
    +--> TTML/IMSC per consegna professionale
```

Il formato interno deve essere più ricco di qualunque formato di esportazione.

---

## 11. Scelta finale per apprendimento linguistico multilingua

Classifica pratica:

1. JSON/SQLite interno
   Migliore come sorgente dati e pipeline NLP.

2. WebVTT
   Migliore per player web interattivo con più tracce.

3. ASS/SSA
   Migliore per mostrare due lingue contemporaneamente nello stesso video.

4. SRT
   Migliore per compatibilità esterna.

5. TTML/IMSC
   Migliore per workflow professionali e archivi strutturati.

Scelta consigliata:

* usare **JSON/SQLite come formato interno**;
* esportare WebVTT per applicazione web;
* esportare **ASS quando serve doppia lingua visuale**;
* esportare SRT per compatibilità;
* esportare TTML/IMSC solo se richiesto da workflow professionali.

## Alcuni riferimenti

MDN - WebVTT
[https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API/Web_Video_Text_Tracks_Format](https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API/Web_Video_Text_Tracks_Format)

W3C - WebVTT specification
[https://www.w3.org/TR/webvtt1/](https://www.w3.org/TR/webvtt1/)

YouTube Help - Supported subtitle and closed caption files
[https://support.google.com/youtube/answer/2734698?hl=en](https://support.google.com/youtube/answer/2734698?hl=en)

Vimeo Help - Add captions or subtitles
[https://help.vimeo.com/hc/en-us/articles/21956884955537-How-to-add-captions-or-subtitles-to-my-video](https://help.vimeo.com/hc/en-us/articles/21956884955537-How-to-add-captions-or-subtitles-to-my-video)

Aegisub
[https://aegisub.org/](https://aegisub.org/)

pysubs2 supported formats
[https://pysubs2.readthedocs.io/en/latest/supported-formats.html](https://pysubs2.readthedocs.io/en/latest/supported-formats.html)

pycaption supported formats
[https://pycaption.readthedocs.io/en/stable/supported_formats.html](https://pycaption.readthedocs.io/en/stable/supported_formats.html)

srt Python library
[https://srt.readthedocs.io/en/latest/api.html](https://srt.readthedocs.io/en/latest/api.html)

OpenAI Whisper
[https://github.com/openai/whisper](https://github.com/openai/whisper)

faster-whisper
[https://github.com/SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)

WhisperX
[https://github.com/m-bain/whisperx](https://github.com/m-bain/whisperx)

stable-ts
[https://github.com/jianfch/stable-ts](https://github.com/jianfch/stable-ts)

W3C IMSC
[https://www.w3.org/TR/ttml-imsc1.1/](https://www.w3.org/TR/ttml-imsc1.1/)

Argos Translate
[https://argos-translate.readthedocs.io/](https://argos-translate.readthedocs.io/)

deep-translator
[https://deep-translator.readthedocs.io/en/stable/README.html](https://deep-translator.readthedocs.io/en/stable/README.html)


read 4