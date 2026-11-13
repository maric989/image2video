# Vodič za pravljenje Text-to-Video aplikacije u Pythonu

Ovaj vodič će ti pomoći da postaviš svoj lokalni, potpuno besplatni video generator. Skripta će uzeti tvoj tekst, pročitati ga AI glasom, izračunati koliko audio traje, ravnomerno rasporediti tvoje slike u videu, i zalepiti naslov preko svega.

## Korak 1: Priprema sistema

Pre nego što krenemo sa kodiranjem, moraš imati instalirane sledeće alate na kompjuteru:

1. **Python:** (Verzija 3.8 ili novija).
2. **ImageMagick:** `MoviePy` ga koristi za renderovanje teksta (titlova).
   * Preuzmi ga sa zvaničnog sajta: `https://imagemagick.org/script/download.php`
   * **VAŽNO:** Prilikom instalacije na Windowsu, obavezno štikliraj opciju **"Install legacy utilities (e.g. convert)"**.

## Korak 2: Struktura foldera

Napravi jedan prazan folder na kompjuteru (npr. `VideoGenerator`) i u njemu napravi sledeću strukturu:

```text
VideoGenerator/
│
├── slike/              # Ovde ubacujes svoje slike (npr. 1.jpg, 2.jpg)
├── tekst.txt           # Ovde kucas tekst koji zelis da AI procita
├── requirements.txt    # Spisak paketa za instalaciju
└── main.py             # Tvoj Python kod
```

## Korak 3: Instalacija paketa

Napravi fajl `requirements.txt` i u njega upiši sledeće:
```text
edge-tts
moviepy==1.0.3
```

Otvori terminal (Command Prompt) u tom folderu i ukucaj:
```bash
pip install -r requirements.txt
```

## Korak 4: Python Kod

Otvori `main.py` i prekopiraj ovaj kod u njega. Ovaj kod koristi besplatan Microsoft-ov AI glas i sastavlja slike i audio.

```python
import asyncio
import os
import edge_tts
from moviepy.editor import *

# --- PODEŠAVANJA ---
TEKST_FAJL = "tekst.txt"
SLIKE_FOLDER = "slike"
IZLAZNI_VIDEO = "gotov_video.mp4"
# Koristimo engleski glas za test. Za srpski mozes staviti: "sr-RS-NicholasNeural"
GLAS = "en-US-ChristopherNeural" 

async def generisi_audio(tekst, izlazni_audio):
    """Funkcija koja koristi Edge-TTS za generisanje besplatnog AI glasa."""
    communicate = edge_tts.Communicate(tekst, GLAS)
    await communicate.save(izlazni_audio)

def napravi_video():
    # 1. Čitanje teksta iz fajla
    with open(TEKST_FAJL, "r", encoding="utf-8") as f:
        tekst = f.read()

    # 2. Generisanje audija
    audio_fajl = "naracija.mp3"
    print("1. Generišem AI glas...")
    asyncio.run(generisi_audio(tekst, audio_fajl))

    # 3. Učitavanje generisanog audija
    print("2. Analiziram audio i slike...")
    audio_klip = AudioFileClip(audio_fajl)
    ukupno_trajanje = audio_klip.duration

    # 4. Učitavanje slika
    # Sortiramo ih abecedno (nazovi ih 01.jpg, 02.jpg da bi isle redom)
    slike = sorted([os.path.join(SLIKE_FOLDER, img) for img in os.listdir(SLIKE_FOLDER) if img.endswith(('.png', '.jpg', '.jpeg'))])
    
    if not slike:
        print("Greška: Nema slika u folderu 'slike'. Ubaci slike pa probaj ponovo!")
        return

    # Računamo koliko sekundi svaka slika treba da bude na ekranu
    trajanje_po_slici = ukupno_trajanje / len(slike)
    
    video_klipovi = []
    for slika_putanja in slike:
        # Resize slike da bude u formatu (npr. Shorts 1080x1920). 
        # Za sada cemo samo uzeti originalnu sliku i podesiti joj trajanje.
        klip = ImageClip(slika_putanja).set_duration(trajanje_po_slici)
        video_klipovi.append(klip)

    # Spajamo slike jednu za drugom
    finalni_video = concatenate_videoclips(video_klipovi, method="compose")

    # 5. Dodavanje Naslova / Titla
    print("3. Dodajem tekst...")
    # Da bi ovo radilo, ImageMagick mora biti instaliran
    naslov = "THE ENTIRE HISTORY"
    txt_clip = TextClip(naslov, fontsize=70, color='white', font='Arial-Bold', bg_color='black')
    
    # Pozicioniramo tekst dole na sredinu i govorimo mu da traje koliko i ceo video
    txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(ukupno_trajanje)

    # 6. Spajanje svega: Slike + Tekst preko njih + Audio
    finalni_video = CompositeVideoClip([finalni_video, txt_clip])
    finalni_video = finalni_video.set_audio(audio_klip)

    # 7. Renderovanje u MP4 fajl
    print("4. Renderujem video fajl (ovo moze potrajati par minuta)...")
    finalni_video.write_videofile(IZLAZNI_VIDEO, fps=24, codec="libx264", audio_codec="aac")
    
    print("\nUspešno završeno! Tvoj video je sačuvan kao", IZLAZNI_VIDEO)

if __name__ == "__main__":
    napravi_video()
```

## Korak 5: Kako se koristi

1. Otvori `tekst.txt` i unesi tekst na engleskom (ili promeni na srpski glas u kodu i unesi srpski).
2. Ubaci 3-4 slike u folder `slike` i nazovi ih `01.jpg`, `02.jpg`, `03.jpg`.
3. Otvori terminal i pokreni skriptu komandom:
   ```bash
   python main.py
   ```
4. Sačekaj par sekundi, i u tvom folderu će se pojaviti `gotov_video.mp4`!