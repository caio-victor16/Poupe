import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()


class GeminiService:

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self):

        self.api_key = os.getenv("GEMINI_API_KEY")

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.1-flash"
        )

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY não foi configurada no arquivo .env."
            )

    def gerar_resposta(self, mensagem):

        modelos = [
            self.model,
            "gemini-3.6-flash",
            "gemini-3.1-flash-lite",
]
        

        ultimo_status = None

        for modelo in modelos:

            url = (
                f"{self.BASE_URL}/"
                f"{modelo}:generateContent"
            )

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }

            prompt = f"""
Você é o assistente financeiro do sistema Poupe+.

Ajude o usuário com:

- organização financeira;
- controle de gastos;
- economia;
- planejamento financeiro;
- metas financeiras;
- hábitos de consumo.

Responda sempre em português do Brasil.

Seja simples, objetivo e educativo.

Não peça:
- senhas;
- números de cartão;
- dados bancários;
- informações pessoais sensíveis.

Não invente informações financeiras.

Mensagem do usuário:

{mensagem}
"""

            body = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }

            print("\n==============================")
            print("ENVIANDO PARA GEMINI")
            print("==============================")
            print("Modelo:", modelo)
            print("URL:", url)
            print("Mensagem:", mensagem)

            try:

                resposta = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=(10, 60)
                )

                ultimo_status = resposta.status_code

                print("\n==============================")
                print("RESPOSTA GEMINI")
                print("==============================")
                print("Status:", resposta.status_code)
                print("Resposta:", resposta.text[:2000])
                
                if resposta.status_code in (404, 503):

                    print(f"Modelo {modelo} indisponível/descontinuado ({resposta.status_code}).")

                    if modelo != modelos[-1]:
                        print("Tentando o próximo modelo...")
                        time.sleep(2)
                        continue

                    raise RuntimeError(
                        "O Gemini está indisponível no momento "
                        "(modelo sobrecarregado ou descontinuado). "
                        "Tente novamente em instantes."
                    )

                if resposta.status_code == 429:

                    raise RuntimeError(
                        "O limite gratuito da API do Gemini "
                        "foi atingido. Aguarde alguns minutos "
                        "e tente novamente."
                    )

                if resposta.status_code in (401, 403):

                    raise RuntimeError(
                        "A chave da API do Gemini "
                        "não está autorizada. "
                        "Verifique a GEMINI_API_KEY."
                    )

                resposta.raise_for_status()

                # Limite de requisições
                if resposta.status_code == 429:

                    raise RuntimeError(
                        "O limite gratuito da API do Gemini "
                        "foi atingido. Aguarde alguns minutos "
                        "e tente novamente."
                    )

                # Chave/autorização
                if resposta.status_code in (401, 403):

                    raise RuntimeError(
                        "A chave da API do Gemini "
                        "não está autorizada. "
                        "Verifique a GEMINI_API_KEY."
                    )

                resposta.raise_for_status()

                dados = resposta.json()

                candidatos = dados.get(
                    "candidates",
                    []
                )

                if not candidatos:

                    raise RuntimeError(
                        "O Gemini não retornou candidatos."
                    )

                conteudo = candidatos[0].get(
                    "content",
                    {}
                )

                partes = conteudo.get(
                    "parts",
                    []
                )

                textos = []

                for parte in partes:

                    texto = parte.get("text")

                    if texto:
                        textos.append(texto)

                if not textos:

                    raise RuntimeError(
                        "O Gemini retornou uma resposta vazia."
                    )

                return "\n".join(textos)

            except requests.Timeout:

                print(
                    "ERRO: timeout ao acessar o Gemini."
                )

                if modelo != modelos[-1]:
                    continue

                raise RuntimeError(
                    "O Gemini demorou demais para responder."
                )

            except requests.ConnectionError as erro:

                print(
                    "ERRO DE CONEXÃO:",
                    erro
                )

                raise RuntimeError(
                    "Não foi possível conectar "
                    "ao servidor do Gemini."
                )

            except requests.HTTPError as erro:

                print(
                    "ERRO HTTP GEMINI:",
                    erro
                )

                raise RuntimeError(
                    f"O Gemini recusou a requisição "
                    f"(HTTP {ultimo_status})."
                )

            except requests.RequestException as erro:

                print(
                    "ERRO REQUESTS:",
                    erro
                )

                raise RuntimeError(
                    "Erro ao acessar a API do Gemini."
                )