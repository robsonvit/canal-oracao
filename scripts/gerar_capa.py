"""
gerar_capa.py
─────────────
Gera a thumbnail do vídeo (1280×720) no estilo do canal Bispo Bruno Leonardo:
  • Lado esquerdo: foto escura de mãos em oração / bíblia (baixada do Pexels)
  • Lado direito: fundo preto com texto hierárquico em branco e dourado
  • Número do salmo em gigante dourado/laranja
  • Linha dourada divisória
"""

import os
import io
import json
import random
import requests

from PIL import Image, ImageDraw, ImageFont, ImageFilter


PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
LARGURA, ALTURA = 1280, 720

# Paleta de cores
BRANCO       = (255, 255, 255)
DOURADO      = (212, 175, 55)
LARANJA_OURO = (255, 190, 40)
PRETO        = (0,   0,   0)
PRETO_RICO   = (8,   6,   4)
CINZA_SUAVE  = (200, 200, 200)


# ─────────────────────────────────────────────────────────────────────────────
# Download de imagem de fundo
# ─────────────────────────────────────────────────────────────────────────────
def _baixar_foto_oracao() -> Image.Image:
    """Tenta baixar foto de mãos em oração com bíblia do Pexels."""
    headers = {"Authorization": PEXELS_API_KEY}
    termos  = [
        "praying hands bible open",
        "bible prayer hands dark",
        "open bible candle",
        "hands prayer worship",
    ]
    for termo in termos:
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params={"query": termo, "orientation": "landscape", "per_page": 8},
                timeout=20,
            )
            fotos = resp.json().get("photos", [])
            if fotos:
                foto  = random.choice(fotos)
                dados = requests.get(foto["src"]["large"], timeout=30).content
                return Image.open(io.BytesIO(dados)).convert("RGB")
        except Exception:
            continue

    # Fallback: fundo gradiente escuro
    img = Image.new("RGB", (LARGURA, ALTURA), (15, 10, 5))
    return img


