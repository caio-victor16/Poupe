from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.extensions import db
from backend.services.receita_service import ReceitaService


def _nao_encontrada():
    return jsonify({"erro": "Receita não encontrada."}), 404


class ReceitaController:
    def __init__(self):
        self.blueprint = Blueprint("receita", __name__)
        self.service = ReceitaService()
        self._registrar_rotas()
        self._registrar_erros()

    def _registrar_rotas(self):
        rotas = [
            ("/receitas", self.criar, ["POST"]),
            ("/receitas/<int:id_receita>", self.atualizar, ["PUT"]),
            ("/receitas/<int:id_receita>", self.excluir, ["DELETE"]),
            ("/receitas/usuario/<int:id_usuario>", self.listar_por_usuario, ["GET"]),
        ]
        for caminho, view, metodos in rotas:
            self.blueprint.add_url_rule(caminho, view_func=view, methods=metodos)

    def _registrar_erros(self):
        @self.blueprint.errorhandler(ValueError)
        def valor_invalido(erro):
            return jsonify({"erro": str(erro)}), 400

        @self.blueprint.errorhandler(SQLAlchemyError)
        def erro_banco(erro):
            db.session.rollback()
            return jsonify({"erro": "Erro ao processar a requisição."}), 500

    def criar(self):
        return jsonify(self.service.criar(request.get_json(silent=True))), 201

    def listar_por_usuario(self, id_usuario):
        return jsonify(self.service.listar_por_usuario(id_usuario)), 200

    def atualizar(self, id_receita):
        receita = self.service.atualizar(id_receita, request.get_json(silent=True))
        return (jsonify(receita), 200) if receita else _nao_encontrada()

    def excluir(self, id_receita):
        if not self.service.excluir(id_receita):
            return _nao_encontrada()
        return "", 204


receita_controller = ReceitaController()
receita_bp = receita_controller.blueprint
