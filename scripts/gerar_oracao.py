import os
import re
import json
import random
import datetime

from groq import Groq

DIAS_SEMANA = ["SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO", "DOMINGO"]

# ─────────────────────────────────────────────────────────────────────────────
# Base de dados de salmos temáticos centrados em dores reais do povo brasileiro
# ─────────────────────────────────────────────────────────────────────────────
SALMOS = [
    {
        "numero": "91",
        "tema": "Proteção Divina e Quebra do Medo",
        "dor_central": "ansiedade, pânico, insônia e medo do amanhã",
        "keys": "ansiedade, pânico, insônia, proteção divina, livramento, paz interior, sono tranquilo",
    },
    {
        "numero": "128",
        "tema": "Restauração do Casamento e do Lar",
        "dor_central": "separação, brigas no lar, frieza conjugal e divórcio",
        "keys": "separação, casamento restaurado, união da família, paz no lar, fim das brigas, reconciliação",
    },
    {
        "numero": "34",
        "tema": "Consolo e Cura do Coração Quebrado",
        "dor_central": "perda de ente querido, luto, dor no peito e saudade dolorosa",
        "keys": "luto, perda, consolo divino, coração despedaçado, alívio da dor, Deus perto dos que choram",
    },
    {
        "numero": "63",
        "tema": "Sede de Deus e Intimidade com Cristo",
        "dor_central": "se aproximar de Jesus, frieza espiritual e vazio na alma",
        "keys": "se aproximar de Jesus, intimidade com Deus, renovo espiritual, presença de Deus, sede da alma",
    },
    {
        "numero": "126",
        "tema": "Virada de Cativeiro e Salvação no Lar",
        "dor_central": "conversão dos filhos, salvação da família e libertação de vícios",
        "keys": "conversão de filhos, salvação da família, libertação de vícios, lágrimas que viram colheita de alegria",
    },
    {
        "numero": "46",
        "tema": "Deus é Nosso Refúgio e Fortaleza",
        "dor_central": "refúgio da alma, esgotamento mental, cansaço extremo e desespero",
        "keys": "refúgio da alma, esgotamento, cansaço extremo, desespero, socorro bem presente, paz na tempestade",
    },
    {
        "numero": "18",
        "tema": "Batalha Espiritual e Quebra de Feitiçaria",
        "dor_central": "reforço espiritual, quebra de inveja, amarras espirituais e feitiços",
        "keys": "reforço espiritual, quebra de feitiços, inveja destruída, amarras quebradas, vitória na batalha",
    },
    {
        "numero": "37",
        "tema": "Providência Divina e Portas Abertas",
        "dor_central": "dívidas asfixiantes, desemprego, humilhação financeira e falta de sustento",
        "keys": "dívidas, providência divina, portas de emprego abertas, socorro financeiro, o justo nunca mendiga o pão",
    },
    {
        "numero": "103",
        "tema": "Cura Divina do Corpo e da Alma",
        "dor_central": "cura de enfermidades graves, dores no corpo e depressão profunda",
        "keys": "cura divina, cura da depressão, alívio de dores, restauração da saúde, Jeová Rafá",
    },
    {
        "numero": "121",
        "tema": "O Senhor Guarda a Sua Saída e a Sua Chegada",
        "dor_central": "medo da violência urbana, assaltos, perigo nas ruas e acidentes",
        "keys": "proteção nas ruas, saída e chegada, livramento de assaltos, guarda de anjos, proteção dos caminhos",
    },
    {
        "numero": "51",
        "tema": "Purificação, Arrependimento e Novo Recomeço",
        "dor_central": "peso da culpa, vergonha do passado, remorso e necessidade de perdão",
        "keys": "perdão dos pecados, alívio da culpa, coração puro, novo recomeço, misericórdia de Deus",
    },
    {
        "numero": "139",
        "tema": "Cura da Solidão e do Sentimento de Rejeição",
        "dor_central": "solidão profunda, rejeição familiar, abandono e sensação de invisibilidade",
        "keys": "cura da solidão, rejeição superada, acolhimento de Deus, amor incondicional, valorizado por Deus",
    },
    {
        "numero": "35",
        "tema": "Livramento de Injustiças e Pessoas Falsas",
        "dor_central": "calúnias, fofocas, traições de falsos amigos e causas na justiça",
        "keys": "justiça divina, calúnias caídas por terra, livramento de traição, causas na justiça, Deus é teu advogado",
    },
    {
        "numero": "130",
        "tema": "Clamor do Fundo do Poço por Socorro",
        "dor_central": "desespero total, quando não há mais forças humanas nem saída aparente",
        "keys": "clamor no fundo do poço, milagre urgente, socorro divino, esperança viva, redenção completa",
    },
    {
        "numero": "23",
        "tema": "O Bom Pastor que Restaura as Forças",
        "dor_central": "sensação de desamparo, falta de paz e medo do futuro incerto",
        "keys": "o Senhor é meu pastor, nada faltará, refrigério para a alma, mesa no deserto, paz de espírito",
    },
    {
        "numero": "40",
        "tema": "Cântico Novo e Resgate da Esperança",
        "dor_central": "espera angustiante, promessas que parecem demorar e choro sem resposta",
        "keys": "paciência na provação, cântico novo, tirado da lama, pés firmes na rocha, vitória decretada",
    },
]


