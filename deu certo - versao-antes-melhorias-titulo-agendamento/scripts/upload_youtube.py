"""
upload_youtube.py
─────────────────
Faz upload do vídeo gerado para o YouTube via YouTube Data API v3
usando credenciais OAuth 2.0 (refresh token).

Secrets necessários no GitHub (Settings → Secrets → Actions):
  YOUTUBE_CLIENT_ID
  YOUTUBE_CLIENT_SECRET
  YOUTUBE_REFRESH_TOKEN
"""

import os
import json

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


def upload_youtube(
    video_path: str,
    thumbnail_path: str,
    metadata: dict,
) -> str:
    """
    Faz upload do vídeo e da thumbnail para o YouTube.
    Retorna o ID do vídeo publicado.
    """
    creds   = _obter_credenciais()
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

    # ── Metadados do vídeo ───────────────────────────────────────────────────
    titulo     = metadata.get("titulo", "Oração Poderosa — Canal Oração")[:100]
    descricao  = metadata.get("descricao", "")[:5000]
    tags       = metadata.get("tags", [])

    body = {
        "snippet": {
            "title":           titulo,
            "description":     descricao,
            "tags":            tags,
            "categoryId":      "22",      # People & Blogs
            "defaultLanguage": "pt-BR",
            "defaultAudioLanguage": "pt-BR",
        },
        "status": {
            "privacyStatus":            "public",
            "selfDeclaredMadeForKids":  False,
            "madeForKids":              False,
        },
    }

    # ── Upload do vídeo ──────────────────────────────────────────────────────
    print(f"📤 Iniciando upload para o YouTube...")
    print(f"   Título : {titulo}")

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
    print(f"\n✅ Vídeo publicado: https://www.youtube.com/watch?v={video_id}")

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
