"""
obter_refresh_token.py
──────────────────────
EXECUTE APENAS UMA VEZ, LOCALMENTE no seu computador.

Este script abre o navegador para autenticação OAuth com o Google
e retorna o REFRESH TOKEN que você deve salvar como secret no GitHub.

Pré-requisitos:
  1. Criar projeto no Google Cloud Console: https://console.cloud.google.com/
  2. Habilitar "YouTube Data API v3"
  3. Criar credenciais OAuth 2.0 → Aplicativo para computador (Desktop)
  4. Baixar o arquivo client_secret.json OU digitar os dados manualmente

Uso:
    pip install google-auth-oauthlib
    python scripts/obter_refresh_token.py
"""

import json
import os
import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("❌ Instale: pip install google-auth-oauthlib")
    sys.exit(1)


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    print("\n" + "═"*60)
    print("  🔑  GERADOR DE REFRESH TOKEN — CANAL ORAÇÃO")
    print("═"*60)
    print()
    print("Você precisa das credenciais OAuth do Google Cloud.")
    print("Acesse: https://console.cloud.google.com/apis/credentials")
    print()

    # Verificar se existe client_secret.json na pasta
    client_secret_path = "client_secret.json"
    if os.path.exists(client_secret_path):
        print(f"✅ Arquivo '{client_secret_path}' encontrado!")
        usar_arquivo = input("Usar este arquivo? (s/n): ").strip().lower()
        if usar_arquivo != "s":
            client_secret_path = None
    else:
        client_secret_path = None

    if not client_secret_path:
        print("\nDigite as credenciais manualmente:")
        client_id     = input("  CLIENT_ID     : ").strip()
        client_secret = input("  CLIENT_SECRET : ").strip()

        client_config = {
            "installed": {
                "client_id":     client_id,
                "client_secret": client_secret,
                "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                "token_uri":     "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
        tmp_path = "_client_secrets_tmp.json"
        with open(tmp_path, "w") as f:
            json.dump(client_config, f)
        client_secret_path = tmp_path

    print("\n🌐 Abrindo navegador para autenticação...")
    print("   Faça login com a conta: robsonvitaacademico@gmail.com")
    print("   e conceda as permissões solicitadas.\n")

    try:
        flow  = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
        creds = flow.run_local_server(port=8080, prompt="consent", access_type="offline")
    finally:
        # Remover arquivo temporário se criado
        if os.path.exists("_client_secrets_tmp.json"):
            os.remove("_client_secrets_tmp.json")

    print("\n" + "═"*60)
    print("  ✅  AUTENTICAÇÃO CONCLUÍDA!")
    print("═"*60)
    print()
    print("Adicione estes valores como SECRETS no seu repositório GitHub:")
    print("  GitHub → Settings → Secrets and variables → Actions")
    print()
    print(f"  YOUTUBE_REFRESH_TOKEN  =  {creds.refresh_token}")

    # Tentar ler client_id/secret dos dados salvos
    try:
        with open(client_secret_path if os.path.exists(client_secret_path) else "_tmp") as f:
            dados = json.load(f)
        instalado = dados.get("installed", dados.get("web", {}))
        print(f"  YOUTUBE_CLIENT_ID      =  {instalado.get('client_id', '(do seu arquivo)')}")
        print(f"  YOUTUBE_CLIENT_SECRET  =  {instalado.get('client_secret', '(do seu arquivo)')}")
    except Exception:
        print("  YOUTUBE_CLIENT_ID      =  (veja seu Google Cloud Console)")
        print("  YOUTUBE_CLIENT_SECRET  =  (veja seu Google Cloud Console)")

    print()
    print("  GROQ_API_KEY           =  (sua chave do groq api)")
    print("  PEXELS_API_KEY         =  (sua chave gratuita em pexels.com/api)")
    print()
    print("═"*60)

    # Salvar também em arquivo local para referência
    saida = {
        "YOUTUBE_REFRESH_TOKEN": creds.refresh_token,
        "AVISO": "NÃO COMMITE ESTE ARQUIVO! Adicione ao .gitignore.",
    }
    with open("refresh_token_PRIVADO.json", "w") as f:
        json.dump(saida, f, indent=2)
    print("\n💾 Refresh token salvo em: refresh_token_PRIVADO.json (NÃO compartilhe!)")


if __name__ == "__main__":
    main()
