from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.extensions import db
from backend.services.orcamento_service import OrcamentoService


class OrcamentoController:
    def __init__(self):
        self.blueprint = Blueprint("orcamento", __name__)
        self.service = OrcamentoService()
        self._registrar_rotas()

    def _registrar_rotas(self):
        self.blueprint.add_url_rule("/orcamentos", view_func=self.definir, methods=["POST"])
        self.blueprint.add_url_rule("/orcamentos/usuario/<int:id_usuario>", view_func=self.status_do_mes, methods=["GET"])
        self.blueprint.add_url_rule("/orcamentos/usuario/<int:id_usuario>/verificar", view_func=self.verificar, methods=["POST"])
        self.blueprint.add_url_rule("/orcamentos/<int:id_orcamento>", view_func=self.excluir, methods=["DELETE"])

    def definir(self):
        try:
            return jsonify(self.service.definir(request.get_json() or {})), 200
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao salvar orçamento."}), 500

    def status_do_mes(self, id_usuario):
        return jsonify(self.service.status_do_mes(id_usuario)), 200

    def verificar(self, id_usuario):
        try:
            criados = self.service.gerar_alertas(id_usuario)
            return jsonify({"alertas_criados": criados}), 200
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao verificar orçamentos."}), 500

    def excluir(self, id_orcamento):
        try:
            if not self.service.excluir(id_orcamento):
                return jsonify({"erro": "Orçamento não encontrado."}), 404
            return "", 204
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao excluir orçamento."}), 500


orcamento_controller = OrcamentoController()
orcamento_bp = orcamento_controller.blueprint