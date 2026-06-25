"""
gerar_audio.py
──────────────
Gera áudio MP3 com voz grave masculina (pt-BR-AntonioNeural) via edge-tts
e produz um arquivo SRT de legendas com timestamps de palavras agrupadas.
"""

import asyncio
import os
import re
import json

import edge_tts


# ─────────────────────────────────────────────────────────────────────────────
# Configurações da voz
# ─────────────────────────────────────────────────────────────────────────────
VOZ          = "pt-BR-AntonioNeural"   # Voz masculina natural do Brasil
PITCH        = "-10Hz"                 # Grave (mais profundo)
RATE         = "-8%"                   # Ritmo levemente mais lento (solene)
PALAVRAS_POR_LEGENDA = 7              # Palavras por bloco de legenda


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de formatação SRT
# ─────────────────────────────────────────────────────────────────────────────
def _ticks_para_hms(ticks: int) -> str:
    """Converte ticks de 100ns → HH:MM:SS,mmm (formato SRT)."""
    ms_total = ticks // 10_000
    horas    = ms_total // 3_600_000
    ms_total %= 3_600_000
    minutos  = ms_total // 60_000
    ms_total %= 60_000
    segundos = ms_total // 1_000
    ms       = ms_total % 1_000
    return f"{horas:02d}:{minutos:02d}:{segundos:02d},{ms:03d}"


def _agrupar_palavras_srt(word_boundaries: list, n: int = PALAVRAS_POR_LEGENDA) -> str:
    """
    Agrupa word boundaries em blocos de `n` palavras e gera conteúdo SRT.
    word_boundaries: lista de dicts com 'offset', 'duration', 'text'
    """
    if not word_boundaries:
        return ""

    linhas_srt = []
    idx = 1

    for i in range(0, len(word_boundaries), n):
        grupo = word_boundaries[i: i + n]
        inicio_ticks = grupo[0]["offset"]
        fim_ticks    = grupo[-1]["offset"] + grupo[-1]["duration"]
        texto        = " ".join(w["text"] for w in grupo)

        linhas_srt.append(
            f"{idx}\n"
            f"{_ticks_para_hms(inicio_ticks)} --> {_ticks_para_hms(fim_ticks)}\n"
            f"{texto}\n"
        )
        idx += 1

    return "\n".join(linhas_srt)


# ─────────────────────────────────────────────────────────────────────────────
# Geração principal (assíncrona)
# ─────────────────────────────────────────────────────────────────────────────
async def _gerar_async(texto: str, output_dir: str) -> tuple[str, str]:
    """Gera MP3 + SRT de forma assíncrona."""
    communicate = edge_tts.Communicate(texto, VOZ, pitch=PITCH, rate=RATE)

    audio_path = os.path.join(output_dir, "audio.mp3")
    srt_path   = os.path.join(output_dir, "legendas.srt")

    word_boundaries = []

    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_boundaries.append({
                    "text":     chunk["text"],
                    "offset":   chunk["offset"],    # ticks de 100ns
                    "duration": chunk["duration"],  # ticks de 100ns
                })

    # Gerar SRT agrupado
    srt_content = _agrupar_palavras_srt(word_boundaries, PALAVRAS_POR_LEGENDA)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    print(f"✅ Áudio gerado : {audio_path}")
    print(f"✅ Legendas SRT : {srt_path}  ({len(word_boundaries)} palavras)")
    return audio_path, srt_path


# ─────────────────────────────────────────────────────────────────────────────
# Interface pública
# ─────────────────────────────────────────────────────────────────────────────
def gerar(texto: str, output_dir: str = "output") -> tuple[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    return asyncio.run(_gerar_async(texto, output_dir))


if __name__ == "__main__":
    with open("output/oracao.json", encoding="utf-8") as f:
        data = json.load(f)
    gerar(data["oracao_texto"])
