"""
pesquisar_titulo.py
───────────────────
Pesquisa os 3 vídeos mais visualizados no YouTube relacionados ao tema
do salmo e usa o Groq AI para gerar um título 90% similar ao padrão
dos concorrentes, mas personalizado para o Canal Oração.

Também extrai tags dos vídeos mais visualizados para enriquecer o SEO.

Requer:
  YOUTUBE_API_KEY    — chave pública de API (não OAuth)
  GROQ_API_KEY       — para geração inteligente do título
"""

import os
import re
import requests
from groq import Groq

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

# Tags fixas do canal (sempre incluídas)
TAGS_FIXAS_CANAL = [
    "oração", "oração poderosa", "canal oração", "oração do dia",
    "oração evangélica", "fé", "Deus", "Jesus", "palavra de Deus",
    "bênção", "milagre", "cura divina", "proteção",
]


def _buscar_top_videos_youtube(query: str, api_key: str, max_results: int = 5) -> list[dict]:
    """
    Busca vídeos no YouTube pela query ordenados por viewCount.
    Retorna lista com id, title, description, tags de cada vídeo.
    """
    # Passo 1: Buscar IDs pelo termo
    params_search = {
        "part":       "snippet",
        "q":          query,
        "type":       "video",
        "order":      "viewCount",
        "relevanceLanguage": "pt",
        "regionCode": "BR",
        "maxResults": max_results,
        "key":        api_key,
    }

    try:
        resp = requests.get(YOUTUBE_SEARCH_URL, params=params_search, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception as e:
        print(f"  ⚠️  Erro ao buscar vídeos no YouTube: {e}")
        return []

    if not items:
        return []

    video_ids = [item["id"]["videoId"] for item in items if "videoId" in item.get("id", {})]
    if not video_ids:
        return []

    # Passo 2: Buscar detalhes (estatísticas + snippet com tags)
    params_videos = {
        "part":  "snippet,statistics",
        "id":    ",".join(video_ids),
        "key":   api_key,
    }

    try:
        resp2 = requests.get(YOUTUBE_VIDEOS_URL, params=params_videos, timeout=15)
        resp2.raise_for_status()
        videos = resp2.json().get("items", [])
    except Exception as e:
        print(f"  ⚠️  Erro ao buscar detalhes dos vídeos: {e}")
        return []

    resultado = []
    for v in videos:
        snippet    = v.get("snippet", {})
        stats      = v.get("statistics", {})
        resultado.append({
            "id":          v.get("id", ""),
            "titulo":      snippet.get("title", ""),
            "descricao":   snippet.get("description", "")[:300],
            "tags":        snippet.get("tags", []),
            "views":       int(stats.get("viewCount", 0)),
            "canal":       snippet.get("channelTitle", ""),
        })

    # Ordenar por views decrescente
    resultado.sort(key=lambda x: x["views"], reverse=True)
    return resultado[:3]


def _gerar_titulo_com_ia(titulos_ref: list[str], tema: str, salmo: str) -> str:
    """
    Usa Groq AI para gerar um título 90% similar aos títulos de referência,
    personalizado para o Canal Oração.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    titulos_formatados = "\n".join(f"  {i+1}. {t}" for i, t in enumerate(titulos_ref))

    prompt = f"""Você é especialista em SEO para canais cristãos no YouTube brasileiro.

Analise os 3 títulos de vídeos mais visualizados sobre "{tema} - Salmo {salmo}" abaixo:

{titulos_formatados}

Sua tarefa: Crie UM ÚNICO título para o "Canal Oração" que seja:
- 90% similar em estrutura e palavras-chave aos títulos acima
- Ligeiramente diferente para não ser cópia exata
- Entre 60 e 80 caracteres
- Em português brasileiro
- Contenha emoção e apelo espiritual
- NÃO use aspas, colchetes ou formatação especial
- Responda APENAS com o título, sem explicações

Exemplo do padrão esperado (baseado nos acima, mas adaptado):
Se os títulos têm "ORAÇÃO PODEROSA DO SALMO 91", o seu deve ter estrutura similar.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=150,
        )
        titulo = response.choices[0].message.content.strip()
        # Limpa aspas extras que a IA pode retornar
        titulo = titulo.strip('"\'').strip()
        return titulo[:100]
    except Exception as e:
        print(f"  ⚠️  Erro ao gerar título com IA: {e}")
        # Fallback com título padrão melhorado
        return f"ORAÇÃO PODEROSA DO SALMO {salmo} — {tema.upper()} | Canal Oração"


