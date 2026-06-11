# Lezione 0 - Progettazione del Lessico Core

## Parte 1 - Cosa significa realmente "N parole" e perché conta

## Obiettivo della lezione

Prima di costruire software per l'apprendimento delle lingue è necessario chiarire un punto fondamentale:

Quando si parla di:

```
1000 parole
2000 parole
3000 parole
```

che cosa si sta contando esattamente?

La domanda può sembrare banale, ma in realtà è uno dei problemi più importanti dell'intera progettazione.

Se non si definisce con precisione cosa significa "parola", diventa impossibile:

* costruire correttamente liste di frequenza;
* confrontare lingue diverse;
* stimare la copertura lessicale;
* valutare il progresso dello studente;
* decidere se una parola deve entrare nel vocabolario core;
* progettare filtri di frequenza;
* costruire deck Anki coerenti.

Questa lezione introduce quindi i concetti teorici necessari per comprendere:

* come viene misurato il vocabolario;
* cosa significa conoscere una parola;
* perché le prime migliaia di parole producono il massimo ritorno sull'investimento;
* quali sono le implicazioni pratiche per il software che verrà sviluppato nelle lezioni successive.

---

# Il problema del ritorno sull'investimento (ROI)

Supporre di avere 10 anni per imparare una lingua.

In teoria sarebbe possibile studiare:

```
10000 parole
20000 parole
30000 parole
```

o più.

Tuttavia il tempo disponibile è limitato.

Ogni ora dedicata allo studio di una parola è un'ora che non può essere dedicata ad altro.

Occorre quindi chiedersi:

```
Quali parole producono il maggior beneficio?
```

Questa domanda è alla base della moderna linguistica applicata e della progettazione di sistemi di apprendimento.

---

## Un esempio intuitivo

Supporre di leggere un giornale tedesco.

Le parole:

```
und
der
die
das
sein
haben
können
gehen
```

compaiono continuamente.

Le parole:

```
Schifffahrtsgesellschaft
Haftpflichtversicherung
Wiederaufbereitungsanlage
```

compaiono molto più raramente.

Imparare una parola rara può richiedere lo stesso sforzo necessario per imparare una parola frequente.

Tuttavia il beneficio ottenuto è molto diverso.

Per questo motivo il lessico non deve essere scelto casualmente.

---

## Frequenza e utilità

In generale esiste una forte correlazione tra:

```
frequenza d'uso
```

e

```
utilità pratica
```

Le parole che compaiono più spesso:

* vengono incontrate più frequentemente;
* vengono riutilizzate più spesso;
* compaiono in molti contesti diversi;
* producono un miglior ritorno sull'investimento.

Questo principio è sorprendentemente stabile tra lingue molto diverse.

---

# Cosa significa realmente "parola"

La maggior parte delle persone usa il termine:

```
parola
```

come se avesse un significato unico.

In realtà esistono diversi modi di contare il vocabolario.

Questa distinzione è fondamentale.

---

## Primo livello: token

Il concetto più semplice è il token.

Un token è una singola occorrenza di una parola in un testo.

Esempio:

```
Ich gehe nach Hause.
Du gehst nach Hause.
Wir gehen nach Hause.
```

Se si contano tutte le parole presenti si ottiene:

```
Ich
gehe
nach
Hause

Du
gehst
nach
Hause

Wir
gehen
nach
Hause
```

Numero totale:

```
12 token
```

In questo conteggio:

```
gehe
```

e

```
gehst
```

sono considerati elementi diversi.

---

## A cosa servono i token

I token sono molto utili per:

* statistica linguistica;
* analisi dei corpora;
* linguistica computazionale;
* NLP;
* modelli linguistici.

Non sono però la misura normalmente utilizzata quando si parla del vocabolario di una persona.

---

# Secondo livello: forma lessicale

Un altro modo di contare consiste nel considerare ogni forma grammaticale come distinta.

Prendere il verbo tedesco:

```
gehen
```

Forme possibili:

```
gehen
gehe
gehst
geht
ging
gegangen
gehend
```

In questo approccio ogni forma viene contata separatamente.

Numero:

```
7 forme
```

---

## Esempio italiano

Verbo:

```
andare
```

Forme:

```
andare
vado
vai
va
andiamo
andate
vanno
andavo
andai
andrò
```

e molte altre.

In questo approccio ogni forma viene contata separatamente.

---

## Esempio giapponese

Verbo:

```
食べる
```

Forme:

```
食べる
食べます
食べた
食べない
食べて
食べよう
食べられる
```

Anche qui ogni forma viene contata come elemento distinto.

---

## Problema delle forme

Se si usa questo criterio, il numero di "parole" esplode rapidamente.

Un singolo verbo può generare:

* decine di forme;
* centinaia di forme nelle lingue più ricche morfologicamente.

Questo rende difficile confrontare lingue diverse.

---

# Terzo livello: lemma

Il lemma è la forma di dizionario.

