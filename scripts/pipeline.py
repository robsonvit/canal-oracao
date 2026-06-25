"""
pipeline.py
───────────
Orquestrador principal do Canal Oração.
Executa todos os passos em sequência e reporta o progresso.

Uso:
    python scripts/pipeline.py
"""

import os
import sys
import json
import traceback

# Garante que o diretório raiz do projeto esteja no path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

OUTPUT_DIR = os.path.join(ROOT_DIR, "output")


def _titulo(passo: int, total: int, descricao: str):
    print(f"\n{'─'*60}")
    print(f" PASSO {passo}/{total}: {descricao}")
    print(f"{'─'*60}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(ROOT_DIR, "data"), exist_ok=True)

    print("\n" + "═"*60)
    print("  🙏  CANAL ORAÇÃO — PIPELINE AUTOMÁTICO")
    print("═"*60)

    # ──────────────────────────────────────────────────────────────
    # PASSO 1 — Gerar texto da oração com Groq AI
    # ──────────────────────────────────────────────────────────────
    _titulo(1, 6, "Gerando oração com Groq AI (llama-3.3-70b)...")
    from scripts.gerar_oracao import gerar_oracao

    dados = gerar_oracao()
    oracao_json = os.path.join(OUTPUT_DIR, "oracao.json")
    with open(oracao_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    palavras = len(dados["oracao_texto"].split())
    print(f"✅ Salmo {dados['salmo']} — {dados['tema']}")
    print(f"   Título  : {dados['titulo']}")
    print(f"   Palavras: {palavras}")

    # ──────────────────────────────────────────────────────────────
    # PASSO 2 — Gerar áudio TTS e legendas SRT
    # ──────────────────────────────────────────────────────────────
    _titulo(2, 6, "Gerando áudio TTS grave e legendas (edge-tts)...")
    from scripts.gerar_audio import gerar as gerar_audio

    audio_path, srt_path = gerar_audio(dados["oracao_texto"], OUTPUT_DIR)

    # ──────────────────────────────────────────────────────────────
    # PASSO 3 — Buscar e processar clipes de vídeo (Pexels)
    # ──────────────────────────────────────────────────────────────
    _titulo(3, 6, "Buscando e processando clipes de vídeo (Pexels)...")
    from scripts.buscar_video import buscar_e_processar_clips

    clips = buscar_e_processar_clips(n_clips=12, output_dir=OUTPUT_DIR)
    print(f"✅ {len(clips)} clipes prontos (5s × 0.8x = 6.25s cada)")

    # ──────────────────────────────────────────────────────────────
    # PASSO 4 — Gerar thumbnail
    # ──────────────────────────────────────────────────────────────
    _titulo(4, 6, "Gerando thumbnail personalizada (Pillow)...")
    from scripts.gerar_capa import gerar_thumbnail

    thumbnail_path = gerar_thumbnail(
        dados["salmo"],
        dados["tema"],
        dados["titulo"],
        OUTPUT_DIR,
    )

    # ──────────────────────────────────────────────────────────────
    # PASSO 5 — Montar vídeo final com FFmpeg
    # ──────────────────────────────────────────────────────────────
    _titulo(5, 6, "Montando vídeo final 1920×1080 (FFmpeg)...")
    from scripts.montar_video import montar_video

    video_final = montar_video(
        clips       = clips,
        audio_path  = audio_path,
        legendas_srt= srt_path,
        output_dir  = OUTPUT_DIR,
    )

    # ──────────────────────────────────────────────────────────────
    # PASSO 6 — Upload para o YouTube
    # ──────────────────────────────────────────────────────────────
    _titulo(6, 6, "Publicando no YouTube...")

    if not os.environ.get("YOUTUBE_REFRESH_TOKEN"):
        print("⚠️  YOUTUBE_REFRESH_TOKEN não configurado.")
        print("   Configure o secret no GitHub e rode novamente.")
        print(f"\n   Vídeo salvo localmente em: {video_final}")
    else:
        from scripts.upload_youtube import upload_youtube
        video_id = upload_youtube(video_final, thumbnail_path, dados)
        print(f"\n🎉 PIPELINE CONCLUÍDO COM SUCESSO!")
        print(f"   📺 https://www.youtube.com/watch?v={video_id}")

    print("\n" + "═"*60)
    print("  📁 Arquivos gerados:")
    for nome in ["oracao.json", "audio.mp3", "legendas.srt", "thumbnail.jpg", "video_final.mp4"]:
        caminho = os.path.join(OUTPUT_DIR, nome)
        if os.path.exists(caminho):
            tamanho = os.path.getsize(caminho)
            print(f"     {nome:<22} {tamanho/1024:.0f} KB")
    print("═"*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        traceback.print_exc()
        sys.exit(1)
