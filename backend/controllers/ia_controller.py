import os
import sqlite3
from flask import Blueprint, jsonify, request, session, current_app
from backend.services.ia_limite import reservar_chamada

from backend.services.ia_service import ErroIA, GeminiService


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
            resposta = self.service.gerar_resposta(mensagem)
            return jsonify({"resposta": resposta}), 200
        except ErroIA as erro:
            return jsonify({"erro": str(erro)}), 502
        except Exception:
            current_app.logger.warning("IA: falha inesperada ao processar chamada")
            return jsonify({"erro": "Erro interno ao processar a mensagem."}), 500


ia_controller = IaController()
ia_bp = ia_controller.blueprint
