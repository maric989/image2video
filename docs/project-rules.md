# Project rules

Pravila za validan video projekat u `projects/`. Ako nešto od obaveznog nedostaje, generisanje se **ne pokreće**.

## Struktura

```text
projects/<ime>/
  ├── transcript.md   # OBAVEZNO — skripta / tekst naracije
  ├── <ime>.wav       # OBAVEZNO — gotova naracija (ili audio.wav / naracija.wav)
  ├── plan.md         # OBAVEZNO — sync slika po vremenu
  ├── slike/          # OBAVEZNO — slika1.jpeg, slika2.jpeg, …
  ├── title.txt       # opciono — naslov na videu (inače ime foldera)
  ├── whisper_hint.txt # opciono — termini / imena za Whisper
  └── gotov_video.mp4 # izlaz (generiše se)
```

## Obavezno (checklist)

| Stavka | Put | Pravilo |
|--------|-----|---------|
| Folder projekta | `projects/<ime>/` | Mora postojati |
| Transcript | `transcript.md` ili `<ime>.md` | Neprazan fajl |
| Audio | `*.wav` | Preferirano `<ime>.wav`, inače `audio.wav` / `naracija.wav` / prvi `.wav` |
| Plan | `plan.md` | Neprazan, sa bar jednim validnim redom tabele |
| Slike | `slike/` | Folder mora postojati i imati ≥1 sliku (`.jpg` / `.jpeg` / `.png` / `.webp`) |

Bez bilo koje od ovih stavki → greška, nema rendera.

## `plan.md`

Svi budući planovi **moraju** biti u istom formatu kao `projects/nvidia1/plan.md`.
Za LLM generisanje plana vidi [`docs/plan-generation-rules.md`](plan-generation-rules.md).

Tabela mora imati redove tipa:

| Naziv fajla | Vreme | Skripta | Prompt |
| :--- | :--- | :--- | :--- |
| **Slika1** | **0:00 - 0:05** | ... | ... |
| **Slika2** | **0:05 - 0:08** | ... | ... |

Pravila:

- Kolona **Naziv fajla** = `SlikaN` / `slikaN` — mora da se poklopi sa fajlom u `slike/` (`slika1.jpeg`, …), case-insensitive.
- Kolona **Vreme** = `0:00`, `**0:00**`, ili opseg `0:00 - 0:05` / `**0:00 - 0:05**`. Koristi se **početak** opsega.
- Trajanje scene = do starta sledeće slike; poslednja ide do kraja audija.
- Između scena se automatski dodaje crossfade do 0,35 sekundi. Prelaz se skraćuje za kratke scene i ne zahteva dodatne kolone u planu.
- Slike dobijaju blagi centralni zoom do 4% tokom prikaza; titlovi su manji, sa crnim obrubom bez pune pozadine i postavljeni u donjoj trećini ekrana.
- Tokom renderovanja skripta prikazuje progress bar sa procentom u konzoli.
- Broj redova u planu treba da odgovara slikama koje želiš u videu (slike van plana se ne koriste).

## `transcript.md`

- Tekst skripte / naracije za taj deo.
- Brojeve piši slovima, nikad ciframa ili rimskim brojevima, da bi ih voiceover pravilno pročitao. Detalji i primeri: [`transcript-generation-rules.md`](transcript-generation-rules.md).
- Ne ide direktno na ekran kao caption — captioni dolaze iz Whisper-a sa `.wav`.
- Ako `whisper_hint.txt` ne postoji, početak transcripta (do 600 karaktera) pomaže Whisper-u da prepozna temu, imena i stručne termine.
- Transcript je pomoć za prepoznavanje, ne zamena za transkripciju audija; izgovor i tekst mogu da se razlikuju.

## `slike/`

- Imenovanje: `slika1.jpeg`, `slika2.jpeg`, … (ili `Slika1.png` — isti stem kao u planu).
- Format: vertikalno preferirano (9:16); generator radi letterbox na 1080×1920.

## Opciono

| Fajl | Uloga |
|------|--------|
| `title.txt` | Prva linija = naslov na dnu videa |
| `language.txt` | Whisper jezik (`en`, `sr`, …); ako nema, `*_en` projekti → `en`, inače `sr` |
| `whisper_hint.txt` | Opciono: prilagođen Whisper prompt; ako postoji, ima prednost nad transcriptom |
| drugi fajlovi | Ignorišu se (npr. stari exporti, note) |

`whisper_hint.txt` treba da sadrži kratak tekst sa imenima i terminima koji se zaista pominju u audiju. Koristi se najviše prvih 600 karaktera. Pošto Whisper prompt može da utiče na prepoznavanje, netačan ili nepovezan hint može pogoršati titlove.

## Pokretanje

```bash
source .venv/bin/activate
python main.py <ime>
```

Izlaz: `projects/<ime>/gotov_video.mp4`.

## Šta generator radi sa čime

| Ulaz | Uloga u renderu |
|------|------------------|
| `.wav` | Audio traka + Whisper captions |
| `plan.md` | Timing / redosled slika |
| `slike/` | Vizuelni sadržaj scena |
| `transcript.md` | Obavezna skripta; koristi se kao Whisper hint ako `whisper_hint.txt` ne postoji |
| `title.txt` | Naslov overlay (opciono) |
| `whisper_hint.txt` | Opciono, projekatno podešavanje Whisper-a sa prednošću nad transcriptom |

Slike prelaze jedna u drugu automatski, bez podešavanja u `plan.md`. Trajanje crossfade-a je najviše 0,35 sekundi i skraćuje se ako je neka od susednih scena kratka.
