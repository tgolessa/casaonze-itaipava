"""
Casa Onze — Reel com fotos da casa em movimento (zoom lento e cortes rápidos).

Uso:
    python templates/reel_fotos.py posts/<pasta>

Lê posts/<pasta>/cenas.json:
{
  "gancho": "Texto fixo no topo durante o vídeo todo (opcional)",
  "cenas": [
    {"foto": "fotos/8baedc19.jpg", "dur": 1.2, "texto": "Texto da cena (opcional)", "zoom": "in"},
    ...
  ]
}
"zoom": "in" (aproxima) ou "out" (afasta). "pos" do texto: "meio" (padrão) ou "baixo".

Gera posts/<pasta>/reel.mp4 (1080x1920, 30 fps, sem áudio) e reel_capa.jpg.
Reel de teste vai sem som: a música entra pelo app, na hora de publicar.
Quando o post.json não for de teste, a trilha própria é aplicada pelo reel.py
(use reel.adicionar_trilha).
"""
import json
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H, FPS = 1080, 1920, 30
FADE = 0.12
TPL = Path(__file__).resolve().parent
ROOT = TPL.parent


def fonte(tam):
    f = ImageFont.truetype(str(TPL / "fonts" / "Fraunces.ttf"), tam)
    try:
        f.set_variation_by_axes([144, 600, 0, 0])  # opsz, wght, SOFT, WONK
    except Exception:  # noqa: BLE001
        pass
    return f


def carregar(rel):
    im = ImageOps.exif_transpose(Image.open(ROOT / rel)).convert("RGB")
    iw, ih = im.size
    if iw / ih > 9 / 16:
        nw = int(ih * 9 / 16)
        x = (iw - nw) // 2
        im = im.crop((x, 0, x + nw, ih))
    else:
        nh = int(iw * 16 / 9)
        y = (ih - nh) // 2
        im = im.crop((0, y, iw, y + nh))
    return im.resize((int(W * 1.18), int(H * 1.18)), Image.LANCZOS)


def caixa(texto, tam, y, largura=18):
    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not texto:
        return camada
    d = ImageDraw.Draw(camada)
    f = fonte(tam)
    linhas = sum([textwrap.wrap(p, largura) or [""] for p in texto.split("\n")], [])
    lh = int(tam * 1.18)
    mw = max(d.textlength(l, font=f) for l in linhas)
    d.rounded_rectangle(((W - mw) / 2 - 46, y - 34, (W + mw) / 2 + 46, y + lh * len(linhas) + 16),
                        radius=30, fill=(28, 26, 22, 175))
    for i, l in enumerate(linhas):
        d.text(((W - d.textlength(l, font=f)) / 2, y + i * lh), l, font=f, fill=(246, 240, 230))
    return camada


def quadro(cena, t):
    p = t / cena["dur"]
    z = 1.0 + 0.16 * p if cena.get("zoom", "in") == "in" else 1.16 - 0.16 * p
    im = cena["_im"]
    iw, ih = im.size
    cw, ch = iw / z, ih / z
    x, y = (iw - cw) / 2, (ih - ch) / 2
    return im.resize((W, H), Image.BILINEAR, box=(x, y, x + cw, y + ch))


def build(post_dir):
    post_dir = Path(post_dir)
    spec = json.loads((post_dir / "cenas.json").read_text(encoding="utf-8"))
    cenas = spec["cenas"]
    for c in cenas:
        c["_im"] = carregar(c["foto"])
        y = 1180 if c.get("pos") == "baixo" else 860
        c["_tl"] = caixa(c.get("texto"), c.get("tam", 92), y)
    gancho = caixa(spec.get("gancho"), spec.get("tam_gancho", 74), 300, 22) if spec.get("gancho") else None

    inicios, s = [], 0.0
    for c in cenas:
        inicios.append(s)
        s += c["dur"] - FADE
    total = s + FADE

    tmp = post_dir / "reel.part.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                           "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(tmp)],
                          stdin=subprocess.PIPE)
    capa = None
    for i in range(int(total * FPS)):
        t = i / FPS
        fr = None
        for c, s0 in zip(cenas, inicios):
            lt = t - s0
            if lt < 0 or lt > c["dur"]:
                continue
            f = quadro(c, lt)
            if lt > FADE:  # o texto da cena só entra depois da transição
                f = Image.alpha_composite(f.convert("RGBA"), c["_tl"]).convert("RGB")
            fr = f if fr is None else Image.blend(fr, f, min(1, lt / FADE))
        if gancho is not None:
            fr = Image.alpha_composite(fr.convert("RGBA"), gancho).convert("RGB")
        if i == 6:
            capa = fr.copy()
        ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit("ffmpeg falhou")
    tmp.replace(post_dir / "reel.mp4")
    capa.save(post_dir / "reel_capa.jpg", quality=92)
    return post_dir / "reel.mp4"


if __name__ == "__main__":
    print(build(sys.argv[1]))
