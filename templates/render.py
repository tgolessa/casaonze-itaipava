"""
Casa Onze — renderizador de carrosséis.

Uso:
    python templates/render.py posts/<pasta>/pauta.json

Lê o pauta.json, monta os slides em HTML com a identidade da Casa Onze
e salva um JPEG 1080x1350 por slide em posts/<pasta>/imagens/.

Editorias (cor de destaque):
  agenda  -> ferrugem   (shows, festivais, feiras, eventos)
  mesa    -> madeira    (restaurantes, bares, cervejarias, cafés)
  roteiro -> turquesa   (passeios, trilhas, pontos turísticos, compras)
  casa    -> musgo      (posts com as fotos da Casa Onze)

Tipos de slide (campo "tipo" de cada item em "slides"):
  capa    -> {"titulo", "subtitulo", "chapeu"}
  texto   -> {"titulo", "texto"}
  lista   -> {"titulo", "itens": ["...", ...]}
  servico -> {"titulo", "linhas": [["Quando", "..."], ["Onde", "..."], ...]}
  casa    -> {"foto": "fotos/<arquivo>.jpg", "titulo", "texto"}
"""
import base64
import html
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
TPL = Path(__file__).resolve().parent

CORES = {
    "agenda": "#9A4A2E",
    "mesa": "#B0703A",
    "roteiro": "#2F8A86",
    "casa": "#4C5240",
}
NOMES = {"agenda": "Agenda", "mesa": "Mesa", "roteiro": "Roteiro", "casa": "Casa Onze"}


def e(t):
    return html.escape(str(t or "")).replace("\n", "<br>")


def font_face():
    out = []
    for fam, f, style in [("Fraunces", "Fraunces.ttf", "normal"),
                          ("Fraunces", "Fraunces-Italic.ttf", "italic"),
                          ("Manrope", "Manrope.ttf", "normal")]:
        b64 = base64.b64encode((TPL / "fonts" / f).read_bytes()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:100 900;"
                   f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}")
    return "\n".join(out)


CSS = """
:root{--creme:#F4EEE4;--tinta:#22201B;--musgo:#4C5240;--cor:__COR__;}
*{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;height:1350px;background:var(--creme);}
.slide{position:relative;width:1080px;height:1350px;overflow:hidden;background:var(--creme);color:var(--tinta);
  font-family:'Manrope',sans-serif;padding:96px 96px 0 96px;display:flex;flex-direction:column}
.topo{display:flex;justify-content:space-between;align-items:center;font-size:26px;letter-spacing:.18em;
  text-transform:uppercase;font-weight:700}
.tag{color:var(--cor)}
.tag::before{content:'';display:inline-block;width:14px;height:14px;border-radius:50%;background:var(--cor);
  margin-right:16px;vertical-align:2px}
.cont{color:#8b857a}
.rodape{position:absolute;left:96px;right:96px;bottom:72px;display:flex;justify-content:space-between;align-items:center;
  font-size:24px;letter-spacing:.2em;text-transform:uppercase;font-weight:700;color:#8b857a;
  border-top:2px solid #d9d0c2;padding-top:28px}
.selo{font-family:'Fraunces',serif;font-size:44px;letter-spacing:0;color:var(--cor);font-weight:600}
h1,h2{font-family:'Fraunces',serif;font-weight:500;letter-spacing:-.01em;line-height:1.02}
.capa{background:var(--musgo);color:var(--creme)}
.capa .cont,.capa .rodape{color:#c9c5b4;border-color:#6b705c}
.capa .tag{color:#E8B48F}.capa .tag::before{background:#E8B48F}
.capa .selo{color:#E8B48F}
.capa .meio{flex:1;display:flex;flex-direction:column;justify-content:center;padding-bottom:140px}
.chapeu{font-family:'Fraunces',serif;font-style:italic;font-size:46px;color:#E8B48F;margin-bottom:36px}
.capa h1{font-size:132px}
.capa .sub{margin-top:48px;font-size:40px;line-height:1.35;color:#e6e1d2;max-width:820px}
.corpo{flex:1;display:flex;flex-direction:column;justify-content:center;padding-bottom:160px}
h2{font-size:84px;margin-bottom:56px}
h2 em{font-style:italic;color:var(--cor)}
.texto{font-size:42px;line-height:1.45;max-width:860px}
ul.lista{list-style:none}
ul.lista li{font-size:40px;line-height:1.3;padding:22px 0;border-bottom:2px solid #e2d9cb;display:flex;gap:28px}
ul.lista li span{font-family:'Fraunces',serif;color:var(--cor);font-weight:600;min-width:64px}
.serv{display:grid;grid-template-columns:230px 1fr;row-gap:34px;column-gap:24px}
.serv dt{font-size:26px;letter-spacing:.16em;text-transform:uppercase;font-weight:800;color:var(--cor);padding-top:10px}
.serv dd{font-size:40px;line-height:1.35}
.casa{padding:0;color:var(--creme)}
.casa img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.casa .veu{position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,18,14,.25) 0%,rgba(20,18,14,0) 30%,rgba(20,18,14,.35) 55%,rgba(20,18,14,.92) 100%)}
.casa .topo{position:relative;padding:96px 96px 0}
.casa .tag,.casa .cont{color:#fff}.casa .tag::before{background:#fff}
.casa .baixo{position:absolute;left:96px;right:96px;bottom:190px}
.casa h2{font-size:84px;margin-bottom:28px;color:#fff;max-width:820px}
.casa .texto{color:#f1ece2}
.casa .rodape{color:#e9e2d4;border-color:rgba(255,255,255,.35)}
.casa .selo{color:#fff}
"""


