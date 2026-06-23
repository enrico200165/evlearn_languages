# Lezione 0 - Progettazione del Lessico Core

## Conteggio parole 

Spesso si parla di:

```
1000 parole core
2000 parole
3000 parole
```

Se non si definisce con precisione cosa significa "parola", diventa impossibile contare le parole e:

* costruire correttamente liste di frequenza;
* confrontare lingue diverse;
* stimare la copertura lessicale;
* valutare il progresso dello studente;
* decidere se una parola deve entrare nel vocabolario core;
* progettare filtri di frequenza;
* costruire deck Anki coerenti.

---

## Selezione parole e Ritorno sull'investimento (ROI)

```
Quali parole producono il maggior beneficio?
```

Questa domanda è alla base della moderna linguistica applicata e della progettazione di sistemi di apprendimento.


### Frequenza e utilità

In generale esiste una forte correlazione tra: frequenza d'uso e utilità pratica


Le parole che compaiono più spesso:

* vengono incontrate più frequentemente;
* vengono riutilizzate più spesso;
* compaiono in molti contesti diversi;
* producono un miglior ritorno sull'investimento.

Questo principio è sorprendentemente stabile tra lingue molto diverse.

---

## Cosa significa realmente "parola"

Esistono diversi modi di contare il vocabolario.

### Primo livello: token

Un token è una singola occorrenza di una parola in un testo.

Esempio:

```
Ich gehe  nach Hause.
Du  gehst nach Hause.
Wir gehen nach Hause.
```

Ogni occorrenza di nach e Hause è conteggiata

Ci sono 12 token


I token sono utili per:

* statistica linguistica;
* analisi dei corpora;
* linguistica computazionale;
* NLP;
* modelli linguistici.

Non sono però la misura normalmente utilizzata quando si parla del vocabolario di una persona.

---

### Secondo livello: forma lessicale

Consideriamo il verbo tedesco: `gehen`. 
Forme possibili: `gehen gehe gehst geht ging gegangen gehend`  

7 forme lessicali

In questo approccio ogni forma viene contata separatamente.


Consideriamo il verbo Giappinese: `食べる`.  
Forme: `食べる 食べます 食べた 食べない 食べて 食べよう 食べられる`  

Anche qui ogni forma viene contata come elemento distinto.

Se si usa questo criterio, il numero di "parole" esplode rapidamente.

Un singolo verbo può generare:

* decine di forme;
* centinaia di forme nelle lingue più ricche morfologicamente.

Questo rende difficile confrontare lingue diverse.

---

### Terzo livello: lemma

Il lemma è la forma di dizionario.

Tutte le forme grammaticali vengono ricondotte a una singola voce.


Esempi: 
Tedesco: le forme: `gehen gehe gehst geht ging gegangen` vengono ricondotte a: `gehen` 
Conteggio: 1 lemma  

Giapponese: le forme: `食べる 食べます 食べた 食べない 食べて 食べよう 食べられる` diventano: `食べる`  
Conteggio: 1 lemma

Quando la ricerca scientifica afferma:
*conoscere N parole* quasi sempre si riferisce a *N lemmi*

---

### Quarto livello: famiglia lessicale

Si raggruppano parole che condividono una stessa radice.

Esempio:  
inglese `teach teacher teaching taught` possono essere considerate parte della stessa famiglia.
tedesco `lernen Lerner Lernende Lernprozess` possono essere considerate una famiglia lessicale.

La famiglia lessicale è utilizzata soprattutto negli studi sulla `copertura lessicale` ovvero sulla percentuale di testo **comprensibile** da un lettore.

---

### Cosa significa conoscere una parola

Questa espressione è più complessa di quanto sembri.

#### Livello 1 - Riconoscimento  

Sapere che: gehen significa andare  


#### Livello 2 - Riconoscimento delle forme  

Capire automaticamente: ging gegangen senza dover consultare un dizionario.


#### Livello 3 - Produzione

Saper utilizzare la parola correttamente in una frase.

Esempio: Ich gehe nach Hause.

#### Livello 4 - Padronanza

Saper usare correttamente:

* tempi verbali;
* sfumature;
* collocazioni;
* registri;
* espressioni idiomatiche.

---

# Tipi di parole vengono contati?

Tutti. Quando si parla di: 2000 lemmi si intendono normalmente tutte le categorie grammaticali.
Sostantivi, Verbi, Aggettivi, Avverbi, Pronomi, Preposizioni, Congiunzioni

le parole più frequenti di una lingua sono spesso:
articoli; pronomi; preposizioni; verbi molto comuni; connettivi.

Esempio: in tedesco:
`der, die, das, und, oder, aber, weil, dass, mit, für`  
sono tra gli elementi più importanti dell'intera lingua.

---

# Implicazioni per il progetto software

Per il software che verrà sviluppato nelle lezioni successive:
```
unità didattica fondamentale = lemma
```

Questo significa che: `gehen` è una voce.  
Non sono voci separate:
`gehe gehst geht ging gegangen ... `  

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


read: 3