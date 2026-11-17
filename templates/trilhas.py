"""
Casa Onze — gera as trilhas instrumentais dos Reels.

As trilhas são sintetizadas aqui mesmo (violão dedilhado, pad e percussão leve),
então não dependem de licença de terceiros. Rode uma vez para criar audio/*.m4a:

    python templates/trilhas.py
"""
import subprocess
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audio"

NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def hz(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave + 1) - 69) / 12)


def pluck(freq, dur, bright=0.5, seed=0):
    """Corda dedilhada (Karplus-Strong)."""
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    period = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, period)
    out = np.empty(n)
    decay = 0.996
    for i in range(n):
        out[i] = buf[i % period]
        buf[i % period] = decay * (bright * buf[i % period] + (1 - bright) * buf[(i + 1) % period])
    return out * np.exp(-np.linspace(0, 3.2, n))


def pad(freqs, dur):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    s = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t + 0.7) for f in freqs)
    env = np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 0.8)
    b, a = butter(2, 1800 / (SR / 2))
    return lfilter(b, a, s * env) / len(freqs)


def kick(dur=0.35):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    f = 110 * np.exp(-t * 18) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def shaker(dur=0.08, seed=1):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    b, a = butter(2, 6000 / (SR / 2), "high")
    return lfilter(b, a, rng.uniform(-1, 1, n)) * np.exp(-np.linspace(0, 6, n))


def add(track, sig, start, gain):
    i = int(start * SR)
    j = min(len(track), i + len(sig))
    track[i:j] += sig[: j - i] * gain


# Cada trilha: andamento, acordes (nota, oitava) e o padrão do dedilhado.
TRILHAS = {
    "manha": dict(bpm=84, chords=[[("D", 3), ("F#", 3), ("A", 3), ("C#", 4)], [("B", 2), ("D", 3), ("F#", 3), ("A", 3)],
                                   [("G", 2), ("B", 2), ("D", 3), ("F#", 3)], [("A", 2), ("C#", 3), ("E", 3), ("G", 3)]],
                  arp=[0, 2, 1, 3, 2, 1, 3, 2], perc=False),
    "tarde": dict(bpm=96, chords=[[("F", 3), ("A", 3), ("C", 4), ("E", 4)], [("D", 3), ("F", 3), ("A", 3), ("C", 4)],
                                   [("G", 2), ("A#", 2), ("D", 3), ("F", 3)], [("C", 3), ("E", 3), ("G", 3), ("B", 3)]],
                  arp=[0, 1, 2, 3, 2, 1, 2, 3], perc=True),
    "noite": dict(bpm=72, chords=[[("A", 2), ("C", 3), ("E", 3), ("G", 3)], [("F", 2), ("A", 2), ("C", 3), ("E", 3)],
                                   [("D", 3), ("F", 3), ("A", 3), ("C", 4)], [("E", 2), ("G#", 2), ("B", 2), ("D", 3)]],
                  arp=[0, 2, 3, 1, 2, 3, 1, 2], perc=False),
    "festa": dict(bpm=108, chords=[[("G", 2), ("B", 2), ("D", 3), ("F#", 3)], [("E", 2), ("G", 2), ("B", 2), ("D", 3)],
                                    [("C", 3), ("E", 3), ("G", 3), ("B", 3)], [("D", 3), ("F#", 3), ("A", 3), ("C", 4)]],
                  arp=[0, 3, 1, 2, 0, 3, 2, 1], perc=True),
}


def build(name, cfg, seconds=40):
    beat = 60 / cfg["bpm"]
    bar = beat * 4
    track = np.zeros(int(SR * (seconds + 3)))
    t, k = 0.0, 0
    while t < seconds:
        chord = cfg["chords"][k % len(cfg["chords"])]
        freqs = [hz(n, o) for n, o in chord]
        add(track, pad([f / 2 for f in freqs[:2]] + freqs[2:], bar + 0.6), t, 0.10)
        add(track, pluck(freqs[0] / 2, 1.6, 0.45, seed=k), t, 0.35)
        for s, idx in enumerate(cfg["arp"]):
            add(track, pluck(freqs[idx] * 2, 1.2, 0.55, seed=k * 10 + s), t + s * beat / 2, 0.22)
        if cfg["perc"]:
            for b in range(4):
                if b in (0, 2):
                    add(track, kick(), t + b * beat, 0.35)
                add(track, shaker(seed=b), t + b * beat + beat / 2, 0.05)
        t += bar
        k += 1
    track = track[: int(SR * seconds)]
    # Fade-in, fade-out e normalização.
    f = int(SR * 0.5)
    track[:f] *= np.linspace(0, 1, f)
    track[-int(SR * 2):] *= np.linspace(1, 0, int(SR * 2))
    track = track / np.max(np.abs(track)) * 0.8
    stereo = np.stack([track, np.roll(track, 220) * 0.96], axis=1)
    OUT.mkdir(exist_ok=True)
    wav = OUT / f"{name}.wav"
    wavfile.write(wav, SR, (stereo * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "aac", "-b:a", "160k",
                    str(OUT / f"{name}.m4a")], check=True)
    wav.unlink()


if __name__ == "__main__":
    for name, cfg in TRILHAS.items():
        build(name, cfg)
        print(OUT / f"{name}.m4a")
