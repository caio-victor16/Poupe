import os
import sqlite3
from flask import Blueprint, jsonify, request, session, current_app
from backend.services.ia_limite import reservar_chamada

from backend.services.ia_contexto import montar_contexto
from backend.services.ia_service import ErroIA, GeminiService

MAX_HISTORICO = 10        # mensagens anteriores enviadas junto (5 trocas)
MAX_HISTORICO_CHARS = 8000


def validar_historico(valor):
    """Lista [{papel: 'usuario'|'ia', texto}] vinda do navegador → só as últimas, com limite."""
    if valor is None:
        return []
    if not isinstance(valor, list):
        raise ValueError("O campo 'historico' deve ser uma lista.")
    limpo = []
    for item in valor[-MAX_HISTORICO:]:
        if (not isinstance(item, dict) or item.get("papel") not in ("usuario", "ia")
                or not isinstance(item.get("texto"), str) or not item["texto"].strip()):
            raise ValueError("Histórico da conversa inválido.")
        limpo.append({"papel": item["papel"], "texto": item["texto"].strip()[:4000]})
    # Corta as mais antigas até caber; a conversa precisa começar pelo usuário.
    while limpo and (sum(len(h["texto"]) for h in limpo) > MAX_HISTORICO_CHARS or limpo[0]["papel"] != "usuario"):
        limpo.pop(0)
    return limpo


class IaController:
    def __init__(self):
        self.blueprint = Blueprint("ia", __name__)
        self.service = GeminiService()
        self._registrar_rotas()

    def _registrar_rotas(self):
        self.blueprint.add_url_rule("/ia", view_func=self.conversar_com_ia, methods=["POST"])

    def conversar_com_ia(self):
        dados = request.get_json(silent=True)
        if not isinstance(dados, dict):
            return jsonify({"erro": "JSON inválido."}), 400

        mensagem = dados.get("mensagem")
        if not mensagem or not isinstance(mensagem, str):
            return jsonify({"erro": "O campo 'mensagem' é obrigatório."}), 400

        mensagem = mensagem.strip()
        if not mensagem:
            return jsonify({"erro": "Escreva uma mensagem."}), 400
        if len(mensagem) > 2000:
            return jsonify({"erro": "A mensagem deve possuir no máximo 2000 caracteres."}), 400

        try:
            historico = validar_historico(dados.get("historico"))
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400

        # REV-006: sem chave, avisa sem gastar a cota do usuário.
        if not self.service.configurada:
            return jsonify({"erro": "A IA não está configurada no servidor: falta GEMINI_API_KEY no arquivo .env."}), 503

        config = current_app.config
        limites = [
            ("minuto", 60, config["IA_LIMITE_MINUTO"], False),
            ("dia", 86400, config["IA_LIMITE_DIA"], False),
            ("minuto", 60, config["IA_LIMITE_GLOBAL_MINUTO"], True),
            ("dia", 86400, config["IA_LIMITE_GLOBAL_DIA"], True),
        ]
        try:
            espera = reservar_chamada(
                config.get("IA_LIMITES_DB") or os.path.join(current_app.instance_path, "ia_limites.sqlite3"),
                session["usuario_id"], limites)
        except (sqlite3.Error, OSError):
            current_app.logger.warning("IA: contador de chamadas indisponível")
            return jsonify({"erro": "IA temporariamente indisponível."}), 503
        if espera:
            return jsonify({"erro": "Limite de mensagens atingido. Tente novamente mais tarde.",
                            "tentar_em_segundos": espera}), 429, {"Retry-After": str(espera)}

        try:
            contexto = montar_contexto(session["usuario_id"])
            resposta = self.service.gerar_resposta(mensagem, contexto, historico)
            return jsonify({"resposta": resposta}), 200
        except ErroIA as erro:
            return jsonify({"erro": str(erro)}), 502
        except Exception:
            current_app.logger.warning("IA: falha inesperada ao processar chamada")
            return jsonify({"erro": "Erro interno ao processar a mensagem."}), 500


ia_controller = IaController()
ia_bp = ia_controller.blueprint
