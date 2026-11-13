# Uputstvo: Text-to-Video po projektu

Svaki video je jedan folder u `projects/`. Skripta uzima **wav + slike + transcript** i pravi `gotov_video.mp4`.

## Struktura

```text
video-master/
├── main.py
├── requirements.txt
├── projects/
│   └── nvidia1/
│       ├── transcript.md   # tekst / skripta
│       ├── nvidia1.wav     # gotova naracija (audio)
│       ├── slike/          # 01.jpg, 02.jpg, ...
│       └── gotov_video.mp4 # izlaz (posle rendera)
└── .venv/
```

Obavezno u svakom projektu:

| Stvar | Gde |
|-------|-----|
| Transcript | `transcript.md` (ili `<ime>.md`) |
| Audio | `*.wav` (npr. `nvidia1.wav` ili `audio.wav`) |
| Slike | `slike/*.jpg` / `*.png` |

## Setup (jednom)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
brew install imagemagick   # za naslov u videu
```

## Novi projekat

```bash
mkdir -p projects/moji_projekat/slike
# ubaci transcript.md, audio.wav, slike u slike/
```

## Pokretanje

```bash
source .venv/bin/activate
python main.py nvidia1
```

Izlaz: `projects/nvidia1/gotov_video.mp4`

## Česte greške

| Problem | Rešenje |
|---------|---------|
| Projekat ne postoji | Proveri ime foldera u `projects/` |
| Nema slika | Ubaci fajlove u `projects/<ime>/slike/` |
| Nema .wav | Ubaci wav u folder projekta |
| ImageMagick / TextClip | `brew install imagemagick` |
