"""
gerar_capa.py
─────────────
Gera a thumbnail do vídeo (1280×720) no estilo moderno de canais de orações:
  • Imagem de fundo completa: Busca via icrawler (Google como padrão, Bing como fallback, Pexels como fallback secundário)
  • Tema: Jesus Cristo (pintura, ilustração ou arte digital de alta definição)
  • Fusão degradê horizontal suave para o lado esquerdo (onde fica o texto)
  • Textos grandes e chamativos em fonte Sans-serif pesada (Arial Black/Impact) com contorno preto (stroke)
  • Ícone estilizado de relógio desenhado sob demanda caso mencione tempo
"""

import os
import io
import json
import random
import shutil
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from icrawler.builtin import GoogleImageCrawler, BingImageCrawler

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
LARGURA, ALTURA = 1280, 720

# Paleta de cores
BRANCO       = (255, 255, 255)
DOURADO      = (255, 215, 0)
AMARELO      = (255, 235, 59)
PRETO        = (0, 0, 0)
PRETO_RICO   = (8, 6, 4)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Download de imagem de fundo com icrawler (Google / Bing / Pexels)
# ─────────────────────────────────────────────────────────────────────────────
def _buscar_imagem_jesus(tema: str, titulo: str, output_dir: str) -> Image.Image:
    """Busca imagem artística de Jesus usando icrawler (Google/Bing) ou Pexels como fallback."""
    tema_lower = tema.lower() if tema else ""
    titulo_lower = titulo.lower() if titulo else ""
    
    # Define query em inglês para melhores resultados artísticos
    query = "jesus praying digital art HD"
    if "noite" in tema_lower or "dormir" in tema_lower or "noite" in titulo_lower or "dormir" in titulo_lower:
        query = "jesus praying night digital art"
    elif "manhã" in tema_lower or "dia" in tema_lower or "manhã" in titulo_lower or "dia" in titulo_lower:
        query = "jesus praying morning sunrise digital art"
    elif "espinhos" in tema_lower or "coroa" in tema_lower or "espinhos" in titulo_lower or "coroa" in titulo_lower:
        query = "jesus crown of thorns painting digital art"

    temp_dir = os.path.join(output_dir, "temp_icrawler")
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
    os.makedirs(temp_dir, exist_ok=True)

    print(f"[BUSCA] Buscando imagem para a thumbnail com query: '{query}'...")

    # 1. Tenta GoogleImageCrawler
    try:
        google_crawler = GoogleImageCrawler(downloader_threads=4, storage={'root_dir': temp_dir})
        # Desativa logs detalhados do icrawler
        google_crawler.logger.setLevel(50)
        google_crawler.crawl(keyword=query, max_num=1, min_size=(800, 600))
    except Exception as e:
        print(f"[AVISO] GoogleImageCrawler falhou: {e}")

    # 2. Se falhar, tenta BingImageCrawler
    arquivos = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
    if not arquivos:
        print("[AVISO] Nenhuma imagem retornada do Google. Tentando BingImageCrawler...")
        try:
            bing_crawler = BingImageCrawler(downloader_threads=4, storage={'root_dir': temp_dir})
            bing_crawler.logger.setLevel(50)
            bing_crawler.crawl(keyword=query, max_num=1, min_size=(800, 600))
        except Exception as e:
            print(f"[AVISO] BingImageCrawler falhou: {e}")

    # Abre a imagem baixada
    arquivos = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
    if arquivos:
        caminho_imagem = os.path.join(temp_dir, arquivos[0])
        try:
            img = Image.open(caminho_imagem).convert("RGB")
            # Remove temporários
            shutil.rmtree(temp_dir)
            print("[OK] Imagem de Jesus obtida com sucesso via crawler!")
            return img
        except Exception as e:
            print(f"[AVISO] Erro ao carregar imagem baixada: {e}")

    # 3. Fallback para Pexels
    print("[AVISO] Fallback para Pexels API...")
    headers = {"Authorization": PEXELS_API_KEY}
    termos_pexels = ["praying hands bible", "open bible candle", "hands prayer worship"]
    for termo in termos_pexels:
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params={"query": termo, "orientation": "landscape", "per_page": 5},
                timeout=15,
            )
            fotos = resp.json().get("photos", [])
            if fotos:
                foto = random.choice(fotos)
                dados = requests.get(foto["src"]["large"], timeout=20).content
                return Image.open(io.BytesIO(dados)).convert("RGB")
        except Exception as e:
            print(f"[AVISO] Erro no fallback Pexels para '{termo}': {e}")
            continue

    # Fallback absoluto: Imagem de gradiente escuro
    print("[AVISO] Usando fallback absoluto de gradiente...")
    img = Image.new("RGB", (LARGURA, ALTURA), (18, 12, 8))
    draw = ImageDraw.Draw(img)
    for y in range(ALTURA):
        r = int(18 + (y / ALTURA) * 15)
        g = int(12 + (y / ALTURA) * 10)
        b = int(8 + (y / ALTURA) * 8)
        draw.line([(0, y), (LARGURA, y)], fill=(r, g, b))
    return img


