
La mappatura non è perfettamente 1:1, perché  
- la grammatica italiana classifica spesso la parola in astratto, mentre  
- UPOS classifica il token nel contesto della frase. La stessa forma può quindi avere tag diversi a seconda dell’uso.  
 
Universal Dependencies definisce UPOS come insieme di categorie POS universali;  
per dettagli morfologici aggiuntivi si usano poi le **“features”**. ([universaldependencies.org][1])

## Mapping operativo grammatica italiana → UPOS

Nome comune → NOUN  
Esempi: casa, libro, lavoro, problema, decisione.

Nome proprio → PROPN  
Esempi: Marco, Roma, Italia, Google.  
Nella grammatica scolastica italiana il nome proprio è un sottotipo del nome;  
in UPOS ha un tag autonomo.

Articolo  → DET  
Esempi: il, lo, la, i, gli, le, un, uno, una.  
In UPOS l’articolo non ha un tag autonomo: rientra nei determinanti.  
La documentazione UD per l’italiano include infatti articoli definiti e indefiniti tra i DET. ([Dipendenze Universali][2])

Articolo partitivo → di norma DET, oppure ADP + DET se analizzato come forma articolata/scomposta  
Esempi: dei libri, delle persone.  
Operativamente, in un sistema NLP conviene controllare come il tokenizer/treebank rappresenta forme come del, dello, della, dei, degli, delle. In molti schemi UD le preposizioni articolate possono essere trattate come combinazioni di preposizione + articolo.

Aggettivo qualificativo → ADJ  
Esempi: bello, grande, difficile, interessante, rosso.  
UD italiano definisce ADJ come categoria delle parole che modificano nomi e ne specificano proprietà o attributi. ([Dipendenze Universali][3])

Aggettivo participiale 
* → ADJ se ha funzione aggettivale  
Esempi: porta chiusa, lavoro completato, persona interessata.
* → VERB se conserva funzione verbale.
UD segnala esplicitamente che i participi possono essere classificati come VERB o ADJ a seconda della lingua e del contesto. ([Dipendenze Universali][4])

Aggettivo possessivo → DET quando determina un nome  
Esempi: mio padre, la mia macchina.  
UD italiano indica esplicitamente che gli aggettivi possessivi sono trattati come DET. ([Dipendenze Universali][2])

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
UD italiano include gli ordinali nella classe ADJ. ([Dipendenze Universali][3])

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
UD distingue VERB dai verbi ausiliari;  
VERB copre i verbi principali, non gli ausiliari. ([Dipendenze Universali][4])

Verbo ausiliare → AUX  
Esempi: essere e avere nei tempi composti; essere nella passiva; eventuali modali secondo le convenzioni specifiche della lingua/treebank.

Verbo copulativo → AUX o VERB, secondo le linee guida della lingua e il contesto  
Esempio: essere in la casa è grande.  
In UD, la copula in senso stretto è normalmente separata dal verbo lessicale; per un progetto software conviene verificare le linee guida specifiche del treebank italiano usato.  

Verbo modale o servile → AUX o VERB, secondo le convenzioni del treebank  
Esempi: potere, dovere, volere.  
UD specifica che i modali possono essere VERB oppure AUX a seconda della lingua e del comportamento grammaticale. ([Dipendenze Universali][4])

Avverbio → ADV  
Esempi: bene, male, rapidamente, ieri, qui, sempre, forse, molto.

Preposizione semplice → ADP  
Esempi: di, a, da, in, con, su, per, tra, fra.  
UD usa ADP, “adposition”, categoria generale che include preposizioni e postposizioni. ([Dipendenze Universali][5])  

Preposizione articolata → ADP + DET se scomposta  
Esempi: del = di + il; alla = a + la; nello = in + lo.
Se non viene scomposta dal tokenizer, può comparire come token unico, ma concettualmente contiene una preposizione e un articolo.

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
Categoria da usare con prudenza.
In UD il tag PART è residuale e va usato solo quando non è adatto un altro tag più specifico. Non tutte le “particelle” della grammatica tradizionale italiana diventano PART in UPOS. Per esempio, le particelle pronominali italiane sono normalmente PRON, non PART.

## Schema sintetico

Grammatica italiana → UPOS  

Nome comune → NOUN  
Nome proprio → PROPN  
Articolo → DET  
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
Verbo modale/servile → AUX oppure VERB secondo convenzione del treebank  
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
[https://universaldependencies.org/u/pos/](https://universaldependencies.org/u/pos/)

Universal Dependencies, Italian DET:
[https://universaldependencies.org/it/pos/DET.html](https://universaldependencies.org/it/pos/DET.html)

Universal Dependencies, Italian ADJ:
[https://universaldependencies.org/it/pos/ADJ.html](https://universaldependencies.org/it/pos/ADJ.html)

Universal Dependencies, VERB:
[https://universaldependencies.org/u/pos/VERB.html](https://universaldependencies.org/u/pos/VERB.html)

Universal Dependencies, ADP:
[https://universaldependencies.org/u/pos/ADP.html](https://universaldependencies.org/u/pos/ADP.html)

[1]: https://universaldependencies.org/u/pos/ "Universal POS tags"
[2]: https://universaldependencies.org/it/pos/DET.html "DET"
[3]: https://universaldependencies.org/it/pos/ADJ.html "ADJ"
[4]: https://universaldependencies.org/u/pos/VERB.html "VERB"
[5]: https://universaldependencies.org/u/pos/ADP.html "ADP"


read: 2