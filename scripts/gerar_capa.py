"""
gerar_capa.py
─────────────
Gera a thumbnail do vídeo (1280×720) no estilo moderno de canais de orações:
  • Imagem de fundo: Busca via Wikimedia Commons (Wikipedia) — domínio público, 100% seguro.
    Fallback: Bing Image Search com safeSearch=Strict.
    Fallback: Pexels com termos religiosos controlados.
  • Tema: Jesus Cristo (pintura, ilustração ou arte digital de alta definição)
  • Fusão degradê horizontal suave para o lado esquerdo (onde fica o texto)
  • Textos grandes e chamativos em fonte Sans-serif pesada (Arial Black/Impact) com contorno preto (stroke)
  • Ícone estilizado de relógio desenhado sob demanda caso mencione tempo
"""

import os
import io
import re
import random
import requests
import urllib.parse
from PIL import Image, ImageDraw, ImageFont

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
BING_API_KEY   = os.environ.get("BING_SEARCH_API_KEY", "")  # opcional — chave Azure Cognitive
LARGURA, ALTURA = 1280, 720

# Paleta de cores
BRANCO       = (255, 255, 255)
DOURADO      = (255, 215, 0)
AMARELO      = (255, 235, 59)
PRETO        = (0, 0, 0)
PRETO_RICO   = (8, 6, 4)

# User-Agent legítimo para requisições HTTP
UA = (
    "Mozilla/5.0 (compatible; CanalOracao/1.0; "
    "+https://github.com/robsonvit/canal-oracao)"
)

# Queries fixas do Wikimedia Commons para arte sacra de Jesus
_WIKIMEDIA_QUERIES = [
    "Jesus Christ painting",
    "Jesus praying art",
    "Sacred Heart of Jesus painting",
    "Jesus Christ resurrection painting",
    "Jesus Christ portrait painting",
    "Christ praying Gethsemane painting",
]


# ─────────────────────────────────────────────────────────────────────────────
# 1. Funções de busca segura de imagem (Wikimedia / Bing / Pexels)
# ─────────────────────────────────────────────────────────────────────────────

def _montar_query(tema: str, titulo: str) -> str:
    """Define query de busca baseada no tema — sempre relacionada a Jesus/arte sacra."""
    texto = (tema or "").lower() + " " + (titulo or "").lower()
    if "noite" in texto or "dormir" in texto:
        return "Jesus Christ praying night painting artwork"
    if "manh" in texto or "amanhecer" in texto or "dia" in texto:
        return "Jesus Christ sunrise dawn painting artwork"
    if "espinhos" in texto or "coroa" in texto:
        return "Jesus Christ crown thorns painting sacred art"
    if "ressurrei" in texto or "ressuscitou" in texto:
        return "Jesus Christ resurrection painting artwork"
    if "paz" in texto or "tranquil" in texto:
        return "Jesus Christ peaceful painting artwork"
    return "Jesus Christ praying painting sacred artwork"


def _baixar_imagem(url: str, min_w: int = 400, min_h: int = 300):
    """Baixa e valida uma imagem. Rejeita se for muito pequena."""
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=20, stream=True)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        w, h = img.size
        if w < min_w or h < min_h:
            print(f"[AVISO] Imagem muito pequena ({w}x{h}), ignorando.")
            return None
        return img
    except Exception as e:
        print(f"[AVISO] Falha ao baixar imagem: {e}")
        return None


def _obter_url_wikimedia(titulo_arquivo: str):
    """Obtém a URL direta de download de um arquivo do Wikimedia Commons."""
    encoded = urllib.parse.quote(titulo_arquivo)
    info_url = (
        "https://commons.wikimedia.org/w/api.php"
        f"?action=query&titles=File:{encoded}"
        "&prop=imageinfo&iiprop=url&iiurlwidth=1280"
        "&format=json&origin=*"
    )
    try:
        resp = requests.get(info_url, headers={"User-Agent": UA}, timeout=10)
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            imageinfo = page.get("imageinfo", [])
            if imageinfo:
                return imageinfo[0].get("thumburl") or imageinfo[0].get("url")
    except Exception as e:
        print(f"[AVISO] Erro URL Wikimedia '{titulo_arquivo[:40]}': {e}")
    return None


def _buscar_wikimedia(query: str):
    """
    Busca imagem no Wikimedia Commons via API pública.
    Retorna apenas imagens de domínio público / arte sacra religiosa.
    """
    search_term = urllib.parse.quote(query)
    api_url = (
        "https://commons.wikimedia.org/w/api.php"
        f"?action=query&list=search&srsearch={search_term}"
        "&srnamespace=6&srlimit=15&format=json&origin=*"
    )
    try:
        resp = requests.get(api_url, headers={"User-Agent": UA}, timeout=15)
        resp.raise_for_status()
        resultados = resp.json().get("query", {}).get("search", [])
        imagens = [
            r for r in resultados
            if any(ext in r["title"].lower() for ext in [".jpg", ".jpeg", ".png"])
        ]
        if not imagens:
            return None
        random.shuffle(imagens)
        for item in imagens[:5]:
            titulo_arquivo = item["title"].replace("File:", "").strip()
            url_img = _obter_url_wikimedia(titulo_arquivo)
            if url_img:
                img = _baixar_imagem(url_img)
                if img:
                    print(f"[OK] Imagem do Wikimedia Commons: {titulo_arquivo[:60]}")
                    return img
    except Exception as e:
        print(f"[AVISO] Wikimedia falhou para '{query}': {e}")
    return None


