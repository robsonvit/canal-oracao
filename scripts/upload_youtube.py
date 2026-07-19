"""
upload_youtube.py
─────────────────
Faz upload do vídeo gerado para o YouTube via YouTube Data API v3
usando credenciais OAuth 2.0 (refresh token).

Novidades desta versão:
  ✅ Renomeia o arquivo de vídeo com o título antes do upload
  ✅ Agenda a publicação para 30 min após a conclusão (arredondado)
  ✅ Tags combinadas: fixas do canal + concorrentes (limite 500 chars)
  ✅ Marcado explicitamente como NÃO É PARA CRIANÇAS

Secrets necessários no GitHub (Settings → Secrets → Actions):
  YOUTUBE_CLIENT_ID
  YOUTUBE_CLIENT_SECRET
  YOUTUBE_REFRESH_TOKEN
  YOUTUBE_API_KEY         ← chave pública para pesquisa de títulos
"""

import os
import re
import json
from datetime import datetime, timezone, timedelta

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


def _obter_credenciais() -> Credentials:
    """Constrói credenciais OAuth a partir dos secrets do ambiente."""
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    # Força refresh do access token
    creds.refresh(Request())
    return creds


def _calcular_horario_agendamento() -> str:
    """
    Calcula o horário de agendamento: now() + 30 min, arredondado para
    a próxima meia hora exata (ex: 18:47 → 19:00 | 19:12 → 19:30).

    Retorna string no formato ISO 8601 UTC para a YouTube API.
    """
    agora = datetime.now(timezone.utc)
    agendado = agora + timedelta(minutes=30)

    minutos = agendado.minute
    if minutos < 30:
        # Arredonda para :30 da hora atual
        agendado = agendado.replace(minute=30, second=0, microsecond=0)
    else:
        # Arredonda para :00 da próxima hora
        agendado = agendado.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    return agendado.strftime("%Y-%m-%dT%H:%M:%S.000Z"), agendado


def _sanitizar_nome_arquivo(titulo: str) -> str:
    """
    Converte o título em um nome de arquivo seguro para Windows/Linux.
    Remove caracteres inválidos e limita a 80 caracteres.
    """
    nome = re.sub(r'[\\/*?:"<>|#]', '', titulo)   # Remove chars inválidos
    nome = re.sub(r'\s+', '_', nome.strip())       # Espaços → underscores
    nome = re.sub(r'_{2,}', '_', nome)             # Remove underscores duplos
    nome = nome[:80].rstrip('_')                   # Limita tamanho
    return nome + ".mp4"


def _renomear_video(video_path: str, titulo: str) -> str:
    """
    Renomeia o arquivo de vídeo com o título sanitizado.
    Retorna o novo caminho do arquivo.
    """
    diretorio = os.path.dirname(video_path)
    novo_nome = _sanitizar_nome_arquivo(titulo)
    novo_path = os.path.join(diretorio, novo_nome)

    if os.path.exists(novo_path) and novo_path != video_path:
        os.remove(novo_path)  # Remove versão anterior se existir

    os.rename(video_path, novo_path)
    print(f"   📁 Arquivo renomeado: {novo_nome}")
    return novo_path


def upload_youtube(
    video_path: str,
    thumbnail_path: str,
    metadata: dict,
) -> str:
    """
    Faz upload do vídeo e da thumbnail para o YouTube.
    Agenda a publicação para 30 minutos após o horário atual (arredondado).
    Retorna o ID do vídeo criado.
    """
    creds   = _obter_credenciais()
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

    # ── Metadados do vídeo ───────────────────────────────────────────────────
    titulo    = metadata.get("titulo", "Oração Poderosa — Canal Oração")[:100]
    descricao = metadata.get("descricao", "")[:5000]
    tags      = metadata.get("tags", [])

    # ── Renomear arquivo de vídeo com o título ───────────────────────────────
    if os.path.exists(video_path):
        video_path = _renomear_video(video_path, titulo)

    # ── Calcular horário de agendamento ──────────────────────────────────────
    publish_at_str, publish_at_dt = _calcular_horario_agendamento()
    hora_local = publish_at_dt.strftime("%d/%m/%Y às %H:%M UTC")

    # ── Montar body da requisição ────────────────────────────────────────────
    body = {
        "snippet": {
            "title":              titulo,
            "description":        descricao,
            "tags":               tags,
            "categoryId":         "22",       # People & Blogs
            "defaultLanguage":    "pt-BR",
            "defaultAudioLanguage": "pt-BR",
        },
        "status": {
            "privacyStatus":            "private",   # OBRIGATÓRIO para agendamento
            "publishAt":                publish_at_str,
            "selfDeclaredMadeForKids":  False,
            "madeForKids":              False,
            "containsSyntheticMedia":   False,
        },
    }

    # ── Upload do vídeo ──────────────────────────────────────────────────────
    print(f"📤 Iniciando upload para o YouTube...")
    print(f"   Título    : {titulo}")
    print(f"   Tags      : {len(tags)} tags")
    print(f"   Agendado  : {hora_local}")
    print(f"   Crianças  : NÃO (selfDeclaredMadeForKids=False)")

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024,  # 10 MB por chunk
    )

    request  = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"   Upload: {pct}%", end="\r")

    video_id = response.get("id", "")
    print(f"\n✅ Vídeo agendado! ID: {video_id}")
    print(f"   🕐 Publicação agendada para: {hora_local}")
    print(f"   📺 https://www.youtube.com/watch?v={video_id}")

    # ── Upload da thumbnail ──────────────────────────────────────────────────
    if video_id and os.path.exists(thumbnail_path):
        print("🖼️  Enviando thumbnail personalizada...")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
            ).execute()
            print("✅ Thumbnail definida com sucesso!")
        except Exception as e:
            print(f"⚠️  Falha ao definir thumbnail: {e}")

    return video_id


if __name__ == "__main__":
    with open("output/oracao.json", encoding="utf-8") as f:
        data = json.load(f)
    upload_youtube("output/video_final.mp4", "output/thumbnail.jpg", data)
