from flask import Blueprint, jsonify, request
from backend.services.caixa_service import CaixaService
class CaixaController:
    def __init__(self):
        self.blueprint = Blueprint("caixa", __name__)
        self.service = CaixaService()
        self._registrar_rotas()

    def _registrar_rotas(self):
        self.blueprint.add_url_rule("/caixa/usuario/<int:id_usuario>", view_func=self.calcular, methods=["GET"])

    def calcular(self, id_usuario):
        try:
            saldo_atual = float(request.args.get("saldo_atual"))
        except (TypeError, ValueError):
            return jsonify({"erro": "Informe o parâmetro 'saldo_atual' com um número."}), 400

        resultado = self.service.calcular(id_usuario, saldo_atual)
        if resultado is None:
            return jsonify({"erro": "Usuário não encontrado."}), 404
        return jsonify(resultado), 200


caixa_controller = CaixaController()
caixa_bp = caixa_controller.blueprint