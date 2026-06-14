# Gestore della pipeline Anki

## Scopo del documento

Questo documento descrive il funzionamento del gestore generale della pipeline implementato nel file:

    pipeline_master.py

Il gestore della pipeline ha il compito di coordinare l'esecuzione ordinata delle varie tratte elaborative necessarie per trasformare materiali sorgente, come video, audio, sottotitoli o testi, in materiali intermedi utilizzabili per la successiva generazione di deck Anki.

Il gestore non contiene la logica tecnica dettagliata dei singoli step. Ogni step deve essere implementato in un modulo dedicato o in una funzione dedicata. Il gestore si occupa invece di:

- definire la configurazione generale della pipeline;
- individuare quali step devono essere eseguiti;
- passare a ogni step le directory di input e output corrette;
- gestire logging su console e su file;
- intercettare errori;
- produrre un riepilogo finale;
- rendere semplice l'aggiunta futura di nuovi step.

## Struttura generale della pipeline

La pipeline è organizzata in directory numerate. Ogni directory rappresenta una fase o uno stato dei dati.

Nella versione attuale è configurato il seguente step:

    010_video_in      input video iniziale
    015_video_out     output dello step di estrazione da video

La directory base predefinita è:

    ./pipe_data

Quindi, per impostazione predefinita, lo step video legge da:

    ./pipe_data/010_video_in

E scrive in:

    ./pipe_data/015_video_out

I log vengono scritti in:

    ./pipe_data/_logs

## File principali

Il sistema attuale usa almeno due file Python.

    pipeline_master.py

È il gestore generale della pipeline. Coordina gli step, prepara la configurazione, imposta il logging, esegue gli step selezionati e produce il riepilogo finale.

    pipeline_video_audio_subtitles_extract_v2.py

Contiene la logica dello step video/audio/sottotitoli. Questo modulo espone la funzione flessibile:

    process_video_audio_subtitles(...)

Questa funzione viene invocata dal master nello step `015_video_out`.

## Uso base

Per eseguire la pipeline con le impostazioni predefinite:

    python pipeline_master.py

Questa esecuzione usa:

    base directory: ./pipe_data
    input video:     ./pipe_data/010_video_in
    output video:    ./pipe_data/015_video_out
    log:             ./pipe_data/_logs

## Uso con directory base diversa

La directory base può essere modificata con:

    python pipeline_master.py --base-dir ./pipe_data

Oppure, per esempio:

    python pipeline_master.py --base-dir D:\\anki_pipeline\\pipe_data

Tutte le directory interne vengono calcolate a partire dalla directory base.

## Esecuzione di un solo step

Il gestore è già predisposto per una pipeline con più step. Anche se attualmente è registrato solo lo step `015_video_out`, è possibile eseguire uno step specifico con:

    python pipeline_master.py --only-step 015_video_out

Questa opzione sarà utile quando la pipeline crescerà e conterrà più passaggi.

## Saltare uno step

Uno step può essere saltato con:

    python pipeline_master.py --skip-step 015_video_out

L'opzione può essere usata più volte quando saranno presenti più step.

Esempio futuro:

    python pipeline_master.py --skip-step 015_video_out --skip-step 020_text_extract

## Dry-run

La modalità dry-run mostra cosa verrebbe eseguito, ma non elabora realmente i file.

    python pipeline_master.py --dry-run

Questa modalità è utile per verificare configurazione, directory e selezione degli step senza produrre output.

## Sovrascrittura degli output

Per consentire la sovrascrittura di file già esistenti:

    python pipeline_master.py --overwrite

Questa opzione viene passata agli step che la supportano. Nel caso dello step video, viene passata a `ffmpeg` tramite opzione di sovrascrittura.

## Logging

Il gestore usa due livelli di logging.

### Logging su console

La console mostra informazioni importanti ma non eccessivamente dettagliate:

- avvio della pipeline;
- avvio dello step;
- directory di input e output;
- file video elaborati;
- errori principali;
- riepilogo finale.

### Logging su file

Il file di log contiene informazioni più dettagliate.

Il log generale della pipeline viene scritto in:

    ./pipe_data/_logs/pipeline_master.log

Ogni step può avere un log dedicato. Per lo step video il log viene scritto in:

    ./pipe_data/_logs/015_video_out.log

I log di step sono utili per isolare gli errori di una specifica fase della pipeline.

## Opzioni principali da riga di comando