def selecionar_salmo() -> dict:
    """
    Seleciona o salmo sequencialmente garantindo que a cada execução um tema
    diferente de dor do brasileiro seja abordado, sem repetições no mesmo dia.

    Suporta tanto execução no GitHub Actions (via GITHUB_RUN_NUMBER)
    quanto execução local (via data/ultimo_salmo.json).
    """
    caminho_tracker = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "ultimo_salmo.json",
    )

    indice = None

    # 1. Se estiver rodando no GitHub Actions com run_number disponível
    if "GITHUB_RUN_NUMBER" in os.environ:
        try:
            run_num = int(os.environ["GITHUB_RUN_NUMBER"])
            run_attempt = int(os.environ.get("GITHUB_RUN_ATTEMPT", 1))
            indice = (run_num + run_attempt - 1) % len(SALMOS)
        except Exception:
            indice = None

    # 2. Se não estiver no GitHub Actions ou se falhou, usa o tracker local
    if indice is None:
        if os.path.exists(caminho_tracker):
            try:
                with open(caminho_tracker, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    ultimo = dados.get("ultimo_indice", -1)
                    indice = (ultimo + 1) % len(SALMOS)
            except Exception:
                indice = 0
        else:
            indice = 0

    salmo_escolhido = SALMOS[indice]

    # Salva o estado atualizado no tracker
    try:
        os.makedirs(os.path.dirname(caminho_tracker), exist_ok=True)
        with open(caminho_tracker, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "ultimo_indice": indice,
                    "salmo": salmo_escolhido["numero"],
                    "tema": salmo_escolhido["tema"],
                    "dor_central": salmo_escolhido["dor_central"],
                    "atualizado_em": datetime.datetime.now().isoformat(),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(
            f"[ORACAO] Salmo selecionado sequencialmente: Salmo {salmo_escolhido['numero']} "
            f"({indice + 1}/{len(SALMOS)}) — Tema: {salmo_escolhido['tema']} — "
            f"Dor Central: {salmo_escolhido['dor_central']}"
        )
    except Exception as e:
        print(f"[ORACAO] Aviso ao atualizar tracking de salmo: {e}")

    return salmo_escolhido


def gerar_oracao() -> dict:
    """
    Chama a API Groq e gera uma oração completa no estilo do canal Bispo Bruno Leonardo.
    Retorna um dict com: oracao_texto, titulo, descricao, tags, salmo, tema, dor_central.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    # Seleciona o salmo sequencialmente com base nas dores centrais do brasileiro
    salmo_info = selecionar_salmo()
    dia_semana_abrev = DIAS_SEMANA[datetime.datetime.now().weekday()]

    prompt = f"""Você é um pastor cristão evangélico brasileiro que grava orações poderosas no YouTube no estilo do canal "Bispo Bruno Leonardo".

Gere uma oração completa, profunda e emocionante baseada no Salmo {salmo_info['numero']} — "{salmo_info['tema']}".

TEMA CENTRAL E DOR DO BRASILEIRO:
Esta oração deve ser fortemente focada na seguinte dor e anseio do coração do povo brasileiro:
👉 {salmo_info['dor_central'].upper()}
Aborde essa dor com profunda compaixão, empatia e autoridade espiritual, trazendo alívio, libertação, cura e renovo de fé.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRUTURA OBRIGATÓRIA (siga à risca):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ABERTURA CALOROSA (3 parágrafos):
   - Cumprimento: "Olá, que Deus e os céus guardem a sua vida."
   - Conecte-se imediatamente com quem está enfrentando {salmo_info['dor_central']}, confortando seu coração e afirmando que esta oração é resposta de Deus.
   - Apresente o Salmo {salmo_info['numero']} e seu poder ({salmo_info['keys']})
   - Convide para orar junto repetindo as palavras ou mentalmente
   - Peça para deixar nomes de familiares nos comentários
   - Explique que todos serão apresentados a Deus em oração

2. ENGAJAMENTO COM O CANAL (2 parágrafos):
   - Peça o gostei/like explicando que avisa o YouTube que este clamor de libertação e esperança precisa alcançar mais vidas aflitas
   - Convide para se inscrever no canal para receber orações diárias
   - Sugira ouvir esta oração por 7 dias seguidos (7 é o número da perfeição e do milagre de Deus)

3. SALMO {salmo_info['numero']} COMPLETO (versículo por versículo):
   - Leia todos os versículos com solene reverência
   - Após cada 2-3 versículos, insira uma breve reflexão pastoral aplicando o texto sagrado diretamente contra a dor de {salmo_info['dor_central']}

4. ORAÇÃO PESSOAL PODEROSA (8 a 10 parágrafos longos):
   - Use os nomes de Deus: Jeová Rafá, Jeová Jiré, Jeová Shalom, Jeová Eloí
   - Ore especificamente contra o jugo de {salmo_info['dor_central']}, determinando livramento e alívio
   - Ore pela quebra de amarras: espirituais, familiares, financeiras, de saúde e emocionais
   - Ore pela proteção da casa e família de quem está assistindo
   - Quebre obras malignas, maldições, feitiços, doenças e desespero
   - Use declarações de fé e autoridade: "Eu declaro que...", "Eu decreto que..."
   - Envie anjos guerreiros para proteger a pessoa e sua casa
   - Peça para a pessoa levantar a mão direita ao céu
   - Repita as declarações para a pessoa repetir em voz alta ou mentalmente

5. PAI NOSSO COMPLETO (texto completo, sem abreviações)

6. ENCERRAMENTO (3 parágrafos):
   - Confirme que as bênçãos e o alívio para {salmo_info['dor_central']} já foram liberados sobre a vida, casa e família
   - Recomende ouvir por 7 dias consecutivos
   - Peça para compartilhar com familiares e amigos que precisam de amparo
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
  "titulo": "PODEROSA ORAÇÃO DO SALMO {salmo_info['numero']} — {salmo_info['tema'].upper()} | {dia_semana_abrev}",
  "descricao": "Oração poderosa baseada no Salmo {salmo_info['numero']} para trazer bênçãos, proteção e alívio contra {salmo_info['dor_central']} na sua vida e na sua família.",
  "tags": ["oração", "salmo {salmo_info['numero']}", "oração poderosa", "proteção", "família", "bênção", "cura", "quebrar amarras", "vitória", "oração do dia", "Deus", "fé", "palavra de Deus", "oração evangélica"],
  "salmo": "{salmo_info['numero']}",
  "tema": "{salmo_info['tema']}"
}}
"""

    modelos_candidatos = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b",
    ]

    response = None
    ultimo_erro = None
    for modelo in modelos_candidatos:
        try:
            print(f"[GROQ] Tentando modelo '{modelo}'...")
            response = client.chat.completions.create(
                model=modelo,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.72,
                max_tokens=4096,
            )
            print(f"[GROQ] Sucesso com o modelo '{modelo}'!")
            break
        except Exception as e:
            print(f"[GROQ] Falha no modelo '{modelo}': {e}")
            ultimo_erro = e

    if not response:
        raise RuntimeError(f"Nenhum modelo da Groq respondeu com sucesso. Último erro: {ultimo_erro}")

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
    metadata["salmo"] = salmo_info["numero"]
    metadata["tema"] = salmo_info["tema"]
    metadata["dor_central"] = salmo_info.get("dor_central", "")

    # ── Sanitização rigorosa do título (sem "Canal Oração", com DIA DA SEMANA) ──
    titulo = metadata.get("titulo", "")
    titulo = re.sub(r'\s*\|\s*canal\s+ora[çc][ãa]o\s*', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'\s*-\s*canal\s+ora[çc][ãa]o\s*', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'canal\s+ora[çc][ãa]o', '', titulo, flags=re.IGNORECASE).strip()
    if not any(titulo.upper().endswith(d) for d in DIAS_SEMANA):
        titulo = f"{titulo} | {dia_semana_abrev}"
    metadata["titulo"] = titulo

    # ── Sanitização rigorosa da descrição (garantir que NUNCA vaze instruções de prompt) ──
    descricao = metadata.get("descricao", "")
    indicadores_prompt = [
        "PARÁGRAFO", "Hook SEO", "Escreva uma descrição", "seguir EXATAMENTE",
        "palavra-chave principal", "benefício emocional", "instrução espiritual",
        "estrutura:", "Oração poderosa baseada no Salmo"
    ]
    if any(ind.lower() in descricao.lower() for ind in indicadores_prompt) or len(descricao.strip()) < 150:
        print("[ORACAO] Descrição continha instruções de prompt ou era resumida. Aplicando descrição pastoral estruturada completa.")
        metadata["descricao"] = _gerar_descricao_completa(salmo_info, dia_semana_abrev)

    return metadata


def _gerar_descricao_completa(salmo_info: dict, dia_semana_abrev: str) -> str:
    """Gera uma descrição pastoral de alta conversão para o YouTube, rica em SEO e sem instruções cruas."""
    salmo_num = salmo_info["numero"]
    tema = salmo_info["tema"]
    dor = salmo_info.get("dor_central", tema)
    keys = salmo_info["keys"]

    return (
        f"🙏 ORAÇÃO PODEROSA DO SALMO {salmo_num} — {tema.upper()} | {dia_semana_abrev}\n\n"
        f"Esta oração poderosa baseada no Salmo {salmo_num} foi preparada especialmente para o seu momento de fé hoje. "
        f"Se você ou alguém da sua família está enfrentando {dor} e precisa de {keys}, receba esta palavra com o coração aberto. "
        f"Não importa qual seja a tempestade, a angústia ou a aflição: quando você se coloca na presença do Altíssimo, "
        f"todo jugo cai por terra e o socorro divino se manifesta. Assista até o fim e receba a bênção de Deus agora mesmo.\n\n"
        f"📖 NESTE VÍDEO VOCÊ VAI RECEBER:\n"
        f"✅ A proclamação do Salmo {salmo_num} completo, versículo por versículo com reflexão pastoral\n"
        f"✅ Clamor profundo e oração de autoridade contra {dor}\n"
        f"✅ Quebra de amarras espirituais, financeiras, familiares e de saúde\n"
        f"✅ Envio de anjos guerreiros para blindar a sua casa e toda a sua família\n"
        f"✅ A oração do Pai Nosso completa para abençoar a sua vida\n\n"
        f"🕊️ INSTRUÇÃO ESPIRITUAL PARA VITÓRIA:\n"
        f"Ouça esta oração por 7 dias consecutivos. Na Bíblia Sagrada, o número 7 representa a perfeição e o ciclo de vitória de Deus. "
        f"No momento da oração forte, erga a sua mão direita aos céus e repita as declarações de fé com determinação.\n\n"
        f"💬 COMENTE SEU NOME E PEDIDO DE ORAÇÃO:\n"
        f"Deixe nos comentários o seu nome e os nomes de seus familiares. Todos os dias esses nomes são apresentados diante de Deus em oração.\n\n"
        f"❤️ SEJA UM INSTRUMENTO DE BÊNÇÃO:\n"
        f"1. Deixe o seu LIKE — assim o YouTube entende que esta palavra abençoa vidas e recomenda para mais pessoas aflitas.\n"
        f"2. INSCREVA-SE no canal e ative o sininho para receber orações diárias de fé e vitória.\n"
        f"3. COMPARTILHE este vídeo no grupo da família e com amigos que precisam de um milagre hoje.\n\n"
        f"Que Jeová Rafá e o Deus de Israel abençoem grandemente a sua vida e toda a sua casa!\n\n"
        f"#oração #salmo{salmo_num} #oraçãoPoderosa #fé #Jesus #Deus #bênção #cura #proteção #oraçãoEvangélica #palavraDeDeus #milagre #quebraDeAmarras #oraçãoDoDia"
    )


def _metadata_padrao(salmo_info: dict) -> dict:
    dia_semana_abrev = DIAS_SEMANA[datetime.datetime.now().weekday()]
    return {
        "titulo": f"PODEROSA ORAÇÃO DO SALMO {salmo_info['numero']} — {salmo_info['tema'].upper()} | {dia_semana_abrev}",
        "descricao": _gerar_descricao_completa(salmo_info, dia_semana_abrev),
        "tags": [
            "oração", f"salmo {salmo_info['numero']}", "oração poderosa",
            "proteção", "família", "bênção", "cura", "quebrar amarras",
            "vitória", "oração do dia", "Deus", "fé",
            "Jesus", "palavra de Deus", "milagre", "oração evangélica",
        ],
        "salmo": salmo_info["numero"],
        "tema": salmo_info["tema"],
        "dor_central": salmo_info.get("dor_central", ""),
    }


if __name__ == "__main__":
    import os, json
    os.makedirs("output", exist_ok=True)
    resultado = gerar_oracao()
    with open("output/oracao.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"✅ Oração gerada: {resultado['titulo']}")
    print(f"   Palavras: {len(resultado['oracao_texto'].split())}")

