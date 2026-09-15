from flask import Blueprint, jsonify

from backend.services.relatorio_service import RelatorioService


class RelatorioController:
    def __init__(self):
        self.blueprint = Blueprint("relatorio", __name__)
        self.service = RelatorioService()
        self._registrar_rotas()

    def _registrar_rotas(self):
        self.blueprint.add_url_rule("/relatorios/usuario/<int:id_usuario>", view_func=self.financeiro, methods=["GET"])

    def financeiro(self, id_usuario):
        resultado = self.service.financeiro(id_usuario)
        if resultado is None:
            return jsonify({"erro": "Usuário não encontrado."}), 404
        return jsonify(resultado), 200


relatorio_controller = RelatorioController()
relatorio_bp = relatorio_controller.blueprint