| Opzione | Effetto |
|---|---|
| `--base-dir` | imposta la directory base della pipeline |
| `--only-step` | esegue solo lo step indicato |
| `--skip-step` | salta uno step |
| `--dry-run` | simula l'esecuzione senza elaborare file |
| `--overwrite` | consente la sovrascrittura degli output |
| `--no-recursive-video-search` | disabilita la ricerca ricorsiva dei video |
| `--no-auto-find-subtitles` | disabilita la ricerca automatica dei sottotitoli |
| `--no-mp3` | disabilita l'estrazione MP3 |
| `--no-ogg` | disabilita l'estrazione OGG Vorbis |
| `--no-frames` | disabilita l'estrazione dei fotogrammi |
| `--no-phrase-files` | disabilita la scrittura dei file frase |
| `--no-step-log-files` | disabilita i file di log separati per step |

## Configurazione tecnica

La configurazione generale è rappresentata dalla classe:

    PipelineConfig

Questa classe contiene i parametri principali della pipeline, tra cui:

    base_dir
    logs_dir_name
    only_step
    skip_steps
    dry_run
    overwrite
    recursive_video_search
    auto_find_subtitles
    write_mp3
    write_ogg
    write_frames
    write_phrase_files
    create_step_log_files

La configurazione viene costruita a partire dagli argomenti della riga di comando tramite la funzione:

    build_config(args)

## Rappresentazione degli step

Ogni step della pipeline viene rappresentato dalla classe:

    PipelineStep

Questa classe contiene:

    step_id
    description
    input_dir_name
    output_dir_name
    runner

Il campo più importante è `runner`, cioè la funzione Python che esegue realmente lo step.

Per esempio, lo step video è registrato così:

    PipelineStep(
        step_id="015_video_out",
        description="Estrazione audio, fotogrammi e frasi da video/sottotitoli.",
        input_dir_name="010_video_in",
        output_dir_name="015_video_out",
        runner=run_015_video_out,
    )

## Risultato di uno step

Ogni step restituisce un oggetto:

    StepRunResult

Questo oggetto contiene:

    step_id
    ok
    started_at
    ended_at
    processed_items
    errors
    details

Il campo `ok` indica se lo step è terminato senza errori.

Il campo `processed_items` indica quanti elementi sono stati elaborati. Nel caso dello step video, indica il numero di video elaborati.

Il campo `errors` contiene l'elenco degli errori rilevati.

Il campo `details` può contenere informazioni aggiuntive specifiche dello step.

## Funzionamento generale del master

Il punto di ingresso è:

    main()

La sequenza logica è:

1. leggere gli argomenti da riga di comando;
2. costruire la configurazione `PipelineConfig`;
3. chiamare `run_pipeline(config)`;
4. eseguire gli step selezionati;
5. produrre il riepilogo;
6. restituire codice di uscita `0` se tutto è andato bene, `1` se ci sono errori.

La funzione principale della pipeline è:

    run_pipeline(config)

Questa funzione:

1. crea il logger generale;
2. legge la lista degli step da `build_steps()`;
3. filtra gli step in base a `--only-step` e `--skip-step`;
4. crea un logger dedicato per ogni step;
5. esegue il runner di ogni step;
6. registra errori e riepilogo finale.

## Step attuale: 015_video_out

Lo step attuale è implementato dalla funzione:

    run_015_video_out(config, logger)

Questa funzione usa come input:

    ./pipe_data/010_video_in

E come output:

    ./pipe_data/015_video_out

Il percorso viene calcolato tramite:

    input_dir = config.step_input_dir("010_video_in")
    output_dir = config.step_output_dir("015_video_out")

Lo step invoca:

    process_video_audio_subtitles(...)

passando i principali parametri di configurazione:

    target=input_dir
    output_dir=output_dir
    subtitles=None
    recursive=config.recursive_video_search
    overwrite=config.overwrite
    auto_find_subtitles=config.auto_find_subtitles
    write_mp3=config.write_mp3
    write_ogg=config.write_ogg
    write_frames=config.write_frames
    write_phrase_files=config.write_phrase_files
    per_video_subdir=True
    create_log_file=False
    logger=logger

Il parametro `create_log_file=False` viene usato perché il file di log dello step viene già gestito dal master. In questo modo si evita di generare log duplicati nello step specifico.

## Output dello step video

Per ogni video elaborato, lo step video produce una sottodirectory dentro:

    ./pipe_data/015_video_out

Per esempio:

    ./pipe_data/015_video_out/out_nomevideo

Dentro questa directory possono essere presenti:

    audio/
        nomevideo.mp3
        nomevideo.ogg

    frames/
        fotogr_<timestamp>_<prime_parole>.jpg

    phrases/
        phrase_<timestamp>.txt

La produzione dei singoli output può essere disabilitata dal master con le opzioni:

    --no-mp3
    --no-ogg
    --no-frames
    --no-phrase-files

## Gestione dei sottotitoli

Nel master, il parametro:

    subtitles=None

indica che non viene passato un file sottotitoli specifico allo step video.

Se `auto_find_subtitles` è attivo, lo step video cerca automaticamente un file `.srt` o `.vtt` accanto al video, con lo stesso nome base.

