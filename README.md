# video-master

Lokalni generator vertikalnih videa (1080×1920). Svaki video je zaseban folder u `projects/` sa **wav**, **slikama**, **planom** i **transcriptom**.

Pravila za validan projekat: [`docs/project-rules.md`](docs/project-rules.md).

## Kako radi

```text
projects/<ime>/
  ├── transcript.md   # OBAVEZNO — skripta / tekst
  ├── *.wav           # OBAVEZNO — gotova naracija
  ├── plan.md         # OBAVEZNO — vremena po slici
  ├── slike/          # OBAVEZNO — slika1.jpeg, slika2.jpeg, …
  ├── title.txt       # opciono — naslov na videu
  ├── whisper_hint.txt # opciono — termini / imena za Whisper
  └── gotov_video.mp4 # izlaz
```

`python main.py <ime>` spaja audio + slike po `plan.md` → `gotov_video.mp4`.

## Preduslovi

- Python 3.8+
- ImageMagick (`brew install imagemagick`) — za naslov (`TextClip`)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Pokretanje

```bash
source .venv/bin/activate
python main.py nvidia1
```

Izlaz: `projects/nvidia1/gotov_video.mp4`

## Novi projekat

```bash
mkdir -p projects/moji_video/slike
# obavezno: transcript.md, plan.md, *.wav, slike/
# opciono: title.txt
python main.py moji_video
```

Detaljna checklist i format plana: [`docs/project-rules.md`](docs/project-rules.md).

### `plan.md` (primer)

| Naziv fajla | Vreme | Skripta | Prompt |
| :--- | :--- | :--- | :--- |
| **Slika1** | 0:00 | ... | ... |
| **Slika2** | 0:08 | ... | ... |

Ime fajla u planu (`Slika1`) mora da se poklopi sa slikom u `slike/` (`slika1.jpeg`) — case-insensitive, bilo koja ekstenzija `.jpg` / `.jpeg` / `.png`.

## Primer

`projects/nvidia1` — priča o Nvidiji (deo 1), 9 slika po `plan.md`, audio `nvidia1.wav`.

## Tech spec

### Stack

| Sloj | Tehnologija | Uloga |
|------|-------------|--------|
| Jezik | Python 3.8+ | CLI generator (`main.py`) |
| Video | [MoviePy](https://zulko.github.io/moviepy/) `1.0.3` | ImageClip, TextClip, CompositeVideoClip, export |
| Slike | Pillow (via MoviePy) | resize / frame processing |
| Audio | lokalni `.wav` | ulazna naracija (trenutno bez TTS u pipeline-u) |
| TTS (opciono / legacy) | [edge-tts](https://github.com/rany2/edge-tts) | Microsoft Edge neural glasovi (u `requirements.txt`, nije u aktivnom `main.py` flow-u) |
| Tekst overlay | ImageMagick 7 (`magick`) | MoviePy `TextClip` |
| Font | Arial Bold (macOS system path) | naslov na dnu videa |

### Izlazni format

| Parametar | Vrednost |
|-----------|----------|
| Rezolucija | **1080 × 1920** (vertikalni Shorts/Reels) |
| FPS | 24 |
| Video codec | `libx264` |
| Audio codec | `aac` |
| Kontejner | `.mp4` (`gotov_video.mp4`) |

### Pipeline

1. Učitaj projekat iz `projects/<ime>/`
2. Proveri obavezno: `transcript.md`, `.wav`, `plan.md`, `slike/`
3. Parsira `plan.md` — mapira `SlikaN` → start vreme; trajanje = do sledeće slike (poslednja do kraja audija)
4. Resize / letterbox na 1080×1920 i automatski kratki crossfade između scena (do 0,35 sekundi)
5. Whisper captions sa audija + overlay naslova (`title.txt` ili ime foldera)
   - Koristi `whisper_hint.txt` ako postoji; u suprotnom koristi početak `transcript.md` kao pomoć za imena i termine
6. Spoji audio + render MP4

### Sistemski dependency-ji

```bash
# macOS
brew install imagemagick
# MoviePy mora da vidi `magick` (podešeno u main.py preko IMAGEMAGICK_BINARY)
```

### Python dependency-ji

Vidi [`requirements.txt`](requirements.txt):

- `moviepy==1.0.3`
- `edge-tts` (rezervisano za budući TTS korak)

## Fajlovi

| Fajl | Opis |
|------|------|
| `main.py` | Generator (CLI po projektu) |
| `docs/project-rules.md` | Obavezna struktura projekta |
| `requirements.txt` | Python paketi |
| `UPUTSTVO.md` | Detaljniji koraci |
| `spec.md` | Originalni vodič / spec |
| `projects/` | Svi video projekti |

## Napomene

- Format izlaza je vertikalni (Shorts/Reels).
- Naslov dolazi iz `title.txt`, inače iz imena foldera.
- Whisper hint se podešava u opcionom `whisper_hint.txt`; ako ga nema, koristi se početak obaveznog `transcript.md`.
- Slike automatski prelaze jedna u drugu kratkim crossfade-om (do 0,35 sekundi); `plan.md` ne treba menjati, a trajanje videa ostaje vezano za audio.
- Render može potrajati zavisno od dužine audija i broja slika.
- Pillow 10+ više nema `Image.ANTIALIAS` — u `main.py` je kompatibilnosni patch za MoviePy 1.0.3.
