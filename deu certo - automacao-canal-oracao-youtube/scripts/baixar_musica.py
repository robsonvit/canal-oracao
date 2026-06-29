import os
import requests

def baixar_musica():
    # URL de How Beautiful (piano cover) do BaptistMusic no Archive.org
    url = "https://archive.org/download/BaptistMusic/How%20Beautiful%20-%20piano%20instrumental%20cover%20with%20lyrics.mp3"
    dest = "data/bg_music.mp3"
    
    if os.path.exists(dest):
        print(f"Musica de fundo ja existe em: {dest}")
        return True
        
    os.makedirs("data", exist_ok=True)
    print(f"Baixando musica de fundo de: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        r = requests.get(url, headers=headers, stream=True, timeout=30)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Musica de fundo (MP3) salva com sucesso em: {dest}")
        return True
    except Exception as e:
        print(f"Erro ao baixar musica de fundo: {e}")
        return False

if __name__ == "__main__":
    baixar_musica()
