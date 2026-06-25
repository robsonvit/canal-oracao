"""
buscar_video.py
───────────────
Busca e baixa múltiplos clipes de vídeo do Pexels para usar como fundo.

Regras implementadas:
  ✅ Cada clipe tem 5 segundos de filmagem original
  ✅ Cada vídeo só pode ser reutilizado após 5 DIAS do último uso
  ✅ Busca diversificada (vários termos de pesquisa)
  ✅ Ao baixar: remove metadados, inverte horizontalmente, reduz velocidade para 0.8x
  ✅ Histórico de uso salvo em data/videos_usados.json
"""

import os
import json
import random
import subprocess
import requests
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────────────────────────────────────────
# Configurações
# ─────────────────────────────────────────────────────────────────────────────
PEXELS_API_KEY   = os.environ.get("PEXELS_API_KEY", "")
TRACKING_FILE    = os.path.join("data", "videos_usados.json")
DIAS_BLOQUEIO    = 5        # Dias mínimos antes de reusar um vídeo
DURACAO_CLIP_S   = 5        # Segundos de filmagem original por clipe
VELOCIDADE       = 0.8      # Fator de velocidade (0.8x = mais lento)
NUM_CLIPS        = 12       # Quantidade de clipes distintos a baixar
CLIP_DIR         = os.path.join("output", "clips")

# Termos de busca variados para maximizar diversidade visual
TERMOS_BUSCA = [
    "peaceful forest sunlight",
    "calm nature sunrise",
    "flowing river nature",
    "sunrise mountains fog",
    "gentle ocean waves",
    "golden hour meadow",
    "forest light rays",
    "beautiful sky clouds",
    "waterfall nature",
    "morning dew grass",
    "candle flame close up",
    "open book light",
    "praying hands nature",
    "cross sunset silhouette",
    "peaceful lake reflection",
    "birds flying sky",
    "wheat field wind",
    "light through leaves",
    "mountain valley sunrise",
    "rain drops window",
]


