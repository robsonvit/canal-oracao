import asyncio
import edge_tts

async def test():
    # Testando com pitch (tom mais grave) e rate (velocidade mais lenta)
    # pitch="-10Hz" deixa a voz mais grave, rate="-20%" deixa mais lenta/pausada
    try:
        c = edge_tts.Communicate("Olá, este é um teste com a voz mais grave e pausada.", "pt-BR-AntonioNeural", rate="-20%", pitch="-10Hz")
        await c.save("output/test_grave.mp3")
        print("Sucesso! Audio gerado em output/test_grave.mp3")
    except Exception as e:
        print(f"Erro: {e}")

asyncio.run(test())
