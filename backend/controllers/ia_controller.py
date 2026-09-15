from flask import Blueprint, jsonify, request

from backend.services.ia_service import GeminiService


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
        if len(mensagem) > 2000:
            return jsonify({"erro": "A mensagem deve possuir no máximo 2000 caracteres."}), 400

        try:
            resposta = self.service.gerar_resposta(mensagem)
            return jsonify({"resposta": resposta}), 200
        except RuntimeError as erro:
            return jsonify({"erro": str(erro)}), 502
        except Exception as erro:
            print("Erro inesperado:", erro)
            return jsonify({"erro": "Erro interno ao processar a mensagem."}), 500


ia_controller = IaController()
ia_bp = ia_controller.blueprint
