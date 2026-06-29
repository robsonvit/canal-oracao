import os
import json
import random
import datetime

from groq import Groq

# ─────────────────────────────────────────────────────────────────────────────
# Base de dados de salmos temáticos (rotação automática por dia do ano)
# ─────────────────────────────────────────────────────────────────────────────
SALMOS = [
    {"numero": "23",  "tema": "O Senhor é Meu Pastor",        "keys": "provisão, paz, restauração, conforto"},
    {"numero": "91",  "tema": "Proteção Divina e Familiar",   "keys": "proteção, amarras, casa, família"},
    {"numero": "121", "tema": "O Senhor Guarda Seus Passos",   "keys": "proteção, caminhos, saída e chegada"},
    {"numero": "27",  "tema": "O Senhor é Minha Luz",         "keys": "luz, salvação, vitória, confiança"},
    {"numero": "103", "tema": "Bênçãos e Cura Divina",        "keys": "cura, perdão, renovação, misericórdia"},
    {"numero": "46",  "tema": "Deus é Nosso Refúgio",         "keys": "refúgio, fortaleza, paz, força"},
    {"numero": "34",  "tema": "Libertação e Louvor",          "keys": "livramento, bênção, proteção, anjos"},
    {"numero": "18",  "tema": "Vitória Sobre os Inimigos",    "keys": "vitória, livramento, força, batalha"},
    {"numero": "37",  "tema": "Confie no Senhor",             "keys": "confiança, provisão, justiça, herança"},
    {"numero": "51",  "tema": "Arrependimento e Restauração", "keys": "perdão, restauração, novo coração"},
    {"numero": "63",  "tema": "Sede de Deus",                 "keys": "adoração, presença, sede espiritual"},
    {"numero": "139", "tema": "Deus Conhece o Seu Coração",   "keys": "onisciência, amor, ser conhecido por Deus"},
]


def gerar_oracao() -> dict:
    """
    Chama a API Groq (llama-3.3-70b-versatile) e gera uma oração
    completa no estilo do canal Bispo Bruno Leonardo.
    Retorna um dict com: oracao_texto, titulo, descricao, tags, salmo, tema.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    # Seleciona o salmo do dia de forma rotativa
    dia_do_ano = datetime.datetime.now().timetuple().tm_yday
    salmo_info = SALMOS[dia_do_ano % len(SALMOS)]

    prompt = f"""Você é um pastor cristão evangélico brasileiro que grava orações poderosas no YouTube no estilo do canal "Bispo Bruno Leonardo".

Gere uma oração completa e emocionante baseada no Salmo {salmo_info['numero']} — "{salmo_info['tema']}".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRUTURA OBRIGATÓRIA (siga à risca):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ABERTURA CALOROSA (3 parágrafos):
   - Cumprimento: "Olá, que Deus e os céus guardem a sua vida."
   - Apresente o Salmo {salmo_info['numero']} e seu poder ({salmo_info['keys']})
   - Convide para orar junto repetindo as palavras ou mentalmente
   - Peça para deixar nomes de familiares nos comentários
   - Explique que todos serão apresentados a Deus em oração

2. ENGAJAMENTO COM O CANAL (2 parágrafos):
   - Peça o gostei/like explicando que avisa o YouTube que o conteúdo é bom
   - Convide para se inscrever no canal para receber mais orações
   - Sugira ouvir esta oração por 7 dias seguidos (7 é o número de Deus)

3. SALMO {salmo_info['numero']} COMPLETO (versículo por versículo):
   - Leia todos os versículos com solene reverência
   - Após cada 2-3 versículos, insira uma breve reflexão pastoral

