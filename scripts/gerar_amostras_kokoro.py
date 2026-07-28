import os
import soundfile as sf
import numpy as np
from kokoro import KPipeline

def gerar_amostras_kokoro():
    texto = "Olá! Este é um teste da voz para o canal de oração. Estamos verificando a velocidade e o tom da narração para que ela fique perfeita e transmita paz."
    
    # Caminho absoluto para garantir que salve no lugar certo
    base_dir = r"c:\#1-CRIAÇÕES-AUTOMAÇÕES-EXTENSÕES\CANAL ORAÇÃO"
    output_dir = os.path.join(base_dir, "output", "amostras_kokoro")
    os.makedirs(output_dir, exist_ok=True)
    
    print("Iniciando KPipeline para Portugues ('p')...")
    pipeline = KPipeline(lang_code='p')
    
    # pm_santa e pm_alex sao masculinas. pf_dora e pf_julia sao femininas
    vozes_para_testar = ["pm_santa", "pm_alex", "pf_dora", "pf_julia"]
    
    for voz in vozes_para_testar:
        print(f"\nTentando gerar amostra com a voz: {voz}")
        try:
            generator = pipeline(texto, voice=voz, speed=1.0, split_pattern=r'\n+')
            audio_chunks = []
            for i, (gs, ps, audio) in enumerate(generator):
                audio_chunks.append(audio)
            
            if audio_chunks:
                final_audio = np.concatenate(audio_chunks)
                path = os.path.join(output_dir, f"{voz}.wav")
                sf.write(path, final_audio, 24000)
                print(f"Gerado com sucesso: {path}")
        except Exception as e:
            print(f"Falha ao gerar voz {voz}: {e}")

if __name__ == "__main__":
    gerar_amostras_kokoro()
