"""
gerar_audio.py
──────────────
Gera áudio WAV via Kokoro TTS e produz um arquivo SRT de legendas
usando Groq Whisper com timestamps precisos.
"""

import asyncio
import os
import re
import json
import subprocess

# ─────────────────────────────────────────────────────────────────────────────
# Configurações da voz
# ─────────────────────────────────────────────────────────────────────────────
VOZ = "pm_santa"   # Voz masculina do Kokoro
PALAVRAS_POR_LEGENDA = 5      # Palavras por bloco de legenda para não estourar a tela


def _segundos_para_hms(segundos: float) -> str:
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    ms = int(round((segundos - int(segundos)) * 1000))
    return f"{horas:02d}:{minutos:02d}:{segs:02d},{ms:03d}"


def _gerar_srt_fallback(texto: str, audio_path: str, chunk_size: int = 5) -> str:
    """Gera SRT distribuindo o texto ao longo da duração total do áudio caso o Whisper falhe."""
    try:
        import soundfile as sf
        duracao = sf.info(audio_path).duration
    except Exception:
        duracao = 450.0

    palavras = texto.strip().split()
    if not palavras:
        return "1\n00:00:00,000 --> 00:00:05,000\nOração\n"

    tempo_por_palavra = duracao / max(len(palavras), 1)
    linhas = []
    idx = 1
    for i in range(0, len(palavras), chunk_size):
        chunk = palavras[i : i + chunk_size]
        chunk_start = i * tempo_por_palavra
        chunk_end = min((i + len(chunk)) * tempo_por_palavra, duracao)
        inicio = _segundos_para_hms(chunk_start)
        fim = _segundos_para_hms(chunk_end)
        linhas.append(f"{idx}\n{inicio} --> {fim}\n{' '.join(chunk)}\n")
        idx += 1
    return "\n".join(linhas)


# ─────────────────────────────────────────────────────────────────────────────
# Geração principal (assíncrona)
# ─────────────────────────────────────────────────────────────────────────────
async def _gerar_async(texto: str, output_dir: str) -> tuple[str, str]:
    """Gera WAV + SRT de forma assíncrona."""
    
    audio_path = os.path.join(output_dir, "audio.wav")
    srt_path   = os.path.join(output_dir, "legendas.srt")

    print(f"🎙️  Gerando áudio com Kokoro TTS (Voz: {VOZ})...")
    from kokoro import KPipeline
    import soundfile as sf
    import numpy as np

    # 'p' para Português do Brasil
    pipeline = KPipeline(lang_code='p')
    
    # Speed 1.0 (mantemos um ritmo solene)
    generator = pipeline(texto, voice=VOZ, speed=1.0, split_pattern=r'\n+')
    
    audio_chunks = []
    for i, (gs, ps, audio) in enumerate(generator):
        audio_chunks.append(audio)
        
    if not audio_chunks:
        raise ValueError("Nenhum áudio gerado pelo Kokoro!")
        
    final_audio = np.concatenate(audio_chunks)
    sf.write(audio_path, final_audio, 24000)

    # 1. Comprimir áudio para envio leve ao Groq Whisper (16kHz mono MP3 a 48kbps)
    # audio.wav de 7 a 10 min tem ~30MB. A Groq tem limite estrito de 25MB por arquivo.
    # Convertendo para MP3 16kHz mono a 48kbps, um áudio de 10 min fica com apenas ~3.6MB!
    whisper_audio_path = os.path.join(output_dir, "audio_whisper.mp3")
    print("🔄 Comprimindo áudio para Groq Whisper (16kHz mono 48kbps)...")
    cmd_compress = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "48k",
        whisper_audio_path
    ]
    res_compress = subprocess.run(cmd_compress, capture_output=True, text=True)
    arquivo_para_whisper = whisper_audio_path if (res_compress.returncode == 0 and os.path.exists(whisper_audio_path)) else audio_path

    from groq import Groq
    
    # 2. Gerar legendas SRT precisas usando Groq Whisper
    print("🎙️  Gerando legendas com Groq Whisper...")
    cliente_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    try:
        ext = os.path.splitext(arquivo_para_whisper)[1].lower()
        nome_envio = "audio.mp3" if ext == ".mp3" else "audio.wav"
        with open(arquivo_para_whisper, "rb") as f:
            transcricao = cliente_groq.audio.transcriptions.create(
                file=(nome_envio, f.read()),
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
                language="pt"
            )
            
        linhas_srt = []
        # No SDK da Groq, transcricao pode ser dict ou objeto
        segmentos = transcricao.get("segments", []) if isinstance(transcricao, dict) else transcricao.segments
        
        idx = 1
        for segment in segmentos:
            try:
                start = segment.start
                end = segment.end
                text = segment.text
            except AttributeError:
                start = segment["start"]
                end = segment["end"]
                text = segment["text"]
                
            palavras = text.strip().split()
            if not palavras:
                continue
                
            # Interpolação linear de tempo para dividir frases longas em blocos de X palavras
            chunk_size = PALAVRAS_POR_LEGENDA
            duracao_total = end - start
            tempo_por_palavra = duracao_total / len(palavras)
            
            for i in range(0, len(palavras), chunk_size):
                chunk = palavras[i : i + chunk_size]
                chunk_text = " ".join(chunk)
                
                chunk_start = start + (i * tempo_por_palavra)
                chunk_end = start + ((i + len(chunk)) * tempo_por_palavra)
                
                inicio = _segundos_para_hms(chunk_start)
                fim = _segundos_para_hms(chunk_end)
                linhas_srt.append(f"{idx}\n{inicio} --> {fim}\n{chunk_text}\n")
                idx += 1
            
        srt_content = "\n".join(linhas_srt)
        
        if not srt_content.strip():
            raise ValueError("Groq retornou legenda vazia")
    except Exception as e:
        print(f"⚠️ Erro ao transcrever com Groq: {e}. Usando fallback inteligente.")
        srt_content = _gerar_srt_fallback(texto, audio_path, PALAVRAS_POR_LEGENDA)

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    num_legendas = srt_content.count("-->")
    print(f"✅ Áudio gerado : {audio_path}")
    print(f"✅ Legendas SRT : {srt_path} ({num_legendas} blocos de legendas)")
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