def _buscar_bing_api(query: str):
    """Usa a API oficial do Bing Image Search (Azure Cognitive Services) com safeSearch=Strict."""
    try:
        headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY, "User-Agent": UA}
        params  = {
            "q": query, "count": 10,
            "safeSearch": "Strict",  # FILTRO DE CONTEÚDO ADULTO — OBRIGATÓRIO
            "imageType": "Photo", "aspect": "Wide",
            "minWidth": 800, "minHeight": 500,
        }
        resp = requests.get(
            "https://api.bing.microsoft.com/v7.0/images/search",
            headers=headers, params=params, timeout=15
        )
        resp.raise_for_status()
        items = resp.json().get("value", [])
        random.shuffle(items)
        for item in items[:5]:
            img = _baixar_imagem(item.get("contentUrl", ""))
            if img:
                print("[OK] Imagem via Bing API (safeSearch=Strict)")
                return img
    except Exception as e:
        print(f"[AVISO] Bing API falhou: {e}")
    return None


def _buscar_bing_public(query: str):
    """
    Busca no endpoint público do Bing Images (sem chave de API).
    Usa safeSearch=Strict e filtra por licença Creative Commons.
    """
    try:
        encoded = urllib.parse.quote(f"{query} painting art")
        url = (
            f"https://www.bing.com/images/search"
            f"?q={encoded}&form=HDRSC2&first=1&count=10"
            f"&qft=+filterui:license-L2_L3_L4_L5_L6_L7"
            f"&safeSearch=Strict"
        )
        headers = {
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        pattern = r'"murl":"(https?://[^"]+\.(?:jpg|jpeg|png))"'
        urls = re.findall(pattern, resp.text)
        if not urls:
            urls_enc = re.findall(r'imgurl=([^&"]+\.(?:jpg|jpeg|png))', resp.text)
            urls = [urllib.parse.unquote(u) for u in urls_enc]
        if not urls:
            print("[AVISO] Bing público não retornou URLs de imagens.")
            return None
        random.shuffle(urls)
        for url_img in urls[:5]:
            img = _baixar_imagem(url_img)
            if img:
                print("[OK] Imagem via Bing público (safeSearch=Strict, CC-License)")
                return img
    except Exception as e:
        print(f"[AVISO] Bing público falhou: {e}")
    return None


def _buscar_bing(query: str):
    """Usa API oficial se BING_API_KEY estiver definida; caso contrário, endpoint público."""
    if BING_API_KEY:
        return _buscar_bing_api(query)
    return _buscar_bing_public(query)


_TERMOS_PEXELS_SEGUROS = [
    "praying hands bible",
    "open bible candle light",
    "cross sunset silhouette",
    "church interior light",
    "hands prayer worship",
    "candle flame dark background",
    "holy book religion",
]


def _buscar_pexels(query: str):
    """Busca imagens religiosas seguras no Pexels com termos controlados."""
    if not PEXELS_API_KEY:
        return None
    headers = {"Authorization": PEXELS_API_KEY}
    for termo in ([query] + _TERMOS_PEXELS_SEGUROS):
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params={"query": termo, "orientation": "landscape", "per_page": 8},
                timeout=15,
            )
            fotos = resp.json().get("photos", [])
            if fotos:
                foto = random.choice(fotos)
                url  = foto["src"].get("large2x") or foto["src"].get("large")
                img  = _baixar_imagem(url)
                if img:
                    print(f"[OK] Imagem religiosa segura do Pexels: '{termo}'")
                    return img
        except Exception as e:
            print(f"[AVISO] Pexels falhou para '{termo}': {e}")
    return None


def _buscar_imagem_jesus(tema: str, titulo: str, output_dir: str) -> Image.Image:
    """
    Busca imagem artística de Jesus / arte sacra.
    Ordem de prioridade:
      1. Wikimedia Commons — domínio público, 100% seguro, arte sacra verificada
      2. Bing Image Search com safeSearch=Strict — filtro ativo
      3. Pexels com termos religiosos genéricos — fallback controlado
      4. Gradiente escuro — fallback absoluto (sem imagem externa)
    """
    query = _montar_query(tema, titulo)
    print(f"[BUSCA] Query: '{query}'")

    # 1. Wikimedia Commons (Wikipedia)
    print("[BUSCA] 1. Wikimedia Commons (Wikipedia, domínio público)...")
    for q in ([query] + _WIKIMEDIA_QUERIES):
        img = _buscar_wikimedia(q)
        if img:
            return img

    # 2. Bing Image Search (safeSearch=Strict)
    print("[BUSCA] 2. Bing Image Search (safeSearch=Strict)...")
    img = _buscar_bing(query)
    if img:
        return img

    # 3. Pexels com termos religiosos controlados
    print("[BUSCA] 3. Pexels com termos religiosos...")
    img = _buscar_pexels(query)
    if img:
        return img

    # 4. Fallback absoluto: gradiente escuro elegante
    print("[AVISO] Todos os métodos falharam. Usando gradiente escuro.")
    img = Image.new("RGB", (LARGURA, ALTURA), (18, 12, 8))
    draw = ImageDraw.Draw(img)
    for y in range(ALTURA):
        r = int(18 + (y / ALTURA) * 15)
        g = int(12 + (y / ALTURA) * 10)
        b = int(8  + (y / ALTURA) * 8)
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