# ─────────────────────────────────────────────────────────────────────────────
# Tracking: controle de vídeos usados recentemente
# ─────────────────────────────────────────────────────────────────────────────
def _carregar_tracking() -> dict:
    """Carrega o JSON de tracking; retorna {} se não existir."""
    os.makedirs("data", exist_ok=True)
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _salvar_tracking(tracking: dict):
    """Persiste o JSON de tracking no disco."""
    os.makedirs("data", exist_ok=True)
    with open(TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(tracking, f, indent=2, ensure_ascii=False)


def _video_disponivel(video_id: str, tracking: dict) -> bool:
    """Retorna True se o vídeo não foi usado nos últimos DIAS_BLOQUEIO dias."""
    if str(video_id) not in tracking:
        return True
    ultimo_uso = datetime.fromisoformat(tracking[str(video_id)])
    limite     = datetime.now(timezone.utc) - timedelta(days=DIAS_BLOQUEIO)
    return ultimo_uso < limite


def _marcar_usado(video_id: str, tracking: dict):
    """Marca o vídeo como usado agora no tracking."""
    tracking[str(video_id)] = datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# Busca no Pexels
# ─────────────────────────────────────────────────────────────────────────────
def _buscar_videos_pexels(termo: str, excluir_ids: set, max_resultados: int = 15) -> list:
    """
    Busca vídeos no Pexels e retorna lista de candidatos disponíveis.
    Filtra IDs já recentemente usados (excluir_ids).
    """
    headers  = {"Authorization": PEXELS_API_KEY}
    params   = {
        "query":       termo,
        "orientation": "landscape",
        "size":        "medium",   # SD ou HD (mais rápido de baixar)
        "per_page":    max_resultados,
    }
    try:
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers, params=params, timeout=30
        )
        resp.raise_for_status()
        videos = resp.json().get("videos", [])

        candidatos = []
        for v in videos:
            if v["id"] in excluir_ids:
                continue
            # Pegar melhor arquivo MP4 disponível
            arquivos_mp4 = [
                f for f in v.get("video_files", [])
                if f.get("file_type") == "video/mp4"
                and f.get("width", 0) >= 1280
            ]
            if not arquivos_mp4:
                arquivos_mp4 = [
                    f for f in v.get("video_files", [])
                    if f.get("file_type") == "video/mp4"
                ]
            if arquivos_mp4:
                melhor = max(arquivos_mp4, key=lambda x: x.get("width", 0))
                candidatos.append({
                    "id":       v["id"],
                    "duracao":  v.get("duration", 10),
                    "url":      melhor["link"],
                    "largura":  melhor.get("width", 0),
                    "altura":   melhor.get("height", 0),
                })
        return candidatos
    except Exception as e:
        print(f"  ⚠️  Erro na busca '{termo}': {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Download + transformações FFmpeg
# ─────────────────────────────────────────────────────────────────────────────
def _baixar_video(url: str, destino_tmp: str):
    """Baixa o vídeo em streaming para destino_tmp."""
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(destino_tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def _processar_clip(input_path: str, output_path: str, duracao_video: int):
    """
    Aplica as transformações via FFmpeg em um único passo:
      1. Escolhe posição aleatória de início (garantindo 5s disponíveis)
      2. Corta 5 segundos de filmagem
      3. Inverte horizontalmente (hflip)
      4. Reduz velocidade para 0.8x (setpts=1.25*PTS)
      5. Remove metadados (map_metadata -1)

    Resultado: clipe de ~6.25s no output (5s ÷ 0.8 = 6.25s)
    """
    # Posição de início aleatória (deixa pelo menos 5s + 1s de margem)
    margem       = max(1, duracao_video - DURACAO_CLIP_S - 1)
    inicio       = random.uniform(0, margem) if margem > 0 else 0
    velocidade_pts = 1.0 / VELOCIDADE  # 1/0.8 = 1.25

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(inicio),
        "-t",  str(DURACAO_CLIP_S),
        "-i",  input_path,
        "-vf", f"scale=1920:1080:force_original_aspect_ratio=increase,"
               f"crop=1920:1080,"
               f"hflip,"
               f"setpts={velocidade_pts:.4f}*PTS",
        "-an",                        # Sem áudio (usaremos o TTS)
        "-map_metadata", "-1",        # Remove todos os metadados
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg erro ao processar clipe:\n{result.stderr[-400:]}")


# ─────────────────────────────────────────────────────────────────────────────
# Interface pública principal
# ─────────────────────────────────────────────────────────────────────────────
def buscar_e_processar_clips(n_clips: int = NUM_CLIPS, output_dir: str = "output") -> list[str]:
    """
    Busca N vídeos distintos do Pexels respeitando o bloqueio de 5 dias,
    processa cada um (hflip + 0.8x + sem metadados + 5s) e retorna
    lista de caminhos dos clipes prontos para concatenação.
    """
    os.makedirs(CLIP_DIR, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "tmp_raw"), exist_ok=True)

    tracking = _carregar_tracking()

    # IDs que NÃO podem ser usados ainda
    bloqueados = {
        vid_id for vid_id, data_uso in tracking.items()
        if not _video_disponivel(vid_id, tracking)
    }

    print(f"📋 Vídeos bloqueados (usados nos últimos {DIAS_BLOQUEIO} dias): {len(bloqueados)}")

    # Embaralha os termos de busca para variedade
    termos = TERMOS_BUSCA.copy()
    random.shuffle(termos)

    candidatos_todos: list[dict] = []
    ids_ja_selecionados: set     = set()

    for termo in termos:
        if len(candidatos_todos) >= n_clips * 3:
            break  # Pool suficiente
        novos = _buscar_videos_pexels(
            termo,
            excluir_ids=bloqueados | ids_ja_selecionados
        )
        for c in novos:
            if c["id"] not in ids_ja_selecionados and c["id"] not in bloqueados:
                candidatos_todos.append(c)
                ids_ja_selecionados.add(c["id"])

    if not candidatos_todos:
        # Fallback: ignora restrição de tempo se não houver candidatos
        print("⚠️  Pool de vídeos esgotado! Removendo restrição de 5 dias temporariamente...")
        tracking = {}
        for termo in termos[:5]:
            novos = _buscar_videos_pexels(termo, excluir_ids=set(), max_resultados=15)
            candidatos_todos.extend(novos)
        if not candidatos_todos:
            raise RuntimeError("Não foi possível encontrar vídeos no Pexels.")

    random.shuffle(candidatos_todos)
    selecionados = candidatos_todos[:n_clips]

    clips_prontos: list[str] = []

    for i, video in enumerate(selecionados, 1):
        vid_id   = video["id"]
        url      = video["url"]
        duracao  = video.get("duracao", 10)

        print(f"  [{i:02d}/{n_clips}] Processando vídeo #{vid_id} "
              f"({video['largura']}x{video['altura']})...")

        tmp_raw  = os.path.join(output_dir, "tmp_raw", f"raw_{vid_id}.mp4")
        clip_out = os.path.join(CLIP_DIR, f"clip_{i:02d}.mp4")

        try:
            # 1. Baixar
            _baixar_video(url, tmp_raw)

            # 2. Processar (hflip + 0.8x + sem metadados + cortar 5s)
            _processar_clip(tmp_raw, clip_out, duracao)

            # 3. Registrar uso
            _marcar_usado(str(vid_id), tracking)
            clips_prontos.append(clip_out)

            # Limpar arquivo raw
            if os.path.exists(tmp_raw):
                os.remove(tmp_raw)

        except Exception as e:
            print(f"    ⚠️  Falha ao processar vídeo #{vid_id}: {e}")
            if os.path.exists(tmp_raw):
                os.remove(tmp_raw)
            continue

    # Persistir tracking atualizado
    _salvar_tracking(tracking)

    if not clips_prontos:
        raise RuntimeError("Nenhum clipe foi processado com sucesso.")

    print(f"\n✅ {len(clips_prontos)} clipes prontos em: {CLIP_DIR}/")
    return clips_prontos


if __name__ == "__main__":
    clips = buscar_e_processar_clips()
    for c in clips:
        print(f"  • {c}")
