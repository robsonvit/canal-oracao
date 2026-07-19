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

# ─────────────────────────────────────────────────────────────────────────────
# Configurações da voz
# ─────────────────────────────────────────────────────────────────────────────
VOZ = "pm_santa"   # Voz masculina do Kokoro
PALAVRAS_POR_LEGENDA = 5      # Palavras por bloco de legenda para não estourar a tela


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

    def _segundos_para_hms(segundos: float) -> str:
        horas = int(segundos // 3600)
        minutos = int((segundos % 3600) // 60)
        segs = int(segundos % 60)
        ms = int(round((segundos - int(segundos)) * 1000))
        return f"{horas:02d}:{minutos:02d}:{segs:02d},{ms:03d}"

    from groq import Groq
    
    # 2. Gerar legendas SRT precisas usando Groq Whisper (muito mais confiável que word_boundaries do edge-tts)
    print("🎙️  Gerando legendas com Groq Whisper...")
    cliente_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    try:
        with open(audio_path, "rb") as f:
            transcricao = cliente_groq.audio.transcriptions.create(
                file=("audio.wav", f.read()),
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
        print(f"⚠️ Erro ao transcrever com Groq: {e}. Usando fallback.")
        srt_content = "1\n00:00:00,000 --> 00:00:05,000\n \n"

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    print(f"✅ Áudio gerado : {audio_path}")
    print(f"✅ Legendas SRT : {srt_path}")
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
