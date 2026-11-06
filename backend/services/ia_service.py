"""Uma chamada ao provedor por mensagem, sem registrar conteúdo privado."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class ErroIA(RuntimeError):
    """Falha conhecida cuja mensagem foi escrita para exibição ao usuário."""


class GeminiService:
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    def gerar_resposta(self, mensagem):
        if not self.api_key:
            raise ErroIA("A IA não está configurada no servidor.")
        prompt = (
            "Você é o assistente financeiro do Poupe+. Responda em português do Brasil, "
            "de forma simples e educativa, sobre organização, gastos, economia e metas. "
            "Não peça senhas, cartões ou dados bancários. Não invente informações financeiras.\n"
            "Mensagem do usuário:\n" + mensagem
        )
        try:
            # Não repetir após timeout: o provedor pode ter processado e cobrado.
            resposta = requests.post(
                f"{self.BASE_URL}/{self.model}:generateContent",
                headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=(5, 30),
            )
            if resposta.status_code == 429:
                raise ErroIA("O provedor de IA atingiu seu limite. Tente mais tarde.")
            if resposta.status_code in (401, 403):
                raise ErroIA("A IA não está autorizada no provedor. Contate o responsável pelo sistema.")
            resposta.raise_for_status()
            dados = resposta.json()
            candidatos = dados.get("candidates") or []
            partes = candidatos[0].get("content", {}).get("parts", []) if candidatos else []
            textos = [p["text"] for p in partes if isinstance(p.get("text"), str) and p["text"]]
            if not textos:
                raise ErroIA("A IA não retornou uma resposta. Tente mais tarde.")
            return "\n".join(textos)
        except requests.Timeout:
            raise ErroIA("A IA demorou demais para responder. Tente mais tarde.") from None
        except requests.RequestException:
            raise ErroIA("Não foi possível consultar o provedor de IA.") from None
        except (ValueError, TypeError, AttributeError, KeyError):
            raise ErroIA("O provedor de IA retornou uma resposta inválida.") from None
