from openai import OpenAI
from dotenv import load_dotenv
import os
import tiktoken
import openai
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_TEST"))
modelo = "gpt-4o-mini"

codificador = tiktoken.encoding_for_model(modelo)

def gerar_parecer(transacao):
    print("2. Gerando parecer para transacao ", transacao["id"])
    prompt_sistema = f"""
    Para a seguinte transação, forneça um parecer, apenas se o status dela for de "Possível Fraude". Indique no parecer uma justificativa para que você identifique uma fraude.
    Transação: {transacao}

    ## Formato de Resposta
    "id": "id",
    "tipo": "crédito ou débito",
    "estabelecimento": "nome do estabelecimento",
    "horario": "horário da transação",
    "valor": "R$XX,XX",
    "nome_produto": "nome do produto",
    "localizacao": "cidade - estado (País)"
    "status": "",
    "parecer" : "Colocar Não Aplicável se o status for Aprovado"
    """

    lista_mensagens = [
        {
            "role": "user",
            "content": prompt_sistema
        }
    ]

    resposta = client.chat.completions.create(
        messages = lista_mensagens,
        model=modelo
    )

    conteudo = resposta.choices[0].message.content.replace("'", '"')
    print("Finalizando parecer para transacao ", transacao["id"])
    return conteudo


def parecer(lista_transacoes):
    lista_parececimentos = []
    for transacao in lista_transacoes["transacoes"]:
        if transacao["status"] == "Possível Fraude":
            um_parecer =  gerar_parecer(transacao)
            lista_parececimentos.append(um_parecer)

        else:
            pass
    return lista_parececimentos

def carrega(nome_do_arquivo):
    try:
        with open(nome_do_arquivo, "r") as arquivo:
            dados = arquivo.read()
            return dados
    except IOError as e:
        print(f"Erro: {e}")


def salva(nome_do_arquivo, conteudo, formato="utf-8"):
    # deleta o arquivo se ele já existir
    if os.path.exists(nome_do_arquivo):
        os.remove(nome_do_arquivo)
    try:
        with open(nome_do_arquivo, "w", encoding=formato) as arquivo:
            arquivo.write(conteudo)
    except IOError as e:
        print(f"Erro: {e}")

def analisador_transacao(transacoes_lista):
    print("1.Executando analisador de transações")

    prompt_sistema = """
    Analise as transações financeiras a seguir e identifique se cada uma delas é uma "Possível Fraude" ou deve ser "Aprovada". 
    Adicione um atributo "Status" com um dos valores: "Possível Fraude" ou "Aprovado".

    Cada nova transação deve ser inserida dentro da lista do JSON.

    # Possíveis indicações de fraude
    - Transações com valores muito discrepantes
    - Transações que ocorrem em locais muito distantes um do outro
    
        Adote o formato de resposta abaixo para compor sua resposta.
        
    # Formato Saída 
    {
        "transacoes": [
            {
            "id": "id",
            "tipo": "crédito ou débito",
            "estabelecimento": "nome do estabelecimento",
            "horário": "horário da transação",
            "valor": "R$XX,XX",
            "nome_produto": "nome do produto",
            "localização": "cidade - estado (País)"
            "status": ""
            },
        ]
    } 
    """
    lista_mensages = [
        {
            "role": "system",
            "content": prompt_sistema
        },
        {
            "role": "user",
            "content": f"Considere o CSV abaixo, onde cada linha é uma transação diferente:\n{transacoes_lista}. Sua resposta deve adotar o $Formato de Resposta (apenas um json sem outros comentários)"
        }
    ]

    resposta = client.chat.completions.create(
        messages = lista_mensages,
        model=modelo,
        temperature=0
    )

    conteudo = resposta.choices[0].message.content.replace("'", '"')
    print("\n Conteuro" ,conteudo)
    json_conteudo = json.loads(conteudo)
    print("\nJSON:",json_conteudo)
    return json_conteudo



def gerar_recomendacao(parecer,id_transacao):
    print(f"3. Gerando recomendações da transacao: {id_transacao}")
        
    prompt_sistema = f"""
    Para a seguinte transação, forneça uma recomendação apropriada baseada no status e nos detalhes da transação da Transação: {parecer}

    As recomendações podem ser "Notificar Cliente", "Acionar setor Anti-Fraude" ou "Realizar Verificação Manual".
    Elas devem ser escritas no formato técnico.

    Inclua também uma classificação do tipo de fraude, se aplicável. 
    """

    lista_mensagens = [
        {
            "role": "user",
            "content": prompt_sistema
        }
    ]

    resposta = client.chat.completions.create(
        messages = lista_mensagens,
        model=modelo,
        temperature=0
    )

    conteudo = resposta.choices[0].message.content.replace("'", '"')
    print(f"Finalizando recomendações para transação: {id_transacao}")
    return conteudo







lista_dados=[]
lista_de_transacoes = carrega("./dados/transacoes.csv") 
transacoes_analisadas = analisador_transacao(lista_de_transacoes)
lista_parecer = parecer(transacoes_analisadas)
for i, parecer in enumerate(lista_parecer):
    print(f"\nParecer {i+1}: {parecer}")

    parecer_json = parecer.replace("'", '"')
    parecer_json = parecer_json.replace("```json", "")
    parecer_json = parecer_json.replace("```", "")
    parecer_json = json.loads(parecer_json)

    
    id_transacao = transacoes_analisadas["transacoes"][i]["id"]
    recomendacao = gerar_recomendacao(parecer,id_transacao)
    produto = transacoes_analisadas["transacoes"][i]["nome_produto"]
    status = transacoes_analisadas["transacoes"][i]["status"]
    # cria uma lista de dicionários
    lista_dados.append({
        "id_transacao": id_transacao,
        "produto": produto,
        "status": status,
        "parecer": parecer_json["parecer"],
        "recomendacao": recomendacao
    })


print("\nSalvando dados")
transacoes_salvas = []
for i, dados in enumerate(lista_dados):
    print(f"\nProcessando dados da transação {i+1}:")
    
    # Variável para armazenar a transação com JSON formatado
    transacao_formatada = {}

    # Exibe e organiza os dados principais da transação
    for chave, valor in dados.items():
        if '```json' in valor:  # Detecta conteúdo JSON
            # Remove os delimitadores de código e formata o JSON
            valor_json = valor.replace('```json\n', '').replace('```', '')
            try:
                json_formatado = json.loads(valor_json)
                transacao_formatada[chave] = json_formatado
            except json.JSONDecodeError:
                transacao_formatada[chave] = valor  # Caso o JSON esteja mal formatado
        else:
            transacao_formatada[chave] = valor
    
    # Adiciona a transação formatada à lista
    transacoes_salvas.append(transacao_formatada)
    print(f"Dados da transação {i+1} processados e adicionados à lista.")

# Salva a lista de transações formatadas em um arquivo JSON
salva('./dados/transacoes_salvas.json', json.dumps(transacoes_salvas, indent=4))
    



