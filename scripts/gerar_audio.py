"""
gerar_audio.py
──────────────
Gera áudio via Fish Audio API (voz clonada do projeto Criação vídeos Jesus)
com fallback automático para Kokoro TTS caso a API falhe ou fique sem créditos.
Produz um arquivo SRT de legendas usando Groq Whisper com timestamps precisos.
"""

import asyncio
import os
import re
import json
import subprocess
import requests
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─────────────────────────────────────────────────────────────────────────────
# Configurações Fish Audio (Voz Principal)
# ─────────────────────────────────────────────────────────────────────────────
FISH_API_KEY  = os.environ.get("FISH_API_KEY") or "sk-fish-5tG751PGMPWuTitwoavwJFCpYP7ZQv-g5HA3qI2lKMw"
FISH_VOICE_ID = os.environ.get("FISH_VOICE_ID") or "da20590a048f483986bf9986e6a87694"  # Voz Jesus
FISH_MODEL    = "s2.1-pro-free"
FISH_API_URL  = "https://api.fish.audio/v1/tts"

# ─────────────────────────────────────────────────────────────────────────────
# Configurações Kokoro (Fallback)
# ─────────────────────────────────────────────────────────────────────────────
KOKORO_VOICE = "pm_santa"
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


def _dividir_em_chunks(texto: str, max_chars: int = 1000) -> list[str]:
    """Divide o texto em blocos de parágrafos respeitando o limite máximo de caracteres."""
    paragrafos = [p.strip() for p in texto.split("\n") if p.strip()]
    chunks = []
    curr = []
    curr_len = 0
    for p in paragrafos:
        if curr_len + len(p) + 1 > max_chars and curr:
            chunks.append("\n\n".join(curr))
            curr = [p]
            curr_len = len(p)
        else:
            curr.append(p)
            curr_len += len(p) + 1
    if curr:
        chunks.append("\n\n".join(curr))
    return chunks


def _gerar_audio_fish(texto: str, output_path: str) -> None:
    """Gera áudio via Fish Audio API dividindo em chunks e concatenando via FFmpeg."""
    if not FISH_API_KEY:
        raise RuntimeError("FISH_API_KEY não definida.")

    chunks = _dividir_em_chunks(texto, max_chars=1000)
    print(f"🎙️  [Fish Audio] Gerando narração (Voz ID: {FISH_VOICE_ID}, {len(chunks)} blocos)...")

    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
        "model": FISH_MODEL,
    }

    work_dir = os.path.dirname(output_path) or "."
    temp_files = []
    concat_txt = os.path.join(work_dir, f"_fish_concat_{os.getpid()}.txt")

    try:
        for idx, chunk in enumerate(chunks):
            print(f"  [Fish Audio] Enviando bloco {idx+1}/{len(chunks)} ({len(chunk)} caracteres)...")
            payload = {
                "text": chunk,
                "reference_id": FISH_VOICE_ID,
                "format": "mp3",
                "mp3_bitrate": 192,
                "normalize": True,
                "latency": "normal",
            }
            resp = requests.post(FISH_API_URL, json=payload, headers=headers, timeout=120)
            if resp.status_code != 200:
                raise RuntimeError(f"Fish Audio retornou status {resp.status_code}: {resp.text[:300]}")

            chunk_file = os.path.join(work_dir, f"_fish_part_{os.getpid()}_{idx}.mp3")
            with open(chunk_file, "wb") as f:
                f.write(resp.content)
            temp_files.append(chunk_file)

        # Concatena partes geradas e converte para WAV 24kHz compatível
        with open(concat_txt, "w", encoding="utf-8") as f:
            for tf in temp_files:
                f.write(f"file '{os.path.abspath(tf).replace(os.sep, '/')}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_txt,
            "-c:a", "pcm_s16le",
            "-ar", "24000",
            output_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Erro ao concatenar partes de áudio do Fish Audio:\n{res.stderr}")
    finally:
        for tf in temp_files:
            if os.path.exists(tf):
                try:
                    os.remove(tf)
                except OSError:
                    pass
        if os.path.exists(concat_txt):
            try:
                os.remove(concat_txt)
            except OSError:
                pass


def _gerar_audio_kokoro(texto: str, output_path: str) -> None:
    """Gera áudio via Kokoro TTS (fallback local)."""
    print(f"🎙️  [Kokoro FALLBACK] Gerando áudio com Kokoro TTS (Voz: {KOKORO_VOICE})...")
    from kokoro import KPipeline
    import soundfile as sf
    import numpy as np

    pipeline = KPipeline(lang_code="p")
    generator = pipeline(texto, voice=KOKORO_VOICE, speed=1.0, split_pattern=r"\n+")

    audio_chunks = []
    for i, (gs, ps, audio) in enumerate(generator):
        audio_chunks.append(audio)

    if not audio_chunks:
        raise ValueError("Nenhum áudio gerado pelo Kokoro!")

    final_audio = np.concatenate(audio_chunks)
    sf.write(output_path, final_audio, 24000)


# ─────────────────────────────────────────────────────────────────────────────
# Geração principal (assíncrona)
# ─────────────────────────────────────────────────────────────────────────────
async def _gerar_async(texto: str, output_dir: str) -> tuple[str, str]:
    """Gera WAV + SRT de forma assíncrona com Fish Audio (e fallback Kokoro)."""
    
    audio_path = os.path.join(output_dir, "audio.wav")
    srt_path   = os.path.join(output_dir, "legendas.srt")

    # 1. Gerar áudio: Fish Audio como primário, Kokoro como fallback
    try:
        _gerar_audio_fish(texto, audio_path)
        fonte_usada = f"Fish Audio (Voz: {FISH_VOICE_ID})"
    except Exception as err_fish:
        print(f"\n⚠️  Fish Audio falhou: {err_fish}")
        print("🔄 Ativando fallback: Kokoro TTS local...\n")
        _gerar_audio_kokoro(texto, audio_path)
        fonte_usada = f"Kokoro FALLBACK ({KOKORO_VOICE})"

    # 2. Comprimir áudio para envio leve ao Groq Whisper (16kHz mono MP3 a 48kbps)
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
    
    # 3. Gerar legendas SRT precisas usando Groq Whisper
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
    print(f"✅ Fonte utilizada: {fonte_usada}")
    print(f"✅ Áudio gerado   : {audio_path}")
    print(f"✅ Legendas SRT   : {srt_path} ({num_legendas} blocos de legendas)")
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
