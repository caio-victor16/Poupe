from flask import Blueprint, jsonify, request
from backend.services.cofrinho_service import CofrinhoService
class CofrinhoController:
    def __init__(self):
        self.blueprint = Blueprint("cofrinho", __name__)
        self.service = CofrinhoService()
        self._registrar_rotas()

    def _registrar_rotas(self):
        self.blueprint.add_url_rule("/cofrinho/usuario/<int:id_usuario>", view_func=self.simular, methods=["GET"])

    def simular(self, id_usuario):
        try:
            passo = int(request.args.get("passo", 5))
            dias = int(request.args.get("dias", 30))
        except ValueError:
            return jsonify({"erro": "Os parâmetros 'passo' e 'dias' devem ser números inteiros."}), 400

        try:
            resultado = self.service.simular(id_usuario, passo, dias)
            if resultado is None:
                return jsonify({"erro": "Usuário não encontrado."}), 404
            return jsonify(resultado), 200
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400


cofrinho_controller = CofrinhoController()
cofrinho_bp = cofrinho_controller.blueprint