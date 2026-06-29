## Categorie POS e UPOS

Le `categorie POS`, dall’inglese Part of Speech, sono classi usate per indicare a quale tipo appartiene una parola o un token: nome, verbo, aggettivo, pronome, articolo, avverbio, preposizione, congiunzione e così via.

Un `token` è un’unità ottenuta dividendo un testo in elementi analizzabili.  
Di solito corrisponde a una parola o a un segno di punteggiatura, ma non sempre coincide perfettamente con una parola grafica.  
In UD, per esempio, alcune forme possono essere rappresentate come token superficiali e poi scomposte in più parole sintattiche.

In un sistema NLP, il POS tagging consiste nell’assegnare a ogni token di una frase un’etichetta che ne descrive la categoria grammaticale generale.  
Per esempio, nella frase `Il ragazzo legge un libro`, `ragazzo` è un nome, `legge` è un verbo, `un` è un determinante/articolo e `libro` è un nome.

UPOS, cioè Universal Part-of-Speech tags,  
è l’insieme delle **17 categorie POS universali** definite da `Universal Dependencies`.  
Serve a rappresentare in modo uniforme le principali categorie grammaticali in lingue diverse.  
Le categorie UPOS sono: `ADJ`, `ADP`, `ADV`, `AUX`, `CCONJ`, `DET`, `INTJ`, `NOUN`, `NUM`, `PART`, `PRON`, `PROPN`, `PUNCT`, `SCONJ`, `SYM`, `VERB`, `X`.



La corrispondenza tra categorie grammaticali italiane tradizionali e tag UPOS non è perfettamente 1:1, perché  

* la grammatica italiana classifica spesso la parola secondo categorie tradizionali, per esempio nome, articolo, aggettivo, pronome, verbo;  
* UPOS assegna a ogni parola sintattica un tag scelto da un inventario universale di 17 categorie.  
  * Nei casi ordinari il tag rappresenta il comportamento grammaticale tipico della parola;  
  * nei casi realmente ambigui, invece, la scelta dipende dall’uso nella frase.  

Un treebank UD è un corpus di frasi annotate secondo le regole di Universal Dependencies:  
per ogni token vengono indicati, tra le altre cose, il tag POS universale, eventuali features morfologiche e le relazioni sintattiche con gli altri token della frase.

La stessa forma grafica può quindi avere tag diversi quando corrisponde a usi grammaticali realmente diversi.  
Per esempio,  
`che` può essere `PRON` quando funziona da pronome relativo o interrogativo, ma può essere `SCONJ` quando introduce una subordinata completiva;  
`questo` può essere `DET` in `questo libro` e `PRON` in `questo è interessante`.  


Universal Dependencies definisce UPOS come insieme di categorie POS universali; per dettagli morfologici aggiuntivi si usano poi le features.

## Features

Le features sono informazioni grammaticali più **dettagliate** associate a un token.  

Mentre il tag UPOS indica la categoria generale della parola, per esempio `NOUN`, `VERB`, `ADJ` o `PRON`, le features descrivono proprietà più specifiche della forma usata nella frase:  
*genere, numero, persona, tempo, modo, grado, caso, tipo di pronome, forma verbale e così via*.

In Universal Dependencies una feature ha normalmente la forma `Nome=Valore`;  
più features possono essere combinate con il carattere `|`.  
Per esempio, in una frase italiana,  
`ragazzi` può essere annotato come `NOUN` con features `Gender=Masc|Number=Plur`;  
`mangiavamo` può essere annotato come `VERB` con informazioni come `Mood=Ind|Tense=Imp|Person=1|Number=Plur`;  
`questa` può essere `DET` con features come `Gender=Fem|Number=Sing|PronType=Dem`.  


Le features servono quindi a non moltiplicare inutilmente le categorie POS: invece di creare un tag diverso per “nome maschile singolare”, “nome femminile plurale”, “verbo indicativo presente” ecc., si mantiene una categoria UPOS generale e si aggiungono proprietà morfologiche separate. In questo modo l’annotazione resta più regolare, confrontabile tra lingue diverse e utilizzabile dai sistemi NLP.

## Mapping operativo grammatica italiana → UPOS

Nome comune → NOUN  
Esempi: casa, libro, lavoro, problema, decisione.

Nome proprio → PROPN  
Esempi: Marco, Roma, Italia, Google.  
Nella grammatica scolastica italiana il nome proprio è un sottotipo del nome; in UPOS ha un tag autonomo.

Articolo → DET  
Esempi: il, lo, la, i, gli, le, un, uno, una.  
In UPOS l’articolo non ha un tag autonomo: rientra nei determinanti.  
La documentazione UD per l’italiano include infatti articoli definiti e indefiniti tra i DET.