4. ORAÇÃO PESSOAL PODEROSA (8 a 10 parágrafos longos):
   - Use os nomes de Deus: Jeová Rafá, Jeová Jiré, Jeová Shalom, Jeová Eloí
   - Ore pela quebra de amarras: espirituais, familiares, financeiras, de saúde
   - Ore pela proteção da casa e família de quem está assistindo
   - Quebre obras malignas, maldições, feitiços, doenças
   - Use declarações: "Eu declaro que...", "Eu decreto que..."
   - Envie anjos guerreiros para proteger a pessoa e sua casa
   - Peça para a pessoa levantar a mão direita ao céu
   - Repita as declarações para a pessoa repetir em voz alta ou mentalmente

5. PAI NOSSO COMPLETO (texto completo, sem abreviações)

6. ENCERRAMENTO (3 parágrafos):
   - Confirme que as bênçãos estão sobre a vida, casa e família
   - Recomende ouvir por 7 dias consecutivos
   - Peça para compartilhar com familiares e amigos
   - "Que Jeová Rafá te abençoe grande e poderosamente. Até a próxima."

━━━━━━━━━━━━━━━━━━━━
REGRAS DE ESCRITA:
━━━━━━━━━━━━━━━━━━━━
- Tom: íntimo, pastoral, emotivo, cheio de fé e esperança
- Linguagem: português brasileiro formal-popular (pregação evangélica)
- MÍNIMO 2.500 palavras
- Parágrafos curtos (3-5 linhas cada) — facilitam leitura como legenda de vídeo
- SEM markdown, asteriscos, negrito ou formatação especial — apenas texto puro
- Parágrafo separado por linha em branco

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ao final do texto, adicione exatamente esta linha separadora e então o JSON:

---JSON---
{{
  "titulo": "PODEROSA ORAÇÃO DO SALMO {salmo_info['numero']} — {salmo_info['tema'].upper()} | Canal Oração",
  "descricao": "(300-400 palavras descrevendo a oração, os temas abordados, pedindo like, inscrição e comentários com nomes de familiares)",
  "tags": ["oração", "salmo {salmo_info['numero']}", "oração poderosa", "proteção", "família", "bênção", "cura", "quebrar amarras", "vitória", "canal oração", "oração do dia", "Deus", "fé", "palavra de Deus", "oração evangélica"],
  "salmo": "{salmo_info['numero']}",
  "tema": "{salmo_info['tema']}"
}}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.72,
        max_tokens=4096,
    )

    content = response.choices[0].message.content.strip()

    # ── Separar texto da oração do JSON de metadados ──
    if "---JSON---" in content:
        partes = content.split("---JSON---", 1)
        oracao_texto = partes[0].strip()
        try:
            metadata = json.loads(partes[1].strip())
        except json.JSONDecodeError:
            metadata = _metadata_padrao(salmo_info)
    else:
        oracao_texto = content
        metadata = _metadata_padrao(salmo_info)

    metadata["oracao_texto"] = oracao_texto
    return metadata


def _metadata_padrao(salmo_info: dict) -> dict:
    return {
        "titulo": f"PODEROSA ORAÇÃO DO SALMO {salmo_info['numero']} — {salmo_info['tema'].upper()} | Canal Oração",
        "descricao": (
            f"Oração poderosa do Salmo {salmo_info['numero']} para {salmo_info['keys']}. "
            "Deixe seu nome e o de seus familiares nos comentários para receber oração especial. "
            "Dê seu like e se inscreva no canal para receber orações diárias!"
        ),
        "tags": [
            "oração", f"salmo {salmo_info['numero']}", "oração poderosa",
            "proteção", "família", "bênção", "cura", "quebrar amarras",
            "vitória", "canal oração", "oração do dia", "Deus", "fé",
        ],
        "salmo": salmo_info["numero"],
        "tema": salmo_info["tema"],
    }


if __name__ == "__main__":
    import os, json
    os.makedirs("output", exist_ok=True)
    resultado = gerar_oracao()
    with open("output/oracao.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"✅ Oração gerada: {resultado['titulo']}")
    print(f"   Palavras: {len(resultado['oracao_texto'].split())}")