# ─────────────────────────────────────────────────────────────────────────────
# Carregamento de fontes
# ─────────────────────────────────────────────────────────────────────────────
def _fonte(tamanho: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Tenta várias fontes serif disponíveis no sistema Ubuntu/Windows."""
    caminhos = []
    if bold:
        caminhos = [
            "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "C:/Windows/Fonts/georgiab.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    else:
        caminhos = [
            "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
            "C:/Windows/Fonts/georgia.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    for caminho in caminhos:
        try:
            return ImageFont.truetype(caminho, tamanho)
        except Exception:
            continue
    return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────────────────────
# Função principal
# ─────────────────────────────────────────────────────────────────────────────
def gerar_thumbnail(salmo: str, tema: str, titulo: str, output_dir: str = "output") -> str:
    """
    Gera thumbnail 1280×720 e salva em output/thumbnail.jpg.
    Retorna o caminho do arquivo.
    """
    os.makedirs(output_dir, exist_ok=True)

    # ── 1. Baixar foto de fundo ──────────────────────────────────────────────
    foto = _baixar_foto_oracao()
    foto = foto.resize((LARGURA, ALTURA), Image.LANCZOS)

    # ── 2. Canvas base ───────────────────────────────────────────────────────
    canvas = Image.new("RGB", (LARGURA, ALTURA), PRETO_RICO)

    # ── 3. Lado esquerdo: foto com overlay escuro ────────────────────────────
    metade_esq = foto.crop((0, 0, 640, ALTURA))

    # Camada de escurecimento
    overlay = Image.new("RGBA", (640, ALTURA), (0, 0, 0, 175))
    metade_rgba = metade_esq.convert("RGBA")
    metade_rgba.paste(overlay, (0, 0), overlay)

    # Gradiente horizontal (fade para o lado direito)
    fade = Image.new("RGBA", (200, ALTURA), (0, 0, 0, 0))
    for x in range(200):
        alpha = int((x / 200) * 220)
        for y in range(ALTURA):
            fade.putpixel((x, y), (0, 0, 0, alpha))
    metade_rgba.paste(fade, (440, 0), fade)

    canvas.paste(metade_rgba.convert("RGB"), (0, 0))

    # ── 4. Lado direito: fundo preto sólido ─────────────────────────────────
    lado_dir = Image.new("RGB", (640, ALTURA), PRETO_RICO)
    canvas.paste(lado_dir, (640, 0))

    # ── 5. Linha divisória dourada ───────────────────────────────────────────
    draw = ImageDraw.Draw(canvas)
    draw.line([(636, 30), (636, ALTURA - 30)], fill=DOURADO, width=3)

    # ── 6. Textos no lado direito ────────────────────────────────────────────
    x0          = 660    # margem esquerda do texto
    max_largura = 590    # largura máxima para textos

    def centralizar_x(texto, font):
        """Retorna x para centralizar na área direita."""
        bbox = draw.textbbox((0, 0), texto, font=font)
        w    = bbox[2] - bbox[0]
        return x0 + (max_largura - w) // 2

    # "PODEROSA ORAÇÃO" — pequeno, branco, topo
    f_sub  = _fonte(30, bold=True)
    y = 55
    tx_sub = "PODEROSA ORAÇÃO"
    draw.text((centralizar_x(tx_sub, f_sub), y), tx_sub, fill=BRANCO, font=f_sub)

    # "DO SALMO" — grande, branco
    f_salmo = _fonte(68, bold=True)
    y += 50
    tx_salmo = "DO SALMO"
    draw.text((centralizar_x(tx_salmo, f_salmo), y), tx_salmo, fill=BRANCO, font=f_salmo)

    # Número do salmo — gigante, dourado/laranja
    f_num = _fonte(200, bold=True)
    y += 75
    tx_num = salmo
    # Sombra
    draw.text((centralizar_x(tx_num, f_num) + 3, y + 3), tx_num, fill=(80, 60, 0), font=f_num)
    # Texto principal
    draw.text((centralizar_x(tx_num, f_num), y), tx_num, fill=LARANJA_OURO, font=f_num)

    # Linha dourada abaixo do número
    y_sep = y + 205
    draw.line([(x0, y_sep), (x0 + max_largura, y_sep)], fill=DOURADO, width=2)

    # Tema do salmo — quebrado em linhas, branco bold
    f_tema = _fonte(42, bold=True)
    y = y_sep + 20
    palavras  = tema.upper().split()
    linhas    = []
    linha_tmp = ""
    for palavra in palavras:
        teste = (linha_tmp + " " + palavra).strip()
        bbox  = draw.textbbox((0, 0), teste, font=f_tema)
        if bbox[2] - bbox[0] > max_largura and linha_tmp:
            linhas.append(linha_tmp)
            linha_tmp = palavra
        else:
            linha_tmp = teste
    if linha_tmp:
        linhas.append(linha_tmp)

    for linha in linhas[:3]:
        draw.text((centralizar_x(linha, f_tema), y), linha, fill=BRANCO, font=f_tema)
        y += 50

    # "CANAL ORAÇÃO" — rodapé dourado
    f_rodape = _fonte(26, bold=False)
    tx_rod   = "CANAL ORAÇÃO"
    draw.text(
        (centralizar_x(tx_rod, f_rodape), ALTURA - 50),
        tx_rod, fill=DOURADO, font=f_rodape
    )

    # ── 7. Salvar ─────────────────────────────────────────────────────────────
    output_path = os.path.join(output_dir, "thumbnail.jpg")
    canvas.save(output_path, "JPEG", quality=95)
    print(f"✅ Thumbnail gerada: {output_path}")
    return output_path


if __name__ == "__main__":
    with open("output/oracao.json", encoding="utf-8") as f:
        data = json.load(f)
    gerar_thumbnail(data["salmo"], data["tema"], data["titulo"])