Articolo partitivo / forma articolata → verificare la tokenizzazione del treebank  
Esempi: dei libri, delle persone.  
In italiano forme come `del`, `dello`, `della`, `dei`, `degli`, `delle` possono essere rilevanti sia come forme articolate sia, in alcuni usi, come partitivi. Nelle linee guida UD italiane le preposizioni articolate sono scomposte in `ADP + DET`.  
In altri strumenti NLP o treebank può però comparire una rappresentazione diversa: per questo, operativamente, conviene controllare il treebank o il modello usato.



Aggettivo qualificativo → ADJ  
Esempi: bello, grande, difficile, interessante, rosso.  
UD italiano definisce ADJ come categoria delle parole che modificano nomi e ne specificano proprietà o attributi.

Aggettivo participiale  
* → ADJ se ha funzione e comportamento aggettivale  
Esempi: porta chiusa, lavoro completato, persona interessata.
* → VERB se conserva funzione verbale all’interno di un predicato verbale.  
UD segnala esplicitamente che i participi possono essere classificati come `VERB` o `ADJ` a seconda della lingua e del contesto.

Aggettivo possessivo → DET quando determina un nome  
Esempi: mio padre, la mia macchina.  
UD italiano indica esplicitamente che gli aggettivi possessivi sono trattati come DET.

Aggettivo dimostrativo  
* → DET quando determina un nome  
Esempi: questo libro, quella casa.  
* → PRON quando sostituisce un nome  
Esempio: questo è interessante.

Aggettivo indefinito  
* → DET quando determina un nome  
Esempi: alcuni studenti, ogni giorno, nessuna risposta.
* → PRON quando sostituisce un nome  
Esempi: alcuni sono arrivati, nessuno risponde.

Aggettivo interrogativo o esclamativo  
* → DET quando determina un nome  
Esempi: quale libro?, che problema!, quanta gente!
* → PRON quando sostituisce un nome  
Esempi: quale preferire?, chi è arrivato?

Aggettivo numerale cardinale → NUM  
Esempi: uno, due, tre, cento, mille.

Aggettivo numerale ordinale → ADJ in UD italiano  
Esempi: primo, secondo, terzo, ultimo.  
UD italiano include gli ordinali nella classe ADJ.

Pronome personale → PRON  
Esempi: io, tu, lui, lei, noi, voi, loro.

Pronome clitico → PRON  
Esempi: mi, ti, lo, la, gli, le, ci, vi, si, ne.  
Questi elementi nella grammatica italiana sono spesso chiamati particelle pronominali, ma in UD vanno normalmente trattati come pronomi, non come PART.

Pronome possessivo  
* → PRON quando sostituisce un nome  
Esempio: questo è il mio.
* → DET quando accompagna un nome  
Esempio: il mio libro.

Pronome dimostrativo  
* → PRON quando sostituisce un nome  
Esempi: questo, quello, ciò.
* → DET quando accompagna un nome  
Esempio: questo libro.

Pronome relativo → PRON  
Esempi: che, cui, il quale, la quale, i quali.  
Attenzione: che può anche essere SCONJ quando introduce una subordinata completiva.

Pronome indefinito  
* → PRON quando sostituisce un nome  
Esempi: qualcuno, qualcosa, nessuno, molti.
* → DET quando determina un nome  
Esempi: molti studenti, nessuna risposta.

Pronome interrogativo  
* → PRON  
Esempi: chi?, che cosa?, quale?
* → DET se determina un nome  
Esempio: quale libro?

Verbo lessicale → VERB  
Esempi: andare, fare, studiare, lavorare, decidere.  
UD distingue VERB dai verbi ausiliari: VERB copre i verbi principali, non gli ausiliari né le copule verbali in senso stretto.

Verbo ausiliare → AUX  
Esempi: essere e avere nei tempi composti; essere e venire nella passiva; stare in costruzioni come sto arrivando; i modali secondo la documentazione UD italiana.

Verbo copulativo → AUX quando è copula in senso stretto  
Esempio: essere in la casa è grande.  
In UD la copula in senso stretto rientra in AUX. Se invece essere ha uso pienamente lessicale, per esempio con valore di esistere o trovarsi, può essere analizzato diversamente secondo il treebank.

Verbo modale o servile → AUX in UD italiano  
Esempi: potere, dovere, volere.  
La documentazione UD generale ammette che i modali possano essere VERB oppure AUX secondo la lingua; la documentazione UD italiana li tratta come ausiliari modali.

