from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.extensions import db
from backend.services.categoria_service import CategoriaService


class CategoriaController:
    def __init__(self):
        self.blueprint = Blueprint("categoria", __name__)
        self.service = CategoriaService()
        self._registrar_rotas()

    def _registrar_rotas(self):
        self.blueprint.add_url_rule("/categorias", view_func=self.listar, methods=["GET"])
        self.blueprint.add_url_rule("/categorias/<int:id_categoria>", view_func=self.buscar, methods=["GET"])
        self.blueprint.add_url_rule("/categorias", view_func=self.criar, methods=["POST"])
        self.blueprint.add_url_rule("/categorias/<int:id_categoria>", view_func=self.atualizar, methods=["PUT"])
        self.blueprint.add_url_rule("/categorias/<int:id_categoria>", view_func=self.excluir, methods=["DELETE"])

    def listar(self):
        return jsonify(self.service.listar()), 200

    def buscar(self, id_categoria):
        categoria = self.service.buscar_por_id(id_categoria)
        if categoria is None:
            return jsonify({"erro": "Categoria não encontrada."}), 404
        return jsonify(categoria), 200

    def criar(self):
        try:
            categoria = self.service.criar(request.get_json() or {})
            return jsonify(categoria), 201
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao salvar categoria."}), 500

    def atualizar(self, id_categoria):
        try:
            categoria = self.service.atualizar(id_categoria, request.get_json() or {})
            if categoria is None:
                return jsonify({"erro": "Categoria não encontrada."}), 404
            return jsonify(categoria), 200
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao atualizar categoria."}), 500

    def excluir(self, id_categoria):
        try:
            if not self.service.excluir(id_categoria):
                return jsonify({"erro": "Categoria não encontrada."}), 404
            return "", 204
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao excluir categoria."}), 500


categoria_controller = CategoriaController()
categoria_bp = categoria_controller.blueprint