def moldura(classe, editoria, i, n, miolo):
    return (f'<div class="slide {classe}"><div class="topo"><div class="tag">{e(NOMES[editoria])}</div>'
            f'<div class="cont">{i:02d}/{n:02d}</div></div>{miolo}'
            f'<div class="rodape"><div>Casa Onze · Itaipava</div><div class="selo">11</div></div></div>')


def slide_html(s, editoria, i, n):
    t = s["tipo"]
    if t == "capa":
        return moldura("capa", editoria, i, n,
                       f'<div class="meio"><div class="chapeu">{e(s.get("chapeu"))}</div>'
                       f'<h1>{e(s["titulo"])}</h1><div class="sub">{e(s.get("subtitulo"))}</div></div>')
    if t == "texto":
        return moldura("", editoria, i, n,
                       f'<div class="corpo"><h2>{s["titulo"]}</h2><div class="texto">{e(s["texto"])}</div></div>')
    if t == "lista":
        lis = "".join(f'<li><span>{k:02d}</span><div>{e(x)}</div></li>' for k, x in enumerate(s["itens"], 1))
        return moldura("", editoria, i, n, f'<div class="corpo"><h2>{s["titulo"]}</h2><ul class="lista">{lis}</ul></div>')
    if t == "servico":
        dl = "".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in s["linhas"])
        return moldura("", editoria, i, n, f'<div class="corpo"><h2>{s["titulo"]}</h2><dl class="serv">{dl}</dl></div>')
    if t == "casa":
        foto = (ROOT / s["foto"]).resolve()
        b64 = base64.b64encode(foto.read_bytes()).decode()
        return (f'<div class="slide casa"><img src="data:image/jpeg;base64,{b64}"><div class="veu"></div>'
                f'<div class="topo"><div class="tag">Casa Onze</div><div class="cont">{i:02d}/{n:02d}</div></div>'
                f'<div class="baixo"><h2>{e(s["titulo"])}</h2><div class="texto">{e(s.get("texto"))}</div></div>'
                f'<div class="rodape"><div>Reservas no link da bio</div><div class="selo">11</div></div></div>')
    raise ValueError(f"tipo de slide desconhecido: {t}")


def render(pauta_path):
    pauta_path = Path(pauta_path).resolve()
    p = json.loads(pauta_path.read_text(encoding="utf-8"))
    editoria = p["editoria"]
    css = font_face() + CSS.replace("__COR__", CORES[editoria])
    out = pauta_path.parent / "imagens"
    out.mkdir(exist_ok=True)
    n = len(p["slides"])
    paths = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for i, s in enumerate(p["slides"], 1):
            pg.set_content(f"<html><head><meta charset='utf-8'><style>{css}</style></head>"
                           f"<body>{slide_html(s, editoria, i, n)}</body></html>")
            pg.evaluate("document.fonts.ready")
            dest = out / f"{i:02d}.jpg"
            pg.screenshot(path=str(dest), type="jpeg", quality=92)
            paths.append(dest)
        b.close()
    return paths


if __name__ == "__main__":
    for path in render(sys.argv[1]):
        print(path)
