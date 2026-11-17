"""
Casa Onze — monta o Reel a partir dos quadros 9:16.

Uso:
    python templates/render.py posts/<pasta>/pauta.json --reel
    python templates/reel.py posts/<pasta>

Gera posts/<pasta>/reel.mp4 (1080x1920, 30 fps, sem áudio) e reel_capa.jpg
(o primeiro quadro). Cada quadro fica ~2,6 s na tela, com transição curta.
"""
import shutil
import subprocess
import sys
from pathlib import Path

FADE = 0.35


def build(post_dir):
    post_dir = Path(post_dir)
    frames = sorted((post_dir / "imagens_reel").glob("*.jpg"))
    if not frames:
        sys.exit("Sem quadros em imagens_reel/. Rode render.py com --reel antes.")
    durs = [2.8] + [2.6] * (len(frames) - 2) + [3.4] if len(frames) > 1 else [4.0]
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for f, d in zip(frames, durs):
        args += ["-loop", "1", "-framerate", "30", "-t", f"{d}", "-i", str(f)]
    chains, last, offset = [], "[0:v]", 0.0
    for i in range(1, len(frames)):
        offset += durs[i - 1] - FADE
        out = f"[v{i}]"
        chains.append(f"{last}[{i}:v]xfade=transition=fade:duration={FADE}:offset={offset:.2f}{out}")
        last = out
    fc = ";".join(chains) + (";" if chains else "") + f"{last}format=yuv420p[out]"
    tmp = post_dir / "reel.part.mp4"
    args += ["-filter_complex", fc, "-map", "[out]", "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "20", "-movflags", "+faststart", str(tmp)]
    subprocess.run(args, check=True)
    tmp.replace(post_dir / "reel.mp4")
    shutil.copy(frames[0], post_dir / "reel_capa.jpg")
    return post_dir / "reel.mp4"


if __name__ == "__main__":
    print(build(sys.argv[1]))