# ─────────────────────────────────────────────────────────────────────────────
# 2. Carregamento de fontes pesadas
# ─────────────────────────────────────────────────────────────────────────────
def _fonte(tamanho: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Retorna uma fonte Sans-Serif pesada para impacto visual."""
    caminhos = []
    if bold:
        caminhos = [
            "C:/Windows/Fonts/ariblk.ttf",   # Arial Black (Melhor para thumbs do Windows)
            "C:/Windows/Fonts/impact.ttf",   # Impact
            "C:/Windows/Fonts/arialbd.ttf",  # Arial Bold
            "C:/Windows/Fonts/trebucbd.ttf", # Trebuchet Bold
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        caminhos = [
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for caminho in caminhos:
        if os.path.exists(caminho):
            try:
                return ImageFont.truetype(caminho, tamanho)
            except Exception:
                continue
    try:
        # Fallback para fonte padrão se nada for encontrado
        return ImageFont.load_default()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# 3. Funções de desenho auxiliares
# ─────────────────────────────────────────────────────────────────────────────
def _desenhar_relogio(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int):
    """Desenha um relógio analógico estilizado (semelhante ao emoji ⏰)."""
    # Corpo do relógio (Amarelo brilhante)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=AMARELO, outline=PRETO, width=4)
    # Detalhes das orelhinhas (sinos) do despertador
    draw.pieslice([cx - r, cy - r, cx - int(r*0.5), cy - int(r*0.5)], start=180, end=270, fill=PRETO)
    draw.pieslice([cx + int(r*0.5), cy - r, cx + r, cy - int(r*0.5)], start=270, end=360, fill=PRETO)
    # Ponteiros do relógio (Preto)
    draw.line([cx, cy, cx, cy - r + 12], fill=PRETO, width=4) # ponteiro longo
    draw.line([cx, cy, cx + r - 15, cy], fill=PRETO, width=4) # ponteiro curto
    # Centro
    draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=PRETO)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Função Principal de Geração de Capa
# ─────────────────────────────────────────────────────────────────────────────
def gerar_thumbnail(salmo: str, tema: str, titulo: str, output_dir: str = "output") -> str:
    """Gera uma thumbnail de alta definição estilo canal de oração."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Buscar e preparar imagem de fundo
    foto = _buscar_imagem_jesus(tema, titulo, output_dir)
    
    # Corta e redimensiona para preencher 1280x720, priorizando o centro/direita
    w, h = foto.size
    proporcao_alvo = LARGURA / ALTURA
    proporcao_foto = w / h

    if proporcao_foto > proporcao_alvo:
        # Foto é mais larga: recortar as laterais
        nova_largura = int(h * proporcao_alvo)
        offset = (w - nova_largura) // 2
        # Tenta deslocar ligeiramente para a direita para posicionar o foco de Jesus à direita
        offset_dir = int(offset * 1.3)
        if offset_dir + nova_largura <= w:
            offset = offset_dir
        foto = foto.crop((offset, 0, offset + nova_largura, h))
    else:
        # Foto é mais alta: recortar topo/rodapé
        nova_altura = int(w / proporcao_alvo)
        offset = (h - nova_altura) // 2
        foto = foto.crop((0, offset, w, offset + nova_altura))

    foto = foto.resize((LARGURA, ALTURA), Image.LANCZOS)

    # 2. Aplicar degradê escuro no lado esquerdo (onde ficará o texto)
    overlay = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # Criar um gradiente horizontal bem forte
    for x in range(LARGURA):
        if x < 850:
            # Opacidade decai de 250 (esquerda) a 0 (perto do x=850)
            alpha = int(255 * (1.0 - (x / 850) ** 1.3))
            alpha = max(0, min(255, alpha))
        else:
            alpha = 0
        draw_overlay.line([(x, 0), (x, ALTURA)], fill=(0, 0, 0, alpha))

    # Combinar a foto de fundo com o degradê escuro
    canvas = Image.new("RGBA", (LARGURA, ALTURA))
    canvas.paste(foto, (0, 0))
    canvas = Image.alpha_composite(canvas, overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # 3. Processar textos chamativos e curtos
    tema_upper = tema.upper().strip() if tema else ""
    titulo_upper = titulo.upper().strip() if titulo else ""

    linhas = []
    relogio = False

    # Detecção inteligente do tema para textos chamativos
    if "NOITE" in tema_upper or "NOITE" in titulo_upper or "DORMIR" in tema_upper or "DORMIR" in titulo_upper:
        linhas = ["ORAÇÃO", "DA NOITE"]
        if "5 MIN" in tema_upper or "5 MIN" in titulo_upper or "5MIN" in tema_upper or "5MIN" in titulo_upper:
            linhas.append("SÓ 5 MINUTOS")
            relogio = True
        else:
            linhas.append("PODEROSA")
    elif "MANHÃ" in tema_upper or "MANHÃ" in titulo_upper or "DIA" in tema_upper or "DIA" in titulo_upper:
        linhas = ["5 MINUTOS", "COM DEUS"]
        relogio = True
        if "HOJE" in titulo_upper or "COMEÇAR" in titulo_upper:
            linhas.append("PARA COMEÇAR O DIA")
        else:
            linhas.append("HOJE")
    elif salmo and len(salmo.strip()) > 0:
        num_salmo = salmo.replace("Salmo", "").replace("SALMO", "").strip()
        linhas = ["ORAÇÃO DO", f"SALMO {num_salmo}"]
        # Pega a palavra principal do tema para a 3ª linha
        palavras = [p for p in tema_upper.split() if len(p) > 3]
        linhas.append(palavras[0] if palavras else "PODEROSA")
    else:
        # Default genérico
        linhas = ["ORAÇÃO", "DE HOJE"]
        palavras = [p for p in tema_upper.split() if len(p) > 3]
        linhas.append(palavras[0] if palavras else "PODEROSA")

    # 4. Desenhar os textos na área esquerda
    x_pos = 80  # margem esquerda
    y_pos = 120  # posição vertical inicial
    
    for idx, linha in enumerate(linhas):
        # Determina a cor de cada linha para dar contraste e ritmo visual
        if idx == len(linhas) - 1:
            # Última linha chamativa sempre em amarelo/ouro
            cor = AMARELO
            tamanho = 88
        elif idx == 0 and ("5 MIN" in linha or "SÓ" in linha or "relogio" in str(relogio)):
            cor = AMARELO
            tamanho = 82
        else:
            cor = BRANCO
            tamanho = 96

        font = _fonte(tamanho, bold=True)
        
        # Caso o texto seja muito longo para o tamanho padrão, reduz um pouco
        bbox = draw.textbbox((0, 0), linha, font=font)
        w_texto = bbox[2] - bbox[0]
        if w_texto > 720:  # limite da margem de texto
            font = _fonte(int(tamanho * (720 / w_texto)), bold=True)
            bbox = draw.textbbox((0, 0), linha, font=font)
            w_texto = bbox[2] - bbox[0]

        # Usa as métricas reais da fonte para evitar pulos/pulo de linha desiguais entre palavras com e sem acento
        ascent, descent = font.getmetrics()
        # Em letras maiúsculas, a altura visual primária é o ascent. Vamos usá-lo para espaçamento compacto
        altura_linha = ascent

        # Espessura do contorno proporcional ao tamanho da letra (para ficar bem acabado)
        stroke_w = max(3, int(font.size * 0.06))

        # Efeito de contorno (Stroke) dinâmico
        draw.text(
            (x_pos, y_pos),
            linha,
            fill=cor,
            font=font,
            stroke_width=stroke_w,
            stroke_fill=PRETO
        )

        # Desenhar relógio analógico se for solicitado e for a linha do tempo
        if relogio and ("5" in linha or "MINUTOS" in linha) and idx == 0:
            rx = x_pos + w_texto + 60
            ry = y_pos + (altura_linha // 2)
            _desenhar_relogio(draw, rx, ry, int(altura_linha * 0.45))

        # Avança a linha com um espaçamento bem compacto (line-height = 1.05 da altura principal)
        y_pos += int(altura_linha * 1.05) + (stroke_w)

    # 5. Salvar a thumbnail final
    output_path = os.path.join(output_dir, "thumbnail.jpg")
    canvas.save(output_path, "JPEG", quality=95)
    print(f"[OK] Nova Thumbnail com icrawler gerada: {output_path}")
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# Teste Local
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Teste de simulação rápida
    print("[TESTE] Rodando teste de geração de thumbnail...")
    try:
        gerar_thumbnail(
            salmo="Salmo 91",
            tema="Oração da Noite de Proteção e Sono Tranquilo",
            titulo="NÃO DURMA ANTES DE FAZER ESTA ORAÇÃO! O Salmo 91 vai te proteger",
            output_dir="output"
        )
    except Exception as e:
        print(f"❌ Erro no teste local: {e}")

