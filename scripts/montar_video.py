"""
montar_video.py
───────────────
Monta o vídeo final 1920×1080 a partir de:
  • Lista de clipes já processados (hflip + 0.8x + sem metadados)
  • Áudio TTS grave em MP3
  • Legendas SRT centralizadas no estilo da referência

Processo:
  1. Cria arquivo de lista de concatenação FFmpeg
  2. Concatena todos os clipes em um vídeo-base
  3. Faz loop do vídeo-base para cobrir a duração total do áudio
  4. Sobrepõe legendas centralizadas (fonte serif branca, borda preta)
  5. Mistura com o áudio TTS
  6. Exporta video_final.mp4 em H.264/AAC 1920×1080
"""

import os
import json
import subprocess
import re


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _duracao_audio(audio_path: str) -> float:
    """Retorna a duração do áudio em segundos via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        audio_path,
    ]
    resultado = subprocess.run(cmd, capture_output=True, text=True)
    try:
        dados = json.loads(resultado.stdout)
        return float(dados["format"]["duration"])
    except Exception:
        raise RuntimeError(f"Não foi possível obter duração de: {audio_path}")


def _duracao_video(video_path: str) -> float:
    """Retorna a duração do vídeo em segundos via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        video_path,
    ]
    resultado = subprocess.run(cmd, capture_output=True, text=True)
    try:
        dados    = json.loads(resultado.stdout)
        streams  = dados.get("streams", [])
        for s in streams:
            if s.get("codec_type") == "video" and "duration" in s:
                return float(s["duration"])
        return 0.0
    except Exception:
        return 0.0


def _criar_concat_list(clips: list[str], lista_path: str):
    """Cria o arquivo de lista .txt para o demuxer concat do FFmpeg."""
    with open(lista_path, "w", encoding="utf-8") as f:
        for clip in clips:
            # FFmpeg no Linux exige / e não backslash
            caminho = clip.replace("\\", "/")
            f.write(f"file '{caminho}'\n")


def _escape_srt_path(path: str) -> str:
    """Escapa o caminho do SRT para uso no filtro subtitles do FFmpeg."""
    # No Linux (Actions), barras normais; escapar ':' no Windows não é necessário
    path = path.replace("\\", "/")
    # Escapa : somente se houver letra de drive (Windows)
    path = re.sub(r"^([A-Za-z]):", r"\1\\:", path)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# Função principal
# ─────────────────────────────────────────────────────────────────────────────
def montar_video(
    clips: list[str],
    audio_path: str,
    legendas_srt: str,
    output_dir: str = "output",
) -> str:
    """
    Monta o vídeo final e retorna o caminho de output/video_final.mp4.

    clips        → lista de arquivos MP4 já processados (5s × 0.8x cada)
    audio_path   → MP3 gerado pelo TTS
    legendas_srt → arquivo SRT com timestamps
    output_dir   → pasta de saída
    """
    os.makedirs(output_dir, exist_ok=True)

    duracao_audio = _duracao_audio(audio_path)
    print(f"⏱️  Duração do áudio : {duracao_audio:.1f}s ({duracao_audio/60:.1f} min)")
    print(f"🎬 Clipes disponíveis: {len(clips)} × ~6.25s cada")

    # ── Passo 1: Concatenar clipes em vídeo-base ─────────────────────────────
    lista_concat = os.path.join(output_dir, "concat_list.txt")
    video_base   = os.path.join(output_dir, "video_base.mp4")

    _criar_concat_list(clips, lista_concat)

    print("🔗 Concatenando clipes...")
    cmd_concat = [
        "ffmpeg", "-y",
        "-f",    "concat",
        "-safe", "0",
        "-i",    lista_concat,
        "-c",    "copy",
        "-an",
        video_base,
    ]
    r = subprocess.run(cmd_concat, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Falha na concatenação:\n{r.stderr[-500:]}")

    duracao_base = _duracao_video(video_base)
    print(f"   Vídeo-base: {duracao_base:.1f}s")

    # ── Passo 2: Montar vídeo final com loop + áudio + legendas ──────────────
    output_path = os.path.join(output_dir, "video_final.mp4")

    # Estilo das legendas: fonte serif, branca, borda preta, CENTRO DA TELA
    # Alignment=5 no padrão ASS = centro absoluto (h e v)
    subtitle_style = ",".join([
        "Fontname=DejaVu Serif",
        "FontSize=60",
        "Bold=1",
        "PrimaryColour=&H00FFFFFF",   # Branco
        "OutlineColour=&H00000000",   # Preto
        "BackColour=&H60000000",      # Sombra suave
        "Outline=3",
        "Shadow=2",
        "Alignment=5",                # Centro da tela (horizontal + vertical)
        "MarginV=0",
        "MarginL=80",
        "MarginR=80",
    ])

    srt_escaped = _escape_srt_path(legendas_srt)

    print(f"🎞️  Montando vídeo final (duração alvo: {duracao_audio:.0f}s)...")

    cmd_final = [
        "ffmpeg", "-y",

        # Input 1: Vídeo-base em loop (para cobrir toda a duração)
        "-stream_loop", "-1",
        "-i", video_base,

        # Input 2: Áudio TTS
        "-i", audio_path,

        # Duração = duração do áudio
        "-t", str(duracao_audio),

        # Mapear vídeo do input 0 e áudio do input 1
        "-map", "0:v:0",
        "-map", "1:a:0",

        # Filtros de vídeo: escurecimento leve + legendas centralizadas
        "-vf",
        (
            "eq=brightness=-0.04:contrast=1.03,"
            f"subtitles='{srt_escaped}':force_style='{subtitle_style}'"
        ),

        # Codec vídeo
        "-c:v",    "libx264",
        "-preset", "fast",
        "-crf",    "22",
        "-pix_fmt", "yuv420p",

        # Codec áudio
        "-c:a",  "aac",
        "-b:a",  "192k",

        # Remover metadados do vídeo final também
        "-map_metadata", "-1",

        output_path,
    ]

    resultado = subprocess.run(cmd_final, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise RuntimeError(f"FFmpeg falhou na montagem final:\n{resultado.stderr[-600:]}")

    tamanho_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅ Vídeo final: {output_path}  ({tamanho_mb:.1f} MB)")
    return output_path


if __name__ == "__main__":
    import glob
    clips = sorted(glob.glob("output/clips/clip_*.mp4"))
    montar_video(clips, "output/audio.mp3", "output/legendas.srt")
