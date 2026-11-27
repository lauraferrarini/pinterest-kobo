"""Gera o site leve (pra Kobo) a partir das fotos em site/fotos/."""
import html
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageOps

try:  # fotos HEIC (formato do iPhone)
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

RAIZ = Path(__file__).resolve().parent.parent
SITE = RAIZ / "site"
FOTOS = SITE / "fotos"

POR_PAGINA = 30                 # miniaturas por página da grade
MINI = (360, 480)               # miniatura cortada em 3:4
TELA = (1264, 1680)             # tela da Kobo Libra Colour
EXTENSOES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic", ".heif"}

CSS = """
body{margin:0;padding:10px 12px 30px;background:#fff;color:#000;font-family:sans-serif;font-size:20px}
a{color:#000}
h1{font-size:26px;margin:8px 0 12px}
.topo a,.nav a,button{display:inline-block;padding:12px 18px;margin:3px 4px 3px 0;border:2px solid #000;border-radius:8px;background:#fff;color:#000;font-size:20px;text-decoration:none}
.nav{text-align:center;margin:8px 0}
.nav span{display:inline-block;padding:12px 10px}
.pastas{font-size:0;margin:0 -5px}
.pastas a{display:inline-block;width:50%;padding:5px;box-sizing:border-box;vertical-align:top;text-decoration:none;font-size:20px}
.pastas img{width:100%;height:auto;display:block;border:2px solid #000}
.pastas b{display:block;margin-top:4px}
.pastas i{font-style:normal;font-size:16px}
.grade{font-size:0;margin:0 -4px}
.grade a{display:inline-block;width:33.33%;padding:4px;box-sizing:border-box}
.grade img{width:100%;height:auto;display:block;border:1px solid #000}
.foto{text-align:center}
.foto img{max-width:100%;max-height:82vh;height:auto}
.info{text-align:center;font-size:16px;margin:6px 0}
.vazio{padding:30px 0}
"""


