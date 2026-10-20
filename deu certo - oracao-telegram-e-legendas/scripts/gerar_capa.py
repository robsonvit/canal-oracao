"""
gerar_capa.py
─────────────
Gera a thumbnail do vídeo (1280×720) no padrão de alta conversão de canais de oração:
  • Imagem religiosa: Busca EXCLUSIVAMENTE no Pinterest via pinscrape, priorizando
    proporção 16:9 e alta definição.
    Categorias cobertas:
      1. Jesus Cristo (arte sacra, pintura clássica, orando no Getsêmani, olhar misericordioso)
      2. Bíblia sagrada (aberta com luz divina, velas, altar)
      3. Pessoas em posição de oração (mãos postas, clamor com fé, joelhos dobrados)
      4. Pomba branca (Espírito Santo, luz celeste, paz)
  • Layout de Alta Conversão (CTR):
    - Imagem posicionada no lado direito com enquadramento de destaque
    - Fusão em degradê suave (curva cosseno) para fundo preto total no lado esquerdo
    - Fundo escuro/preto sólido à esquerda garantindo 100% de legibilidade
    - Textos grandes em fonte IMPACT (pesada e condensada)
    - Paleta de alto contraste: Branco e Amarelo Dourado com contorno (stroke) preto nítido
    - Ícone de relógio estilizado caso mencione tempo ("5 MINUTOS", etc.)
"""

import os
import io
import math
import random
import requests
from PIL import Image, ImageDraw, ImageFont
from pinscrape import Pinterest

LARGURA, ALTURA = 1280, 720

# Paleta de cores de alta visibilidade para thumbnails do YouTube
BRANCO       = (255, 255, 255)
AMARELO      = (255, 235, 59)
DOURADO      = (255, 215, 0)
PRETO        = (0, 0, 0)
PRETO_SUAVE  = (10, 10, 10)

