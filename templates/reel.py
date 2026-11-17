"""
Casa Onze — monta o Reel a partir dos quadros 9:16.

Uso:
    python templates/render.py posts/<pasta>/pauta.json --reel
    python templates/reel.py posts/<pasta>

Gera posts/<pasta>/reel.mp4 (1080x1920, 30 fps) e reel_capa.jpg (o primeiro
quadro). Cada quadro fica ~2,6 s na tela, com transição curta.

Trilha: instrumental gerada por templates/trilhas.py (sem direitos de terceiros).
Usa o campo "trilha" do pauta.json, se houver; senão, escolhe pela editoria:
agenda -> festa, mesa -> tarde, roteiro -> manha, casa -> noite.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

FADE = 0.35
ROOT = Path(__file__).resolve().parents[1]
TRILHA_POR_EDITORIA = {"agenda": "festa", "mesa": "tarde", "roteiro": "manha", "casa": "noite"}


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
    trilha = None
    pauta = post_dir / "pauta.json"
    if pauta.is_file():
        p = json.loads(pauta.read_text(encoding="utf-8"))
        trilha = p.get("trilha") or TRILHA_POR_EDITORIA.get(p.get("editoria"))
    audio = ROOT / "audio" / f"{trilha}.m4a" if trilha else None
    if audio and audio.is_file():
        total = sum(durs) - FADE * (len(frames) - 1)
        mixed = post_dir / "reel.audio.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-i", str(audio),
                        "-filter_complex", f"[1:a]atrim=0:{total:.2f},loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={max(0, total - 1.5):.2f}:d=1.5[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
                        "-movflags", "+faststart", str(mixed)], check=True)
        tmp.unlink()
        tmp = mixed
    tmp.replace(post_dir / "reel.mp4")
    shutil.copy(frames[0], post_dir / "reel_capa.jpg")
    return post_dir / "reel.mp4"


if __name__ == "__main__":
    print(build(sys.argv[1]))
