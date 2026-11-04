from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.extensions import db
from backend.services.gasto_service import GastoService


class GastoController:
    def __init__(self):
        self.blueprint = Blueprint("gasto", __name__)
        self.service = GastoService()
        self._registrar_rotas()

    def _registrar_rotas(self):
        self.blueprint.add_url_rule("/gastos", view_func=self.listar, methods=["GET"])
        self.blueprint.add_url_rule("/gastos/<int:id_gasto>", view_func=self.buscar, methods=["GET"])
        self.blueprint.add_url_rule("/gastos", view_func=self.criar, methods=["POST"])
        self.blueprint.add_url_rule("/gastos/<int:id_gasto>", view_func=self.atualizar, methods=["PUT"])
        self.blueprint.add_url_rule("/gastos/<int:id_gasto>", view_func=self.excluir, methods=["DELETE"])
        self.blueprint.add_url_rule("/gastos/usuario/<int:id_usuario>", view_func=self.listar_por_usuario, methods=["GET"])
        self.blueprint.add_url_rule("/gastos/usuario/<int:id_usuario>/categorias", view_func=self.gastos_por_categoria, methods=["GET"])
        self.blueprint.add_url_rule("/gastos/usuario/<int:id_usuario>/periodo", view_func=self.gastos_por_periodo, methods=["GET"])
        self.blueprint.add_url_rule("/gastos/usuario/<int:id_usuario>/limite", view_func=self.verificar_limite, methods=["GET"])

    def listar(self):
        return jsonify(self.service.listar()), 200

    def buscar(self, id_gasto):
        gasto = self.service.buscar_por_id(id_gasto)
        if gasto is None:
            return jsonify({"erro": "Gasto não encontrado."}), 404
        return jsonify(gasto), 200

    def criar(self):
        try:
            gasto = self.service.criar(request.get_json() or {})
            return jsonify(gasto), 201
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao salvar gasto."}), 500

    def atualizar(self, id_gasto):
        try:
            gasto = self.service.atualizar(id_gasto, request.get_json() or {})
            if gasto is None:
                return jsonify({"erro": "Gasto não encontrado."}), 404
            return jsonify(gasto), 200
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao atualizar gasto."}), 500

    def excluir(self, id_gasto):
        try:
            if not self.service.excluir(id_gasto):
                return jsonify({"erro": "Gasto não encontrado."}), 404
            return "", 204
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao excluir gasto."}), 500

    def listar_por_usuario(self, id_usuario):
        return jsonify(self.service.listar_por_usuario(id_usuario)), 200

    def gastos_por_categoria(self, id_usuario):
        return jsonify(self.service.gastos_por_categoria(id_usuario)), 200

    def gastos_por_periodo(self, id_usuario):
        data_inicio = request.args.get("inicio")
        data_fim = request.args.get("fim")
        if not data_inicio or not data_fim:
            return jsonify({"erro": "Informe os parâmetros 'inicio' e 'fim'."}), 400
        return jsonify(self.service.gastos_por_periodo(id_usuario, data_inicio, data_fim)), 200

    def verificar_limite(self, id_usuario):
        resultado = self.service.verificar_limite(id_usuario)
        if resultado is None:
            return jsonify({"erro": "Usuário não encontrado."}), 404
        return jsonify(resultado), 200


gasto_controller = GastoController()
gasto_bp = gasto_controller.blueprint
