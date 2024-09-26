from openai import OpenAI
from dotenv import load_dotenv
import os
import tiktoken
import openai

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_TEST"))
modelo = "gpt-4o-mini"

codificador = tiktoken.encoding_for_model(modelo)

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

def analisador_sentimentos(produto):
    prompt_sistema = f"""
        Você é um analisador de sentimentos de avaliações de produtos.
        Escreva um parágrafo com até 50 palavras resumindo as avaliações e 
        depois atribua qual o sentimento geral para o produto.
        Identifique também 3 pontos fortes e 3 pontos fracos identificados a partir das avaliações.

        # Formato de Saída

        Nome do Produto:
        Resumo das Avaliações:
        Sentimento Geral: [utilize aqui apenas Positivo, Negativo ou Neutro]
        Ponto fortes: lista com três bullets
        Pontos fracos: lista com três bullets
    """

    prompt_usuario = carrega(f'../dados/avaliacoes-{produto}.txt')
    print(f"Analisando avaliações para o produto {produto}")

    lista_mensagens = [
        {
            "role": "system",
            "content": prompt_sistema
        },
        {
            "role": "user",
            "content": prompt_usuario
        }
    ]

    try:
        resposta = client.chat.completions.create(
            messages = lista_mensagens,
            model=modelo
        )
        
        texto_resposta = resposta.choices[0].message.content
        salva(f'../dados/analise-{produto}.txt', texto_resposta)
    except openai.AuthenticationError as e:
        print(f"Erro de autenticação: {e}")
    except openai.APIError as e:
        print(f"Erro de API: {e}")



lista_de_produtos = ["Maquiagem mineral", "Camisetas de algodão orgânico", "Jeans feitos com materiais reciclados"]

for produto in lista_de_produtos:
    analisador_sentimentos(produto)
