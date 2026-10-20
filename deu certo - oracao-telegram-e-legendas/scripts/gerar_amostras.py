import asyncio
import edge_tts
import os

async def gerar_amostras():
    texto = "Olá! Este é um teste da voz para o canal de oração. Estamos verificando a velocidade e o tom da narração para que ela fique perfeita e transmita paz."
    
    configuracoes = [
        ("antonio_atual_15", "pt-BR-AntonioNeural", "-15%"),
        ("antonio_lento_20", "pt-BR-AntonioNeural", "-20%"),
        ("antonio_lento_25", "pt-BR-AntonioNeural", "-25%"),
        ("duarte_lento_15", "pt-PT-DuarteNeural", "-15%"),
        ("duarte_lento_20", "pt-PT-DuarteNeural", "-20%"),
    ]
    
    output_dir = "output/amostras"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Gerando amostras de audio...")
    for nome, voz, rate in configuracoes:
        path = os.path.join(output_dir, f"{nome}.mp3")
        communicate = edge_tts.Communicate(texto, voz, rate=rate)
        await communicate.save(path)
        print(f"Gerado: {path} (Voz: {voz}, Velocidade: {rate})")

if __name__ == "__main__":
    asyncio.run(gerar_amostras())
