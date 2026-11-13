#!/usr/bin/env python3
"""Generisanje videa po projektu: python main.py <ime_projekta>"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image as PILImage
from faster_whisper import WhisperModel
from moviepy.config import change_settings
from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
)
from moviepy.video.compositing.transitions import crossfadein

# Pillow 10+ uklonio ANTIALIAS; MoviePy 1.0.3 ga još očekuje
if not hasattr(PILImage, "ANTIALIAS"):
    PILImage.ANTIALIAS = PILImage.Resampling.LANCZOS

# ImageMagick 7 na macOS-u koristi `magick` umesto zastarelog `convert`
change_settings({"IMAGEMAGICK_BINARY": "magick"})

PROJECTS_DIR = Path("projects")
# Debeli display font za Shorts/TikTok čitljivost
FONT = "/System/Library/Fonts/Supplemental/Impact.ttf"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_SIZE = (1080, 1920)  # vertikalni Shorts/Reels format
SUBTITLE_Y = 1180  # malo više da ne prekriva fokus na slici
WHISPER_MODEL = "small"
WORDS_PER_CHUNK = 3
WHISPER_HINT_MAX_CHARS = 600
IMAGE_TRANSITION_DURATION = 0.35


def nadji_projekat(ime: str) -> Path:
    putanja = PROJECTS_DIR / ime
    if not putanja.is_dir():
        print(f"Greška: projekat '{ime}' ne postoji u {PROJECTS_DIR}/")
        dostupni = [p.name for p in sorted(PROJECTS_DIR.iterdir()) if p.is_dir()]
        print("Dostupni projekti:", ", ".join(dostupni) or "(nema)")
        sys.exit(1)
    return putanja


def nadji_transcript(projekat: Path) -> Path:
    kandidati = [
        projekat / "transcript.md",
        projekat / f"{projekat.name}.md",
    ]
    for k in kandidati:
        if k.is_file() and k.stat().st_size > 0:
            return k
    print(f"Greška: u {projekat}/ nema transcript.md (obavezno — vidi docs/project-rules.md)")
    sys.exit(1)


def nadji_wav(projekat: Path) -> Path:
    kandidati = [
        projekat / "audio.wav",
        projekat / f"{projekat.name}.wav",
        projekat / "naracija.wav",
    ]
    for k in kandidati:
        if k.is_file():
            return k
    wav_fajlovi = sorted(projekat.glob("*.wav"))
    if wav_fajlovi:
        return wav_fajlovi[0]
    print(f"Greška: u {projekat}/ nema .wav fajla")
    sys.exit(1)


def lista_slika(projekat: Path) -> list[Path]:
    slike_dir = projekat / "slike"
    if not slike_dir.is_dir():
        print(f"Greška: nema foldera {slike_dir}/")
        sys.exit(1)
    slike = [
        p for p in slike_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]
    if not slike:
        print(f"Greška: nema slika u {slike_dir}/")
        sys.exit(1)
    return slike


def nadji_sliku_po_imenu(slike: list[Path], naziv: str) -> Path | None:
    """Slika1 / slika1 -> slika1.jpeg (case-insensitive, bilo koja ekstenzija)."""
    cilj = Path(naziv).stem.lower()
    for p in slike:
        if p.stem.lower() == cilj:
            return p
    cilj_compact = re.sub(r"[\s_\-]+", "", cilj)
    for p in slike:
        if re.sub(r"[\s_\-]+", "", p.stem.lower()) == cilj_compact:
            return p
    return None


def parse_vreme(tekst: str) -> float:
    """'0:08' ili '1:03' -> sekunde."""
    delovi = [int(x) for x in tekst.strip().split(":")]
    if len(delovi) == 2:
        return delovi[0] * 60 + delovi[1]
    if len(delovi) == 3:
        return delovi[0] * 3600 + delovi[1] * 60 + delovi[2]
    raise ValueError(f"Nepoznat format vremena: {tekst}")


def ucitaj_plan(projekat: Path) -> list[dict]:
    """
    Čita plan.md tabelu samo za sync slika: Naziv | Vreme | ...
    Podržava '0:00', '**0:00**', '0:00 - 0:05', '**0:00 - 0:05**'.
    Vraća [{"naziv", "start"}, ...] sortirano po vremenu (koristi početak opsega).
    Obavezno — vidi docs/project-rules.md.
    """
    plan = projekat / "plan.md"
    if not plan.is_file() or plan.stat().st_size == 0:
        print(f"Greška: u {projekat}/ nema plan.md (obavezno — vidi docs/project-rules.md)")
        sys.exit(1)

    tekst = plan.read_text(encoding="utf-8")
    stavke: list[dict] = []
    # | **Slika1** | **0:00 - 0:05** | ... |  ili  | Slika1 | 0:00 |
    red_re = re.compile(
        r"\|\s*\**(?P<naziv>[A-Za-z]+\d+)\**\s*"
        r"\|\s*\**(?P<vreme>\d+:\d{2}(?::\d{2})?(?:\s*[-–—]\s*\d+:\d{2}(?::\d{2})?)?)\**\s*\|"
    )
    for m in red_re.finditer(tekst):
        naziv = m.group("naziv")
        if naziv.lower().startswith("naziv"):
            continue
        vreme_raw = m.group("vreme")
        # Uzmi samo start iz opsega "0:00 - 0:05"
        start_str = re.split(r"\s*[-–—]\s*", vreme_raw)[0].strip()
        stavke.append({"naziv": naziv, "start": parse_vreme(start_str)})

    if not stavke:
        print(
            f"Greška: plan.md postoji ali nema prepoznatih redova tabele "
            f"(vidi docs/project-rules.md)"
        )
        sys.exit(1)

    stavke.sort(key=lambda x: x["start"])
    return stavke


def ucitaj_whisper_hint(projekat: Path, transcript: Path) -> str:
    """Koristi projekatni hint ako postoji, inače početak transcripta."""
    hint_fajl = projekat / "whisper_hint.txt"
    izvor = hint_fajl if hint_fajl.is_file() else transcript
    tekst = izvor.read_text(encoding="utf-8")
    tekst = re.sub(r"```.*?```", " ", tekst, flags=re.DOTALL)
    tekst = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", tekst)
    tekst = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", tekst)
    tekst = re.sub(r"^\s{0,3}#{1,6}\s*", "", tekst, flags=re.MULTILINE)
    tekst = re.sub(r"[*_`~>#|]", " ", tekst)
    tekst = re.sub(r"\s+", " ", tekst).strip()
    if len(tekst) > WHISPER_HINT_MAX_CHARS:
        tekst = tekst[:WHISPER_HINT_MAX_CHARS].rsplit(" ", 1)[0]
    return tekst


def pripremi_image_klip(putanja: Path, trajanje: float) -> ImageClip:
    klip = ImageClip(str(putanja)).resize(height=VIDEO_SIZE[1]).set_duration(trajanje)
    if klip.w != VIDEO_SIZE[0] or klip.h != VIDEO_SIZE[1]:
        klip = klip.on_color(
            size=VIDEO_SIZE, color=(0, 0, 0), pos=("center", "center")
        )
    return klip


def napravi_klipove_iz_plana(
    plan: list[dict],
    slike: list[Path],
    ukupno_trajanje: float,
) -> CompositeVideoClip:
    scene_podaci: list[tuple[Path, float]] = []

    for i, scena in enumerate(plan):
        naziv = scena["naziv"]
        putanja = nadji_sliku_po_imenu(slike, naziv)
        if putanja is None:
            print(f"Greška: plan traži '{naziv}' ali nema odgovarajuće slike u slike/")
            print("Dostupne:", ", ".join(p.name for p in sorted(slike)))
            sys.exit(1)
        start = scena["start"]
        kraj = plan[i + 1]["start"] if i + 1 < len(plan) else ukupno_trajanje
        trajanje = max(kraj - start, 0.1)
        scene_podaci.append((putanja, trajanje))

    prelazi = [
        min(
            IMAGE_TRANSITION_DURATION,
            scene_podaci[i][1] / 2,
            scene_podaci[i + 1][1] / 2,
        )
        for i in range(len(scene_podaci) - 1)
    ]

    image_klipovi: list[ImageClip] = []
    start_klipa = 0.0
    for i, (putanja, trajanje) in enumerate(scene_podaci):
        fade_in = prelazi[i - 1] if i > 0 else 0
        fade_out = prelazi[i] if i < len(prelazi) else 0
        klip = pripremi_image_klip(putanja, trajanje + fade_out)
        if fade_in:
            klip = klip.fx(crossfadein, fade_in)
        klip = klip.set_start(start_klipa)
        image_klipovi.append(klip)
        kraj = start_klipa + trajanje
        print(
            f"  {putanja.name}: {start_klipa:.1f}s → {kraj:.1f}s "
            f"({trajanje:.1f}s)"
            + (f", crossfade {fade_in:.2f}s" if fade_in else "")
        )
        start_klipa = kraj

    return CompositeVideoClip(image_klipovi, size=VIDEO_SIZE).set_duration(
        start_klipa
    )


def ffmpeg_bin() -> str:
    """Preferiraj system ffmpeg, inače imageio-ffmpeg binary (MoviePy dependency)."""
    from shutil import which

    putanja = which("ffmpeg")
    if putanja:
        return putanja
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        print("Greška: ffmpeg nije dostupan (ni system ni imageio-ffmpeg).")
        sys.exit(1)


def ucitaj_audio_za_whisper(wav: Path) -> np.ndarray:
    """
    Učitaj wav kao mono float32 @ 16kHz preko ffmpeg-a.
    Zaobilazi PyAV decode_audio (inkompatibilnost av 19 + faster-whisper).
    """
    cmd = [
        ffmpeg_bin(),
        "-v",
        "error",
        "-i",
        str(wav),
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-",
    ]
    try:
        out = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Greška: ffmpeg nije uspeo da pročita {wav}: {e}")
        sys.exit(1)
    return np.frombuffer(out, dtype=np.float32).copy()


def transkribuj_reci(wav: Path, hint: str) -> list[dict]:
    """faster-whisper word-level timestamps iz lokalnog .wav fajla."""
    print(f"   Model: {WHISPER_MODEL} (word_timestamps=True)")
    if hint:
        print(f"   initial_prompt: {hint[:80]}…")
    audio = ucitaj_audio_za_whisper(wav)
    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        audio,
        word_timestamps=True,
        language="sr",
        vad_filter=True,
        initial_prompt=hint or None,
        condition_on_previous_text=True,
    )
    print(f"   Detektovan jezik: {info.language} (p={info.language_probability:.2f})")

    reci: list[dict] = []
    for segment in segments:
        if not segment.words:
            continue
        for w in segment.words:
            tekst = (w.word or "").strip()
            if not tekst:
                continue
            reci.append({"word": tekst, "start": float(w.start), "end": float(w.end)})
    return reci


def grupisi_u_chunkove(
    reci: list[dict], max_reci: int = WORDS_PER_CHUNK
) -> list[dict]:
    """Grupiše reči u kratke TikTok chunk-ove (3–4 reči)."""
    if not reci:
        return []

    chunkovi: list[dict] = []
    i = 0
    while i < len(reci):
        grupa = reci[i : i + max_reci]
        # Ako poslednja reč u chunku ima jaku interpunkciju, ne guši dalje —
        # max_reci već seče; dodatno seci ranije na . ! ? ,
        cut = len(grupa)
        for j, r in enumerate(grupa):
            if j == 0:
                continue
            if re.search(r"[.!?…]$", r["word"]):
                cut = j + 1
                break
            if j >= 2 and re.search(r"[,;:]$", r["word"]):
                cut = j + 1
                break
        grupa = reci[i : i + cut]
        tekst = " ".join(r["word"] for r in grupa).strip()
        tekst = re.sub(r"\s+", " ", tekst)
        start = grupa[0]["start"]
        end = grupa[-1]["end"]
        if end <= start:
            end = start + 0.15
        chunkovi.append({"text": tekst, "start": start, "end": end})
        i += cut

    return chunkovi


def napravi_caption_klip(tekst: str, start: float, end: float) -> TextClip | None:
    if not tekst:
        return None
    trajanje = max(end - start, 0.12)
    # Impact + debeli stroke = Shorts čitljivost; blaga crna pozadina iza reči
    clip = TextClip(
        tekst.upper(),
        fontsize=70,
        color="white",
        stroke_color="black",
        stroke_width=5,
        font=FONT,
        method="caption",
        size=(900, None),
        align="center",
        bg_color="black",
    )
    return (
        clip.set_start(start)
        .set_duration(trajanje)
        .set_position(("center", SUBTITLE_Y))
    )


def napravi_whisper_captions(
    wav: Path, projekat: Path, transcript: Path
) -> list[TextClip]:
    print("3. Transkribujem audio (faster-whisper)...")
    hint = ucitaj_whisper_hint(projekat, transcript)
    reci = transkribuj_reci(wav, hint)
    print(f"   Reči: {len(reci)}")
    chunkovi = grupisi_u_chunkove(reci, max_reci=WORDS_PER_CHUNK)
    print(f"   Caption chunk-ova: {len(chunkovi)}")

    klipovi: list[TextClip] = []
    for c in chunkovi:
        print(f"   [{c['start']:.2f}-{c['end']:.2f}] {c['text']}")
        clip = napravi_caption_klip(c["text"], c["start"], c["end"])
        if clip is not None:
            klipovi.append(clip)
    return klipovi


def naslov_projekta(projekat: Path) -> str:
    title_fajl = projekat / "title.txt"
    if title_fajl.is_file():
        tekst = title_fajl.read_text(encoding="utf-8").strip()
        if tekst:
            return tekst.splitlines()[0].strip()
    return projekat.name.replace("_", " ").upper()


def napravi_video(ime_projekta: str) -> None:
    projekat = nadji_projekat(ime_projekta)
    transcript = nadji_transcript(projekat)
    wav = nadji_wav(projekat)
    slike = lista_slika(projekat)
    plan = ucitaj_plan(projekat)
    izlaz = projekat / "gotov_video.mp4"
    naslov = naslov_projekta(projekat)

    print(f"Projekat:   {projekat}")
    print(f"Transcript: {transcript.name}")
    print(f"Audio:      {wav.name}")
    print(f"Plan:       plan.md ({len(plan)} scena)")
    print(f"Slike:      {len(slike)}")
    print(f"Naslov:     {naslov}")

    print("1. Učitavam audio...")
    audio_klip = AudioFileClip(str(wav))
    ukupno_trajanje = audio_klip.duration
    print(f"   Trajanje audija: {ukupno_trajanje:.1f}s")

    print("2. Sastavljam slike...")
    baza = napravi_klipove_iz_plana(plan, slike, ukupno_trajanje)

    caption_klipovi = napravi_whisper_captions(wav, projekat, transcript)

    print("4. Dodajem naslov...")
    title_clip = TextClip(
        naslov, fontsize=60, color="white", font=FONT, bg_color="black"
    )
    title_clip = title_clip.set_position(("center", "bottom")).set_duration(
        ukupno_trajanje
    )

    # Slojevi: slike → Whisper captions → glavni naslov
    slojevi = [baza, *caption_klipovi, title_clip]
    finalni_video = CompositeVideoClip(slojevi, size=VIDEO_SIZE)
    finalni_video = finalni_video.set_audio(audio_klip)
    finalni_video = finalni_video.set_duration(ukupno_trajanje)

    print("5. Renderujem video (može potrajati)...")
    finalni_video.write_videofile(
        str(izlaz), fps=24, codec="libx264", audio_codec="aac"
    )

    print(f"\nUspešno! Video: {izlaz}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generiši video za jedan projekat iz projects/"
    )
    parser.add_argument(
        "projekat",
        help="Ime foldera u projects/ (npr. nvidia1)",
    )
    args = parser.parse_args()
    napravi_video(args.projekat)


if __name__ == "__main__":
    main()