def _extrair_tags_concorrentes(videos: list[dict]) -> list[str]:
    """
    Extrai e deduplica tags dos vídeos concorrentes.
    Filtra tags relevantes (ignora marcas de outros canais).
    """
    tags_vistas = set()
    tags_relevantes = []

    # Palavras que indicam tag de marca de outro canal (ignorar)
    _ignorar = {"bispo", "pastor", "padre", "padre"}

    for video in videos:
        for tag in video.get("tags", []):
            tag_lower = tag.lower().strip()
            if tag_lower in tags_vistas:
                continue
            # Ignora tags muito longas ou com nome de canal concorrente
            if len(tag) > 40:
                continue
            # Ignora tags que provavelmente são nome de pastores concorrentes
            primeira_palavra = tag_lower.split()[0] if tag_lower else ""
            if primeira_palavra in _ignorar:
                continue
            tags_vistas.add(tag_lower)
            tags_relevantes.append(tag)

    return tags_relevantes


def pesquisar_e_gerar_titulo(tema: str, salmo: str) -> tuple[str, list[str]]:
    """
    Função principal do módulo.

    1. Busca top 3 vídeos do YouTube pelo tema + salmo
    2. Gera título 90% similar via Groq AI
    3. Extrai tags dos vídeos mais visualizados

    Retorna: (titulo_otimizado, lista_de_tags_combinadas)
    """
    api_key = os.environ.get("YOUTUBE_API_KEY", "")

    if not api_key:
        print("  ⚠️  YOUTUBE_API_KEY não configurada. Usando título padrão.")
        titulo_padrao = f"ORAÇÃO PODEROSA DO SALMO {salmo} — {tema.upper()} | Canal Oração"
        return titulo_padrao, TAGS_FIXAS_CANAL.copy()

    query = f"oração salmo {salmo} {tema} poderosa"
    print(f"  🔍 Pesquisando YouTube: \"{query}\"")

    videos = _buscar_top_videos_youtube(query, api_key, max_results=5)

    if not videos:
        print("  ⚠️  Nenhum vídeo encontrado. Tentando busca alternativa...")
        query_alt = f"oração {tema} poderosa evangélica"
        videos = _buscar_top_videos_youtube(query_alt, api_key, max_results=5)

    tags_concorrentes = []

    if videos:
        print(f"  📊 Top {len(videos)} vídeos encontrados:")
        titulos_ref = []
        for v in videos:
            views_fmt = f"{v['views']:,}".replace(",", ".")
            print(f"     • {v['titulo'][:60]}... ({views_fmt} views)")
            titulos_ref.append(v["titulo"])

        print("  🤖 Gerando título otimizado com IA...")
        titulo = _gerar_titulo_com_ia(titulos_ref, tema, salmo)
        tags_concorrentes = _extrair_tags_concorrentes(videos)
        print(f"  ✅ Título gerado: {titulo}")
        print(f"  🏷️  Tags dos concorrentes: {len(tags_concorrentes)} extraídas")
    else:
        print("  ⚠️  Sem vídeos de referência. Usando título padrão.")
        titulo = f"ORAÇÃO PODEROSA DO SALMO {salmo} — {tema.upper()} | Canal Oração"

    # Combinar tags: fixas do canal + concorrentes (sem duplicatas)
    tags_fixas_lower = {t.lower() for t in TAGS_FIXAS_CANAL}
    tags_extras = [t for t in tags_concorrentes if t.lower() not in tags_fixas_lower]

    tags_finais = TAGS_FIXAS_CANAL.copy() + tags_extras

    # Limitar ao total de 500 chars que a YouTube API aceita
    total_chars = 0
    tags_limitadas = []
    for tag in tags_finais:
        if total_chars + len(tag) + 1 <= 500:
            tags_limitadas.append(tag)
            total_chars += len(tag) + 1
        else:
            break

    return titulo, tags_limitadas


if __name__ == "__main__":
    # Teste rápido
    titulo, tags = pesquisar_e_gerar_titulo("Proteção Divina e Familiar", "91")
    print(f"\n📌 Título final: {titulo}")
    print(f"🏷️  Total de tags: {len(tags)}")
    print(f"   {tags}")