Tutte le forme grammaticali vengono ricondotte a una singola voce.

---

## Esempio tedesco

Le forme:

```
gehen
gehe
gehst
geht
ging
gegangen
```

vengono ricondotte a:

```
gehen
```

Conteggio:

```
1 lemma
```

---

## Esempio italiano

Le forme:

```
andare
vado
vai
va
andiamo
andate
vanno
andrò
```

diventano:

```
andare
```

Conteggio:

```
1 lemma
```

---

## Esempio giapponese

Le forme:

```
食べる
食べます
食べた
食べない
食べて
食べよう
食べられる
```

diventano:

```
食べる
```

Conteggio:

```
1 lemma
```

---

# Perché il lemma è importante

Quando la ricerca scientifica afferma:

```
conoscere 2000 parole
```

oppure:

```
conoscere 3000 parole
```

quasi sempre si riferisce a:

```
2000 lemmi
3000 lemmi
```

e non a:

```
2000 token
```

oppure:

```
2000 forme flesse
```

Questa distinzione è fondamentale.

---

# Quarto livello: famiglia lessicale

Esiste un livello ancora più aggregato.

Si raggruppano parole che condividono una stessa radice.

---

## Esempio inglese

```
teach
teacher
teaching
taught
```

possono essere considerate parte della stessa famiglia.

---

## Esempio tedesco

```
lernen
Lerner
Lernende
Lernprozess
```

possono essere considerate una famiglia lessicale.

---

## Quando viene usata

La famiglia lessicale è utilizzata soprattutto negli studi sulla:

```
copertura lessicale
```

ovvero sulla percentuale di testo comprensibile da un lettore.

---

# Cosa significa conoscere una parola

Anche questa espressione è più complessa di quanto sembri.

---

## Livello 1 - Riconoscimento

Sapere che:

```
gehen
```

significa:

```
andare
```

---

## Livello 2 - Riconoscimento delle forme

Capire automaticamente:

```
ging

gegangen
```

senza dover consultare un dizionario.

---

## Livello 3 - Produzione

Saper utilizzare la parola correttamente in una frase.

Esempio:

```
Ich gehe nach Hause.
```

---

## Livello 4 - Padronanza

Saper usare correttamente:

* tempi verbali;
* sfumature;
* collocazioni;
* registri;
* espressioni idiomatiche.

---

# Tutti i tipi di parole vengono contati?

Sì.

Quando si parla di:

```
2000 lemmi
```

si intendono normalmente tutte le categorie grammaticali.

---

## Sostantivi

Esempi:

```
Haus
Hund
Schule
```

---

## Verbi

Esempi:

```
gehen
essen
schlafen
```

---

## Aggettivi

Esempi:

```
groß
klein
schön
```

---

## Avverbi

Esempi:

```
heute
morgen
immer
```

---

## Pronomi

Esempi:

```
ich
du
wir
```

---

## Preposizioni

Esempi:

```
mit
für
von
```

---

## Congiunzioni

Esempi:

```
und
oder
weil
```

---

# Un errore molto comune

Molte persone immaginano che il vocabolario sia composto soprattutto da sostantivi.

In realtà le parole più frequenti di una lingua sono spesso:

* articoli;
* pronomi;
* preposizioni;
* verbi molto comuni;
* connettivi.

Esempio tedesco:

```
der
die
das
und
oder
aber
weil
dass
mit
für
```

Sono tra gli elementi più importanti dell'intera lingua.

---

# Implicazioni per il progetto software

Per il software che verrà sviluppato nelle lezioni successive è opportuno adottare una convenzione chiara.

Definizione:

```
unità didattica fondamentale = lemma
```

Questo significa che:

```
gehen
```

è una voce.

Non sono voci separate:

```
gehe
gehst
geht
ging
gegangen
```

Queste forme saranno memorizzate come proprietà del lemma.

---

## Modello dati consigliato

Esempio:

```
{
    "lemma": "gehen",
    "language": "de",
    "part_of_speech": "verb",
    "frequency_rank": 523,
    "forms": [
        "gehe",
        "gehst",
        "geht",
        "ging",
        "gegangen"
    ]
}
```

Lo stesso approccio sarà valido per:

* tedesco;
* giapponese;
* inglese;
* francese;
* spagnolo;

e per la maggior parte delle lingue supportate dal sistema.

---

# Preparazione alla parte 2

Ora che è chiaro cosa significhi realmente:

```
1000 parole
2000 parole
3000 parole
```

si può affrontare la domanda successiva:

```
Quanti lemmi conviene imparare?
```

Nella seconda parte verranno analizzati:

* copertura lessicale;
* Core-1000;
* Core-2000;
* Core-3000;
* Core-5000;
* contesti comunicativi;
* categorie lessicali;
* pesi;
* priorità;
* modello quantitativo per il filtro di frequenza;
* implicazioni specifiche per tedesco e giapponese;
* progettazione delle liste core per il software.