# Dicionário curado de termos de busca no Pinterest (priorizando 16:9, arte sacra de Jesus Cristo e alta definição)
TERMOS_RELIGIOSOS_PINTEREST = {
    "jesus": [
        "Jesus Cristo pintura classica wallpaper 16:9",
        "Jesus Christ artwork wallpaper 4k 16:9",
        "Jesus Cristo olhar misericordioso pintura 16:9",
        "Jesus Cristo luz divina wallpaper 16:9",
        "Sagrado Coracao de Jesus arte 16:9",
        "Jesus orando Getsemani pintura wallpaper 16:9",
        "Jesus Cristo ressuscitado arte sacra 16:9",
        "Jesus Cristo salvador pintura hd 16:9",
    ],
    "biblia": [
        "biblia sagrada aberta altar velas wallpaper 16:9",
        "open holy bible candle light wallpaper 16:9",
        "biblia aberta luz divina wallpaper 16:9",
        "biblia sagrada e cruz luz celestial 16:9",
        "holy bible church altar wallpaper hd 16:9",
    ],
    "oracao": [
        "Jesus Cristo orando pintura classica 16:9",
        "Jesus orando Getsemani wallpaper hd",
        "Jesus Cristo com ovelha bom pastor pintura 16:9",
        "Jesus abencoando pintura arte sacra 16:9",
        "Jesus Cristo perdoa pecadora pintura arte 16:9",
    ],
    "pomba": [
        "espirito santo pomba branca luz celestial 16:9",
        "white dove holy spirit wallpaper hd 16:9",
        "espirito santo pentecostes arte sacra wallpaper 16:9",
    ]
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Busca Exclusiva no Pinterest
# ─────────────────────────────────────────────────────────────────────────────

def _selecionar_queries_pinterest(tema: str, titulo: str) -> list[str]:
    """
    Seleciona as queries mais adequadas do Pinterest.
    Prioriza arte sacra marcante de Jesus Cristo e Bíblia sagrada.
    """
    texto = (tema or "").lower() + " " + (titulo or "").lower()
    queries = []

    if any(k in texto for k in ["pomba", "espirito santo", "espírito santo", "pentecostes"]):
        queries.extend(TERMOS_RELIGIOSOS_PINTEREST["pomba"])
        queries.extend(TERMOS_RELIGIOSOS_PINTEREST["jesus"])
    elif any(k in texto for k in ["biblia", "bíblia", "palavra", "versiculo", "versículo"]):
        queries.extend(TERMOS_RELIGIOSOS_PINTEREST["biblia"])
        queries.extend(TERMOS_RELIGIOSOS_PINTEREST["jesus"])
    else:
        # Padrão de máxima conversão: Jesus Cristo e oração solene
        queries.extend(TERMOS_RELIGIOSOS_PINTEREST["jesus"])
        queries.extend(TERMOS_RELIGIOSOS_PINTEREST["oracao"])
        queries.extend(TERMOS_RELIGIOSOS_PINTEREST["biblia"])

    random.shuffle(queries)
    return queries


def _buscar_imagem_pinterest(tema: str, titulo: str) -> Image.Image | None:
    """
    Busca imagens religiosas exclusivamente no Pinterest.
    Prioriza fortemente imagens horizontais e 16:9 (proporção ~1.78) de arte sacra / Jesus Cristo.
    """
    queries = _selecionar_queries_pinterest(tema, titulo)
    p = Pinterest(proxies={}, sleep_time=0.3)

    for q in queries[:5]:
        print(f"[PINTEREST] Buscando: '{q}'...")
        try:
            urls = p.search(q, 8)
            if not urls:
                continue

            candidatas = []
            for url in urls:
                try:
                    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                    if resp.status_code == 200:
                        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                        w, h = img.size
                        # Filtra imagens muito pequenas
                        if w >= 450 and h >= 300:
                            aspect = w / h
                            # Pontuação: prioriza fortemente imagens horizontais e 16:9
                            if aspect >= 1.3:
                                # Imagem horizontal (16:9 ideal aspect ~ 1.777)
                                score = 100.0 - (abs(aspect - 1.777) * 20.0) + (w / 100.0)
                            elif aspect >= 1.0:
                                # Imagem quadrada ou quase horizontal
                                score = 40.0 + (w / 100.0)
                            else:
                                # Imagem vertical (penalidade severa para preferir horizontal)
                                score = 5.0 + (w / 200.0)

                            candidatas.append((score, aspect, img, url))
                except Exception:
                    continue

            if candidatas:
                # Escolhe a melhor imagem (horizontais 16:9 vencem)
                candidatas.sort(key=lambda x: x[0], reverse=True)
                melhor = candidatas[0]
                print(f"[PINTEREST] Imagem selecionada: {melhor[2].size} (proporção {melhor[1]:.2f}) | Score: {melhor[0]:.1f} | URL: {melhor[3][:70]}...")
                return melhor[2]

        except Exception as e:
            print(f"[AVISO] Pinterest busca falhou para '{q}': {e}")
            continue

    print("[AVISO] Nenhuma imagem foi obtida do Pinterest. Aplicando gradiente escuro de fallback.")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 2. Carregamento da Fonte IMPACT
# ─────────────────────────────────────────────────────────────────────────────

def _obter_fonte_impact(tamanho: int) -> ImageFont.FreeTypeFont:
    """
    Carrega especificamente a fonte IMPACT (pesada e condensada para YouTube thumbs).
    Prioriza o arquivo local assets/fonts/impact.ttf versionado no projeto.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminhos = [
        os.path.join(base_dir, "assets", "fonts", "impact.ttf"),
        os.path.join(base_dir, "assets", "fonts", "IMPACT.TTF"),
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/IMPACT.TTF",
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/impact.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for caminho in caminhos:
        if os.path.exists(caminho):
            try:
                font = ImageFont.truetype(caminho, tamanho)
                print(f"[FONTE] Impact carregada: {caminho} (tamanho {tamanho})")
                return font
            except Exception as e:
                continue
    return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────────────────────
# 3. Composição com Degradê Fundo Preto
# ─────────────────────────────────────────────────────────────────────────────

def _processar_degrade_fundo(foto: Image.Image | None) -> Image.Image:
    """
    Posiciona a imagem religiosa no lado direito e aplica um degradê horizontal
    suave com fundo preto total no lado esquerdo (onde fica o texto).
    """
    base = Image.new("RGB", (LARGURA, ALTURA), PRETO)

    if foto is None:
        # Fallback sutil com leve iluminação dourada se não houver imagem
        draw = ImageDraw.Draw(base)
        for x in range(LARGURA):
            r = int(15 * (x / LARGURA))
            g = int(12 * (x / LARGURA))
            b = int(6  * (x / LARGURA))
            draw.line([(x, 0), (x, ALTURA)], fill=(r, g, b))
        return base

    w, h = foto.size
    aspect = w / h

    # Ajusta o dimensionamento da imagem para o quadrante direito
    if aspect >= 1.5:
        # Imagem já é horizontal: redimensiona para cobrir 1280x720 focando o lado direito
        escala = ALTURA / h
        nova_w = int(w * escala)
        nova_h = ALTURA
        if nova_w < LARGURA:
            escala = LARGURA / w
            nova_w = LARGURA
            nova_h = int(h * escala)
        foto_resized = foto.resize((nova_w, nova_h), Image.LANCZOS)
        # Recorta focando na direita
        offset_x = max(0, nova_w - LARGURA)
        offset_y = max(0, (nova_h - ALTURA) // 2)
        foto_crop = foto_resized.crop((offset_x, offset_y, offset_x + LARGURA, offset_y + ALTURA))
        base.paste(foto_crop, (0, 0))
        pos_x_imagem = 450
    else:
        # Imagem quadrada ou vertical: escala para altura 720 com largura mínima de ~750px
        escala = ALTURA / h
        nova_w = int(w * escala)
        nova_h = ALTURA
        if nova_w < 750:
            escala = 750 / w
            nova_w = int(w * escala)
            nova_h = int(h * escala)

        foto_resized = foto.resize((nova_w, nova_h), Image.LANCZOS)
        if nova_h > ALTURA:
            offset_y = (nova_h - ALTURA) // 2
            foto_resized = foto_resized.crop((0, offset_y, nova_w, offset_y + ALTURA))

        pos_x_imagem = max(350, LARGURA - nova_w)
        base.paste(foto_resized, (pos_x_imagem, 0))

    # Cria a máscara de degradê horizontal preto:
    # - Da margem esquerda até 'inicio_fade': 100% Preto puro (área exclusiva do texto)
    # - De 'inicio_fade' até 'fim_fade': curva suave cosseno de fade-out do preto
    # - A partir de 'fim_fade': imagem 100% visível, nítida e brilhante
    overlay = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    inicio_fade = max(300, pos_x_imagem - 60)
    fim_fade = min(LARGURA - 80, pos_x_imagem + 380)
    distancia = max(1, fim_fade - inicio_fade)

    for x in range(LARGURA):
        if x <= inicio_fade:
            alpha = 255
        elif x <= fim_fade:
            # Curva suave cosseno de 1.0 a 0.0 (elimina cortes visíveis)
            progresso = (x - inicio_fade) / distancia
            fator = (1.0 + math.cos(progresso * math.pi)) / 2.0
            alpha = int(255 * fator)
        else:
            alpha = 0
        draw_overlay.line([(x, 0), (x, ALTURA)], fill=(0, 0, 0, alpha))

    # Fusão suave do degradê sobre o canvas
    resultado = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# 4. Elementos Visuais Auxiliares (Ícones)
# ─────────────────────────────────────────────────────────────────────────────

def _desenhar_relogio(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int):
    """Desenha um relógio analógico estilizado caso mencione tempo (ex: 5 MINUTOS)."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=AMARELO, outline=PRETO, width=5)
    # Sinos do despertador
    draw.pieslice([cx - r, cy - r, cx - int(r * 0.5), cy - int(r * 0.5)], start=180, end=270, fill=PRETO)
    draw.pieslice([cx + int(r * 0.5), cy - r, cx + r, cy - int(r * 0.5)], start=270, end=360, fill=PRETO)
    # Ponteiros
    draw.line([cx, cy, cx, cy - r + 14], fill=PRETO, width=5)
    draw.line([cx, cy, cx + r - 16, cy], fill=PRETO, width=5)
    draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=PRETO)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Função Principal de Geração de Thumbnail