Esempio:

    lezione01.mp4
    lezione01.srt

Se il file sottotitoli viene trovato, vengono generati fotogrammi e file frase, salvo disattivazione esplicita.

## Gestione degli errori

Il master gestisce errori a più livelli.

### Errori nello step

Se uno step genera errori recuperabili, questi vengono salvati nel campo:

    StepRunResult.errors

Lo step può quindi terminare con:

    ok=False

ma il master può comunque produrre un riepilogo finale.

### Eccezioni non previste

Se si verifica un'eccezione imprevista dentro uno step, il master la intercetta, la registra nel log e salva il traceback nel log dettagliato.

La parte interessata è:

    except Exception as exc:
        result.errors.append(str(exc))
        logger.error("Errore nello step %s: %s", step_id, exc)
        logger.debug("Traceback:\\n%s", traceback.format_exc())

## Codici di uscita

Il programma restituisce:

    0

se tutti gli step eseguiti sono terminati correttamente.

Restituisce:

    1

se almeno uno step ha prodotto errori o se nessuno step è stato eseguito.

Questo comportamento permette di usare il master anche in script batch o in automazioni.

## Come aggiungere un nuovo step

Per aggiungere uno step futuro, occorre seguire questi passaggi.

### 1. Creare la funzione runner dello step

Esempio:

    def run_020_text_extract(
        config: PipelineConfig,
        logger: logging.Logger
    ) -> StepRunResult:
        step_id = "020_text_extract"
        started_at = datetime.now()

        result = StepRunResult(
            step_id=step_id,
            ok=False,
            started_at=started_at,
        )

        input_dir = config.step_input_dir("015_video_out")
        output_dir = config.step_output_dir("020_text_extract")

        try:
            # qui inserire la logica dello step
            result.processed_items = 0
            result.ok = True
        except Exception as exc:
            result.errors.append(str(exc))
            logger.exception("Errore nello step %s", step_id)

        result.ended_at = datetime.now()
        return result

### 2. Registrare lo step in build_steps()

Aggiungere lo step nella lista restituita da:

    build_steps()

Esempio:

    PipelineStep(
        step_id="020_text_extract",
        description="Estrazione testo normalizzato dai materiali intermedi.",
        input_dir_name="015_video_out",
        output_dir_name="020_text_extract",
        runner=run_020_text_extract,
    )

### 3. Verificare l'ordine degli step

Gli step vengono eseguiti nell'ordine in cui sono presenti nella lista restituita da `build_steps()`.

Quindi, per una pipeline ordinata, la lista dovrà seguire la numerazione delle directory.

Esempio futuro:

    010_video_in
    015_video_out
    020_text_extract
    030_text_normalized
    040_targets_lemma_sentence
    050_cards_ready

## Vantaggi della struttura attuale

La struttura attuale ha diversi vantaggi.

Primo: separa il coordinamento generale dalla logica tecnica dei singoli step.

Secondo: rende ogni step sostituibile, testabile e migliorabile in modo indipendente.

Terzo: centralizza logging, configurazione e gestione errori.

Quarto: consente di eseguire uno step alla volta, cosa utile durante sviluppo e debug.

Quinto: permette di aggiungere nuove tratte senza riscrivere il master.

## Limiti attuali

La versione attuale del master è già estendibile, ma è ancora semplice.

I principali limiti sono:

- non usa ancora un file di configurazione esterno;
- non gestisce ancora dipendenze formali tra step;
- non verifica ancora automaticamente che l'output di uno step sia compatibile con l'input dello step successivo;
- non produce ancora un report finale strutturato in JSON o CSV;
- non ha ancora un sistema di resume avanzato;
- non distingue ancora tra errori bloccanti e avvisi non bloccanti in modo configurabile.

Questi limiti non impediscono l'uso attuale, ma indicano possibili evoluzioni future.

## Evoluzioni consigliate

In una fase successiva si potranno aggiungere:

- file di configurazione YAML, TOML o JSON;
- report finale in JSON;
- report finale in CSV;
- validazione delle directory di input e output;
- modalità resume;
- modalità force-clean per cancellare output precedenti;
- gestione esplicita delle dipendenze tra step;
- configurazione separata per ogni step;
- test automatici per ciascuna tratta;
- log strutturati in formato machine-readable.

## Sintesi

Il file `pipeline_master.py` è il punto centrale di coordinamento della pipeline.

Attualmente esegue lo step `015_video_out`, che legge video da:

    ./pipe_data/010_video_in

E scrive i risultati in:

    ./pipe_data/015_video_out

Il master è però già progettato per essere esteso con nuovi step. La logica principale è basata su configurazione, registrazione degli step, runner dedicati, logging centralizzato e risultati standardizzati.

Questa impostazione permette di far crescere progressivamente la pipeline mantenendo separati i compiti: il master coordina, gli step elaborano.
