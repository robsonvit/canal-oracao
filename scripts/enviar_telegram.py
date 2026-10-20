"""
enviar_telegram.py
──────────────────
Envia a prévia completa da oração (thumbnail, título, descrição, tags e vídeo)
diretamente para o Telegram para aprovação prévia do usuário, sem postar no YouTube.
"""

import os
import sys
import json
import requests
import subprocess


def enviar_aprovacao_telegram(
    video_path: str,
    thumbnail_path: str,
    dados_oracao: dict,
    output_dir: str = "output"
) -> bool:
    """
    Envia todos os materiais da oração para o Telegram para aprovação do usuário.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("⚠️ TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não definidos.")
        return False

    titulo = dados_oracao.get("titulo", "Oração")
    salmo = dados_oracao.get("salmo", "")
    tema = dados_oracao.get("tema", "")
    descricao = dados_oracao.get("descricao", "")
    tags = dados_oracao.get("tags", [])

    base_url = f"https://api.telegram.org/bot{token}"

    print("\n📲 [TELEGRAM] Enviando materiais para aprovação...")

    # 1. Enviar Thumbnail com Título e Metadados
    if os.path.exists(thumbnail_path):
        caption_foto = (
            f"🙏 NOVA ORAÇÃO PRONTA PARA APROVAÇÃO\n\n"
            f"📌 Título:\n{titulo}\n\n"
            f"📖 Salmo: {salmo} — {tema}\n\n"
            f"⏳ Status: Aguardando sua aprovação para postar no YouTube."
        )
        print("   🖼️  Enviando Thumbnail...")
        with open(thumbnail_path, "rb") as foto:
            requests.post(
                f"{base_url}/sendPhoto",
                data={"chat_id": chat_id, "caption": caption_foto},
                files={"photo": foto},
                timeout=60
            )
        print("   ✅ Thumbnail enviada com sucesso!")

    # 2. Enviar a Descrição Completa e Tags em Mensagem de Texto
    print("   📝 Enviando Descrição completa...")
    texto_descricao = (
        f"📝 DESCRIÇÃO PROPOSTA PARA O YOUTUBE:\n\n"
        f"{descricao}\n\n"
        f"🏷️ TAGS:\n{', '.join(tags)}"
    )
    # Se exceder o limite do Telegram (4096 caracteres), divide em partes
    for i in range(0, len(texto_descricao), 4000):
        parte = texto_descricao[i : i + 4000]
        requests.post(
            f"{base_url}/sendMessage",
            json={"chat_id": chat_id, "text": parte},
            timeout=60
        )
    print("   ✅ Descrição enviada com sucesso!")

    # 3. Enviar o Vídeo para Visualização no Telegram
    if os.path.exists(video_path):
        tamanho_mb = os.path.getsize(video_path) / (1024 * 1024)
        print(f"   🎬 Preparando vídeo ({tamanho_mb:.1f} MB)...")

        video_para_enviar = video_path

        # Se o vídeo for maior que 48 MB, comprime uma versão leve em 480p para caber no limite de 50MB do Telegram Bot API
        if tamanho_mb > 48.0:
            preview_path = os.path.join(output_dir, "video_telegram.mp4")
            print(f"   ⚡ Vídeo tem {tamanho_mb:.1f} MB (limite do Telegram bot é 50 MB). Comprimindo preview leve...")
            cmd_preview = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", "scale=854:480",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "28",
                "-c:a", "aac",
                "-b:a", "96k",
                preview_path
            ]
            subprocess.run(cmd_preview, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            video_para_enviar = preview_path
            tamanho_mb = os.path.getsize(preview_path) / (1024 * 1024)
            print(f"   ✅ Preview compactado: {tamanho_mb:.1f} MB")

        caption_video = (
            f"🎥 VÍDEO COMPLETO PARA AVALIAÇÃO\n\n"
            f"📌 {titulo}\n\n"
            f"✨ Legendas centralizadas, áudio solene e trilha de fundo inclusos.\n"
            f"👉 Por favor, assista e confira se está tudo aprovado!"
        )

        print("   📤 Enviando vídeo para o Telegram...")
        with open(video_para_enviar, "rb") as vid:
            r = requests.post(
                f"{base_url}/sendVideo",
                data={
                    "chat_id": chat_id,
                    "caption": caption_video,
                    "supports_streaming": True
                },
                files={"video": vid},
                timeout=300
            )
            if r.json().get("ok"):
                print("   ✅ Vídeo enviado com sucesso ao Telegram!")
            else:
                print(f"   ⚠️ Resposta do Telegram ao enviar vídeo: {r.text}")

    print("🎉 [TELEGRAM] Todos os materiais foram enviados para aprovação!")
    return True


if __name__ == "__main__":
    import json
    with open("output/oracao.json", encoding="utf-8") as f:
        dados = json.load(f)
    enviar_aprovacao_telegram("output/video_final.mp4", "output/thumbnail.jpg", dados)