# ─────────────────────────────────────────────────────────────────────────────

def gerar_thumbnail(salmo: str, tema: str, titulo: str, output_dir: str = "output") -> str:
    """
    Gera uma thumbnail de alta definição com:
      - Imagem religiosa buscada exclusivamente no Pinterest
      - Fundo escuro à esquerda com degradê suave para a imagem à direita
      - Textos chamativos com fonte IMPACT
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Buscar imagem religiosa apenas no Pinterest
    foto_pinterest = _buscar_imagem_pinterest(tema, titulo)

    # 2. Processar fundo preto e degradê suave para o lado direito
    canvas = _processar_degrade_fundo(foto_pinterest)
    draw = ImageDraw.Draw(canvas)

    # 3. Definição das frases chamativas e de alto clique (CTR)
    tema_upper = (tema or "").upper().strip()
    titulo_upper = (titulo or "").upper().strip()

    linhas = []
    tem_relogio = False

    if any(k in tema_upper or k in titulo_upper for k in ["NOITE", "DORMIR", "SONO"]):
        linhas = ["ORAÇÃO", "DA NOITE"]
        if any(k in tema_upper or k in titulo_upper for k in ["5 MIN", "5MIN"]):
            linhas.append("SÓ 5 MINUTOS")
            tem_relogio = True
        else:
            linhas.append("PODEROSA")
    elif any(k in tema_upper or k in titulo_upper for k in ["MANHÃ", "MANHA", "DIA", "ACORDAR"]):
        linhas = ["5 MINUTOS", "COM DEUS"]
        tem_relogio = True
        if "HOJE" in titulo_upper or "COMEÇAR" in titulo_upper:
            linhas.append("PARA O SEU DIA")
        else:
            linhas.append("HOJE")
    elif salmo and len(salmo.strip()) > 0:
        num_salmo = salmo.replace("Salmo", "").replace("SALMO", "").strip()
        linhas = ["ORAÇÃO DO", f"SALMO {num_salmo}"]
        stopwords = {"PARA", "COM", "UMA", "DEUS", "NOSSO", "NOSSA", "SEU", "SUA", "SOBRE", "PELO", "PELA", "MEU", "MINHA"}
        palavras_impacto = [p for p in tema_upper.split() if len(p) > 2 and p not in stopwords]
        linhas.append(palavras_impacto[0] if palavras_impacto else "PODEROSA")
    else:
        linhas = ["ORAÇÃO", "DE HOJE"]
        stopwords = {"PARA", "COM", "UMA", "DEUS", "NOSSO", "NOSSA", "SEU", "SUA"}
        palavras_impacto = [p for p in tema_upper.split() if len(p) > 2 and p not in stopwords]
        linhas.append(palavras_impacto[0] if palavras_impacto else "PODEROSA")

    # 4. Renderizar textos com a fonte IMPACT no lado esquerdo
    x_pos = 70
    y_pos = 125
    largura_max_texto = 580  # Limite para manter o texto 100% sobre o fundo escuro

    for idx, linha in enumerate(linhas):
        # Definição de cores e tamanhos de impacto
        if idx == len(linhas) - 1:
            cor = AMARELO
            tam = 98
        elif idx == 0 and ("5 MIN" in linha or "SÓ" in linha or tem_relogio):
            cor = AMARELO
            tam = 104
        else:
            cor = BRANCO
            tam = 108

        font = _obter_fonte_impact(tam)

        # Ajuste dinâmico se a palavra for muito larga
        bbox = draw.textbbox((0, 0), linha, font=font)
        w_texto = bbox[2] - bbox[0]
        if w_texto > largura_max_texto:
            tam_ajustado = int(tam * (largura_max_texto / w_texto))
            font = _obter_fonte_impact(tam_ajustado)
            bbox = draw.textbbox((0, 0), linha, font=font)
            w_texto = bbox[2] - bbox[0]

        ascent, descent = font.getmetrics()
        altura_linha = ascent

        # Contorno preto pesado (stroke) para destacar do fundo escuro
        stroke_w = max(4, int(font.size * 0.07))

        draw.text(
            (x_pos, y_pos),
            linha,
            fill=cor,
            font=font,
            stroke_width=stroke_w,
            stroke_fill=PRETO
        )

        # Relógio caso seja linha de tempo
        if tem_relogio and ("5" in linha or "MINUTOS" in linha) and idx == 0:
            rx = x_pos + w_texto + 60
            ry = y_pos + (altura_linha // 2)
            _desenhar_relogio(draw, rx, ry, int(altura_linha * 0.45))

        # Espaçamento vertical proporcional e compacto
        y_pos += int(altura_linha * 1.08) + stroke_w

    # 5. Salvar a thumbnail gerada
    output_path = os.path.join(output_dir, "thumbnail.jpg")
    canvas.save(output_path, "JPEG", quality=95)
    print(f"[OK] Thumbnail com Pinterest e IMPACT gerada: {output_path}")
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# Teste Local Direto
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[TESTE] Gerando thumbnail com Pinterest, fonte IMPACT e degradê...")
    try:
        gerar_thumbnail(
            salmo="Salmo 91",
            tema="Oração da Noite de Proteção e Sono Tranquilo",
            titulo="NÃO DURMA ANTES DE FAZER ESTA ORAÇÃO! O Salmo 91 vai te proteger",
            output_dir="output"
        )
    except Exception as e:
        print(f"Erro no teste: {e}")
