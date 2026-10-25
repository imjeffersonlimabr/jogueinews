"""Gera as artes do Joguei News (1080x1350) nos dois modelos da marca.

Uso:
    python3 render.py posts/AAAA-MM-DD/pauta.json

O JSON é uma lista de posts:
[
  {
    "saida": "posts/2026-10-26/01.png",
    "modelo": "foto",              # "foto" = foto cheia + manchete em caixa-alta + barra rosa
    "titulo": "Manchete do post",
    "fotos": ["fotos/a.jpg"],      # 1 foto para "foto", 2 fotos para "duplo"
    "foco": [[0.5, 0.4]]           # opcional: ponto de interesse (x, y de 0 a 1) de cada foto
  },
  {
    "saida": "posts/2026-10-26/02.png",
    "modelo": "duplo",             # "duplo" = cabeçalho @jogueinews + duas fotos lado a lado
    "titulo": "Manchete do post",
    "fotos": ["fotos/esq.jpg", "fotos/dir.jpg"]
  }
]
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(BASE, "assets")
W, H = 1080, 1350


def fonte(nome, tamanho):
    return ImageFont.truetype(os.path.join(A, "fonts", nome), tamanho)


def asset(nome):
    return Image.open(os.path.join(A, nome)).convert("RGBA")


def cobrir(caminho, w, h, foco=(0.5, 0.5)):
    """Redimensiona e recorta a foto para preencher w x h (como CSS background-size: cover)."""
    img = Image.open(caminho).convert("RGB")
    escala = max(w / img.width, h / img.height)
    nw, nh = round(img.width * escala), round(img.height * escala)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = min(max(round(foco[0] * nw - w / 2), 0), nw - w)
    y = min(max(round(foco[1] * nh - h / 2), 0), nh - h)
    return img.crop((x, y, x + w, y + h))


def quebrar(texto, f, largura):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if f.getlength(teste) <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def ajustar(texto, nome_fonte, tamanho, largura, max_linhas):
    while True:
        f = fonte(nome_fonte, tamanho)
        linhas = quebrar(texto, f, largura)
        if len(linhas) <= max_linhas or tamanho <= 26:
            return f, linhas
        tamanho -= 2


def modelo_foto(post):
    foco = (post.get("foco") or [[0.5, 0.5]])[0]
    img = cobrir(post["fotos"][0], W, H, foco).convert("RGBA")

    # escurecimento: leve no topo, forte embaixo
    sombra = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(sombra)
    for y in range(H):
        t = y / H
        if t < 0.40:
            a = 0.30
        elif t < 0.70:
            a = 0.30 + (t - 0.40) / 0.30 * 0.50
        else:
            a = 0.80 + (t - 0.70) / 0.30 * 0.13
        d.line([(0, y), (W, y)], fill=(16, 16, 20, round(a * 255)))
    img = Image.alpha_composite(img, sombra)

    img.alpha_composite(asset("logo_grande.png"), (424, 746))

    f, linhas = ajustar(post["titulo"].upper(), "Poppins-SemiBold.ttf", 40, 790, 3)
    lh = round(f.size * 1.52)
    d = ImageDraw.Draw(img)
    base = 1185
    topo = base - lh * len(linhas)
    for i, linha in enumerate(linhas):
        d.text((W / 2, topo + i * lh + lh / 2), linha, font=f, fill="white", anchor="mm")

    img.alpha_composite(asset("barra_rosa.png"), (0, 1278))
    return img.convert("RGB")


def modelo_duplo(post):
    img = Image.new("RGBA", (W, H), "white")
    focos = post.get("foco") or [[0.5, 0.5], [0.5, 0.5]]
    esq = cobrir(post["fotos"][0], 535, 975, focos[0])
    dir_ = cobrir(post["fotos"][1], 540, 975, focos[1] if len(focos) > 1 else (0.5, 0.5))
    img.paste(esq, (0, 375))
    img.paste(dir_, (540, 375))

    img.alpha_composite(asset("logo_cabecalho.png"), (70, 100))
    img.alpha_composite(asset("handle_selo.png"), (220, 105))

    f, linhas = ajustar(post["titulo"], "Poppins-Light.ttf", 42, 800, 3)
    lh = round(f.size * 1.38)
    d = ImageDraw.Draw(img)
    for i, linha in enumerate(linhas):
        d.text((225, 162 + i * lh + lh / 2), linha, font=f, fill=(37, 37, 63), anchor="lm")

    img.alpha_composite(asset("logo_grande.png"), (424, 724))
    return img.convert("RGB")


def main(pauta):
    posts = json.load(open(pauta, encoding="utf-8"))
    for post in posts:
        img = modelo_foto(post) if post["modelo"] == "foto" else modelo_duplo(post)
        os.makedirs(os.path.dirname(post["saida"]) or ".", exist_ok=True)
        img.save(post["saida"], "PNG", optimize=True)
        print("ok", post["saida"])


if __name__ == "__main__":
    main(sys.argv[1])
