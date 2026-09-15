from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.extensions import db
from backend.services.alerta_service import AlertaService


class AlertaController:
    def __init__(self):
        self.blueprint = Blueprint("alerta", __name__)
        self.service = AlertaService()
        self._registrar_rotas()

    def _registrar_rotas(self):
        self.blueprint.add_url_rule("/alertas/usuario/<int:id_usuario>", view_func=self.listar_por_usuario, methods=["GET"])
        self.blueprint.add_url_rule("/alertas/<int:id_alerta>", view_func=self.buscar, methods=["GET"])
        self.blueprint.add_url_rule("/alertas", view_func=self.criar, methods=["POST"])
        self.blueprint.add_url_rule("/alertas/<int:id_alerta>/visualizar", view_func=self.visualizar, methods=["PUT"])
        self.blueprint.add_url_rule("/alertas/<int:id_alerta>", view_func=self.excluir, methods=["DELETE"])
        self.blueprint.add_url_rule("/alertas/usuario/<int:id_usuario>/gerar-limite", view_func=self.gerar_alerta_limite, methods=["POST"])

    def listar_por_usuario(self, id_usuario):
        return jsonify(self.service.listar_por_usuario(id_usuario)), 200

    def buscar(self, id_alerta):
        alerta = self.service.buscar_por_id(id_alerta)
        if alerta is None:
            return jsonify({"erro": "Alerta não encontrado."}), 404
        return jsonify(alerta), 200

    def criar(self):
        try:
            alerta = self.service.criar(request.get_json() or {})
            return jsonify(alerta), 201
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao salvar alerta."}), 500

    def visualizar(self, id_alerta):
        try:
            alerta = self.service.marcar_como_visualizado(id_alerta)
            if alerta is None:
                return jsonify({"erro": "Alerta não encontrado."}), 404
            return jsonify(alerta), 200
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao visualizar alerta."}), 500

    def excluir(self, id_alerta):
        try:
            if not self.service.excluir(id_alerta):
                return jsonify({"erro": "Alerta não encontrado."}), 404
            return "", 204
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao excluir alerta."}), 500

    def gerar_alerta_limite(self, id_usuario):
        try:
            self.service.gerar_alerta_limite(id_usuario)
            return jsonify({"mensagem": "Verificação de limite realizada."}), 200
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao gerar alerta de limite."}), 500


alerta_controller = AlertaController()
alerta_bp = alerta_controller.blueprint