Avverbio → ADV  
Esempi: bene, male, rapidamente, ieri, qui, sempre, forse, molto.

Preposizione semplice → ADP  
Esempi: di, a, da, in, con, su, per, tra, fra.  
UD usa ADP, “adposition”, categoria generale che include preposizioni e postposizioni.

Preposizione articolata → ADP + DET se scomposta  
Esempi: del = di + il; alla = a + la; nello = in + lo.  
Se non viene scomposta dal tokenizer, può comparire come token unico, ma concettualmente contiene una preposizione e un articolo. In UD, per le forme fuse, conviene controllare se il treebank separa il token in più parole sintattiche.

Congiunzione coordinante → CCONJ  
Esempi: e, o, ma, però, né.

Congiunzione subordinante → SCONJ  
Esempi: che, se, perché, quando, mentre, benché, affinché.  
Attenzione: alcune parole, come che, se, quando, possono avere tag diversi secondo la funzione nella frase.

Interiezione → INTJ  
Esempi: ah, oh, ahi, ehi, boh, mah.

Numerale  
* → NUM se cardinale  
Esempi: uno, due, tre, cento.
* → ADJ se ordinale in UD italiano  
Esempi: primo, secondo, terzo.

Simbolo → SYM  
Esempi: %, €, $, +, =.  
Non è una parte del discorso scolastica tradizionale, ma è utile nel tagging NLP.

Punteggiatura → PUNCT  
Esempi: punto, virgola, punto interrogativo, punto esclamativo, parentesi.  
Non è una categoria lessicale tradizionale, ma è un tag UPOS.

Elemento altro / non classificato → X  
Esempi: parole straniere non analizzate, errori, frammenti, token non classificabili.

Particella → PART  
Categoria da usare con prudenza. In UD il tag PART è residuale e va usato solo quando non è adatto un altro tag più specifico. Non tutte le “particelle” della grammatica tradizionale italiana diventano PART in UPOS. Per esempio, le particelle pronominali italiane sono normalmente PRON, non PART.

## Schema sintetico

Grammatica italiana → UPOS

Nome comune → NOUN  
Nome proprio → PROPN  
Articolo → DET  
Articolo partitivo → DET oppure ADP + DET secondo tokenizzazione e treebank  
Aggettivo qualificativo → ADJ  
Aggettivo possessivo → DET  
Aggettivo dimostrativo → DET oppure PRON secondo l’uso  
Aggettivo indefinito → DET oppure PRON secondo l’uso  
Aggettivo interrogativo/esclamativo → DET oppure PRON secondo l’uso  
Numerale cardinale → NUM  
Numerale ordinale → ADJ  
Pronome → PRON  
Verbo lessicale → VERB  
Verbo ausiliare → AUX  
Verbo copulativo → AUX quando è copula in senso stretto  
Verbo modale/servile → AUX in UD italiano  
Avverbio → ADV  
Preposizione → ADP  
Preposizione articolata → ADP + DET, se scomposta  
Congiunzione coordinante → CCONJ  
Congiunzione subordinante → SCONJ  
Interiezione → INTJ  
Punteggiatura → PUNCT  
Simbolo → SYM  
Altro/non classificabile → X  
Particella → PART, solo se non è più appropriato un altro tag

## Nota operativa importante

Per un database lessicale conviene non usare un solo campo.

Meglio separare almeno:

- **categoria_grammaticale_italiana**  
Esempio: articolo, nome, aggettivo, verbo, pronome.

- **upos**  
Esempio: DET, NOUN, ADJ, VERB, PRON.

- **funzione_nel_contesto**  
Esempio: determinante, pronome, ausiliare, verbo principale, congiunzione subordinante.

In questo modo si evita l’errore di trattare il mapping come se fosse sempre 1:1.

## Alcuni riferimenti

Universal Dependencies, Universal POS tags:  
https://universaldependencies.org/u/pos/

Universal Dependencies, Morphology: General Principles:  
https://universaldependencies.org/u/overview/morphology.html

Universal Dependencies, Universal features:  
https://universaldependencies.org/u/feat/all.html

Universal Dependencies, Italian DET:  
https://universaldependencies.org/it/pos/DET.html

Universal Dependencies, Italian ADJ:  
https://universaldependencies.org/it/pos/ADJ.html

Universal Dependencies, Italian AUX:  
https://universaldependencies.org/it/pos/AUX_.html

Universal Dependencies, VERB:  
https://universaldependencies.org/u/pos/VERB.html

Universal Dependencies, ADP:  
https://universaldependencies.org/u/pos/ADP.html

Universal Dependencies, PART:  
https://universaldependencies.org/u/pos/PART.html


read: 4