from flask import Blueprint, jsonify
from backend.services.desperdicio_service import DesperdicioService
class DesperdicioController:
    def __init__(self):
        self.blueprint = Blueprint("desperdicio", __name__)
        self.service = DesperdicioService()
        self._registrar_rotas()

    def _registrar_rotas(self):
        self.blueprint.add_url_rule("/desperdicios/usuario/<int:id_usuario>", view_func=self.analisar, methods=["GET"])

    def analisar(self, id_usuario):
        return jsonify(self.service.analisar(id_usuario)), 200


desperdicio_controller = DesperdicioController()
desperdicio_bp = desperdicio_controller.blueprint