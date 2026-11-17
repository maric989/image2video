# ideology_explained — vizuelni vodič serijala

Ovaj dokument definiše zajednički vizuelni stil za sve videe serijala `ideology_explained` (npr. komunizam, nacionalizam, kapitalizam). Svaki novi `plan.md` treba da prati ovaj vodič kako bi slike pripadale istom serijalu.

## Kako izgledaju postojeće slike

- Vertikalna kompozicija 9:16.
- Topla, svetla krem/bež pozadina, uglavnom prazna.
- Ručno crtana 2D ilustracija, kao jednostavan urednički crtani film.
- Debele, jasno vidljive crne konture i ravne boje; bez gradijenata, foto-tekstura i 3D izgleda.
- Prigušena, ograničena paleta: krem, crna, crvena, zagasita plava, zelena i oker; izbegavati neonske i previše zasićene boje.
- Likovi su jednostavni, lako čitljivi i ekspresivni. Lica i gestovi nose šalu.
- Glavni prizor/likovi su obično grupisani u donjoj polovini slike, često oslonjeni na jednostavnu crnu podnu liniju. Ostaviti dosta praznog prostora iznad.
- Jedna jasna vizuelna ideja po slici; geg treba da pomogne objašnjenju, a ne da zatrpa kadar.
- Bez teksta, slova, natpisa, logotipa ili watermark-a unutar slike. Simbole koristiti samo kada su važni za temu.
- Stvarne istorijske ličnosti, poput Karla Marksa ili Josipa Broza Tita, mogu da se prikažu kao prepoznatljive karikature. Ostali likovi treba da ostanu originalni, generički likovi.

## Ponavljajući narator

Kada se narator pojavljuje, zadrži isti dizajn kroz ceo serijal: mršav, jednostavan crtani muškarac sa velikim izražajnim očima, raščupanom/šiljatom belom kosom, crnim odelom i pantalonama. Njegov izraz može da se menja prema sceni, ali odeća i osnovne crte ostaju iste. Ne dodavati mu stalno nove rekvizite ili drugačiji kostim.

U promptu ponovi opis naratora; generator slika ne pamti nužno lik iz prethodnih slika.

## Šablon prompta

Svaki prompt treba da počne ovim stilskim opisom, zatim da opiše samo prizor za konkretnu scenu i da završi zajedničkim ograničenjima:

```text
2D hand-drawn editorial cartoon illustration, vertical 9:16 composition, warm light cream-beige empty background, thick slightly imperfect black outlines, simple expressive characters with clear funny facial expressions and gestures, flat muted colors in a limited palette of cream, charcoal, dusty blue, muted red, olive green and ochre, subjects grouped in the lower half with generous empty space above, simple thin black ground line. [OPIŠI JEDAN JASAN PRIZOR I BLAGI VIZUELNI GEG]. If the recurring narrator appears, use the same slim cartoon man with messy spiky white hair, large expressive eyes, black suit and trousers. no text, no letters, no logos, no watermark, no photorealism, no gradients, no 3D.
```

## Ton humora

- Koristi blage fizičke gegove, preterane rekvizite i čitljive reakcije likova.
- Humor treba da razjasni pojam, npr. vaga koja se naginje ili prevelika knjiga koju lik jedva nosi.
- Političke teme i stvarne istorijske tragedije obrađivati pažljivo; ne praviti žrtve nasilja predmetom šale.
- Ne forsirati šalu u svakoj sceni. Važnije je da prizor jasno prenese ideju i da se uklopi sa susednim slikama.

## Provera pre čuvanja `plan.md`

- Svih 13 (ili drugi dogovoreni broj) scena koristi isti krem/bež, ručno crtani vizuelni jezik.
- Paleta, konture, raspored likova i količina praznog prostora ostaju dosledni.
- Narator ima isti opis i izgled kad god se pojavi.
- Promptovi opisuju konkretan kadar, a ne menjaju nasumično medijum, estetiku ili paletu.
- Promptovi su na engleskom za generisanje slika, a tekst „Skripta“ u `plan.md` prati jezik voiceovera.