def slugify(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "pasta"


def slug_unico(texto, usados):
    base = slugify(texto)
    s, n = base, 2
    while s in usados:
        s, n = f"{base}-{n}", n + 1
    usados.add(s)
    return s


def chave_ordem(stem):
    partes = stem.split("_")
    try:
        pin = int(partes[0])
    except ValueError:
        pin = 0
    return (-pin, "_".join(partes[1:]))


def pin_id(stem):
    return stem.split("_")[0]


def link(de_pagina, para, pasta=False):
    rel = os.path.relpath(para, de_pagina.parent).replace(os.sep, "/")
    rel = "/".join(quote(p) for p in rel.split("/"))
    if pasta:
        rel = rel + "/" if rel != "." else "./"
    return rel


def esc(t):
    return html.escape(str(t), quote=True)


def pagina_html(titulo, corpo):
    return (
        "<!DOCTYPE html>\n<html lang=\"pt-BR\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{esc(titulo)}</title><style>{CSS}</style></head>"
        f"<body>{corpo}</body></html>\n"
    )


def escrever(caminho, texto):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")


def abrir_rgb(origem):
    im = Image.open(origem)
    im.seek(0)
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fundo = Image.new("RGB", im.size, (255, 255, 255))
        fundo.paste(im, mask=im.split()[-1])
        return fundo
    return im.convert("RGB")


def gerar_versoes(item):
    orig = item["original"]
    precisa = [d for d in (item["mini"], item["tela"])
               if not d.exists() or d.stat().st_mtime < orig.stat().st_mtime]
    if not precisa:
        return True
    try:
        im = abrir_rgb(orig)
    except Exception as e:
        print(f"  ignorando {orig.relative_to(SITE)}: {e}")
        return False
    if item["mini"] in precisa:
        item["mini"].parent.mkdir(parents=True, exist_ok=True)
        ImageOps.fit(im, MINI, Image.LANCZOS).save(item["mini"], "JPEG", quality=72, optimize=True)
    if item["tela"] in precisa:
        item["tela"].parent.mkdir(parents=True, exist_ok=True)
        t = im.copy()
        t.thumbnail(TELA, Image.LANCZOS)
        t.save(item["tela"], "JPEG", quality=85, optimize=True)
    return True


def ler_album(dir_fotos, caminho_slug):
    itens = []
    for f in sorted(dir_fotos.iterdir()):
        if f.is_file() and f.suffix.lower() in EXTENSOES:
            itens.append({
                "stem": f.stem,
                "original": f,
                "mini": SITE / "mini" / caminho_slug / f"{f.stem}.jpg",
                "tela": SITE / "tela" / caminho_slug / f"{f.stem}.jpg",
            })
    itens.sort(key=lambda i: chave_ordem(i["stem"]))
    return itens


def ler_pastas():
    pastas = []
    if not FOTOS.exists():
        return pastas
    usados = set()
    for d in sorted(FOTOS.iterdir(), key=lambda p: p.name.lower()):
        if not d.is_dir():
            continue
        bslug = slug_unico(d.name, usados)
        secoes, usados_sec = [], set()
        for s in sorted(d.iterdir(), key=lambda p: p.name.lower()):
            if s.is_dir():
                sslug = slug_unico(s.name, usados_sec)
                itens = ler_album(s, f"{bslug}/{sslug}")
                if itens:
                    secoes.append({"nome": s.name, "slug": sslug, "itens": itens,
                                   "url": f"{bslug}/{sslug}"})
        itens = ler_album(d, bslug)
        ids_secoes = {pin_id(i["stem"]) for sec in secoes for i in sec["itens"]}
        itens = [i for i in itens if pin_id(i["stem"]) not in ids_secoes]
        if itens or secoes:
            pastas.append({"nome": d.name, "slug": bslug, "itens": itens,
                           "secoes": secoes, "url": bslug})
    return pastas


def caminho_grade(album, n):
    base = SITE / "p" / album["url"]
    return base / ("index.html" if n == 1 else f"{n}.html")


def caminho_foto(album, item):
    return SITE / "v" / album["url"] / f"{item['stem']}.html"


def link_grade(de, album, n):
    alvo = caminho_grade(album, n)
    return link(de, alvo.parent, pasta=True) if n == 1 else link(de, alvo)


def bloco_pastas(de, lista, url_de):
    partes = ['<div class="pastas">']
    for a in lista:
        capa = a["capa"]
        img = (f'<img src="{link(de, capa["mini"])}" width="{MINI[0]}" height="{MINI[1]}" alt="">'
               if capa else "")
        n = a["total"]
        partes.append(
            f'<a href="{url_de(a)}">{img}<b>{esc(a["nome"])}</b>'
            f'<i>{n} foto{"s" if n != 1 else ""}</i></a>')
    partes.append("</div>")
    return "".join(partes)


def paginar(album, titulo, topo_html, extra_primeira=None):
    itens = album["itens"]
    total_pag = max(1, -(-len(itens) // POR_PAGINA))
    for n in range(1, total_pag + 1):
        pag = caminho_grade(album, n)
        fatia = itens[(n - 1) * POR_PAGINA: n * POR_PAGINA]
        for it in fatia:
            it["pagina_grade"] = n
        nav = ""
        if total_pag > 1:
            ant = f'<a href="{link_grade(pag, album, n - 1)}">‹ Anterior</a>' if n > 1 else ""
            prox = f'<a href="{link_grade(pag, album, n + 1)}">Próxima ›</a>' if n < total_pag else ""
            nav = f'<div class="nav">{ant}<span>Página {n} de {total_pag}</span>{prox}</div>'
        grade = ['<div class="grade">']
        for it in fatia:
            grade.append(
                f'<a href="{link(pag, caminho_foto(album, it))}">'
                f'<img src="{link(pag, it["mini"])}" width="{MINI[0]}" height="{MINI[1]}" alt=""></a>')
        grade.append("</div>")
        corpo = (topo_html(pag) + f"<h1>{esc(titulo)}</h1>"
                 + (extra_primeira(pag) if n == 1 and extra_primeira else "")
                 + nav + "".join(grade) + nav)
        escrever(pag, pagina_html(titulo, corpo))


def paginas_fotos(album, titulo):
    itens = album["itens"]
    for idx, it in enumerate(itens):
        pag = caminho_foto(album, it)
        grade = link_grade(pag, album, it["pagina_grade"])
        ant = (f'<a href="{link(pag, caminho_foto(album, itens[idx - 1]))}">‹ Anterior</a>'
               if idx > 0 else "")
        prox = (f'<a href="{link(pag, caminho_foto(album, itens[idx + 1]))}">Próxima ›</a>'
                if idx < len(itens) - 1 else "")
        nav = f'<div class="nav">{ant}<a href="{grade}">Grade</a>{prox}</div>'
        orig = link(pag, it["original"])
        corpo = (
            nav
            + f'<div class="foto"><a href="{orig}"><img src="{link(pag, it["tela"])}" alt=""></a></div>'
            + f'<div class="info">{esc(titulo)} · {idx + 1} de {len(itens)}</div>'
            + f'<div class="nav"><a href="{orig}">Original (resolução máxima)</a></div>'
            + nav
        )
        escrever(pag, pagina_html(titulo, corpo))


def main():
    SITE.mkdir(exist_ok=True)
    pastas = ler_pastas()

    esperados = set()
    for p in pastas:
        for album in [p] + p["secoes"]:
            ok = [it for it in album["itens"] if gerar_versoes(it)]
            album["itens"] = ok
            for it in ok:
                esperados.update({it["mini"], it["tela"]})
    for pasta in ("mini", "tela"):
        for f in (SITE / pasta).rglob("*.jpg") if (SITE / pasta).exists() else []:
            if f not in esperados:
                f.unlink()

    for p in pastas:
        p["secoes"] = [s for s in p["secoes"] if s["itens"]]
        for s in p["secoes"]:
            s["capa"], s["total"] = s["itens"][0], len(s["itens"])
        todos = p["itens"] + [i for s in p["secoes"] for i in s["itens"]]
        p["capa"] = todos[0] if todos else None
        p["total"] = len(todos)
    pastas = [p for p in pastas if p["total"]]

    for d in ("p", "v"):
        shutil.rmtree(SITE / d, ignore_errors=True)

    inicio = SITE / "index.html"
    for p in pastas:
        def topo_pasta(pag):
            return f'<div class="topo"><a href="{link(pag, inicio.parent, pasta=True)}">‹ Pastas</a></div>'

        def secoes_html(pag, p=p):
            if not p["secoes"]:
                return ""
            return bloco_pastas(pag, p["secoes"],
                                lambda s: link(pag, caminho_grade(s, 1).parent, pasta=True))

        paginar(p, p["nome"], topo_pasta, secoes_html)
        paginas_fotos(p, p["nome"])

        for s in p["secoes"]:
            def topo_secao(pag, p=p):
                return (f'<div class="topo"><a href="{link(pag, inicio.parent, pasta=True)}">‹ Pastas</a>'
                        f'<a href="{link(pag, caminho_grade(p, 1).parent, pasta=True)}">‹ {esc(p["nome"])}</a></div>')
            titulo = f'{p["nome"]} › {s["nome"]}'
            paginar(s, titulo, topo_secao)
            paginas_fotos(s, titulo)

    ultima = RAIZ / "dados" / "ultima-atualizacao.txt"
    quando = ultima.read_text(encoding="utf-8").splitlines()[0] if ultima.exists() else ""
    lista = (bloco_pastas(inicio, pastas, lambda p: link(inicio, caminho_grade(p, 1).parent, pasta=True))
             if pastas else '<p class="vazio">Nenhuma pasta ainda. Rode a atualização.</p>')
    corpo = (
        "<h1>Minhas pastas</h1>" + lista
        + '<form method="post" action="atualizar" class="nav">'
          '<button type="submit">Buscar pins novos</button></form>'
        + (f'<p class="info">Última atualização: {esc(quando)}</p>' if quando else "")
    )
    escrever(inicio, pagina_html("Minhas pastas", corpo))

    total = sum(p["total"] for p in pastas)
    print(f"Site gerado: {len(pastas)} pasta(s), {total} foto(s).")


if __name__ == "__main__":
    sys.exit(main())
