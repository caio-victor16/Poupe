from flask import Blueprint, jsonify

from backend.services.previsao_service import PrevisaoService


class PrevisaoController:
    def __init__(self):
        self.blueprint = Blueprint("previsao", __name__)
        self.service = PrevisaoService()
        self._registrar_rotas()

    def _registrar_rotas(self):
        self.blueprint.add_url_rule("/previsoes/usuario/<int:id_usuario>", view_func=self.calcular, methods=["GET"])

    def calcular(self, id_usuario):
        resultado = self.service.calcular(id_usuario)
        if resultado is None:
            return jsonify({"erro": "Usuário não encontrado."}), 404
        return jsonify(resultado), 200


previsao_controller = PrevisaoController()
previsao_bp = previsao_controller.blueprint
