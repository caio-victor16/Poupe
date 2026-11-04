from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.extensions import db
from backend.services.recorrencia_gasto_service import RecorrenciaGastoService


def _nao_encontrada():
    return jsonify({"erro": "Recorrência não encontrada."}), 404


class RecorrenciaGastoController:
    def __init__(self):
        self.blueprint = Blueprint("recorrencia_gasto", __name__)
        self.service = RecorrenciaGastoService()
        self._registrar_rotas()
        self._registrar_erros()

    def _registrar_rotas(self):
        rotas = [
            ("/recorrencias", self.criar, ["POST"]),
            ("/recorrencias/<int:id_recorrencia>", self.buscar, ["GET"]),
            ("/recorrencias/<int:id_recorrencia>", self.atualizar, ["PUT"]),
            ("/recorrencias/<int:id_recorrencia>", self.excluir, ["DELETE"]),
            ("/recorrencias/usuario/<int:id_usuario>", self.listar_por_usuario, ["GET"]),
            ("/recorrencias/usuario/<int:id_usuario>/processar", self.processar_vencidas, ["POST"]),
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
        return jsonify(self.service.criar(request.get_json() or {})), 201

    def buscar(self, id_recorrencia):
        recorrencia = self.service.buscar_por_id(id_recorrencia)
        return (jsonify(recorrencia), 200) if recorrencia else _nao_encontrada()

    def listar_por_usuario(self, id_usuario):
        return jsonify(self.service.listar_por_usuario(id_usuario)), 200

    def atualizar(self, id_recorrencia):
        recorrencia = self.service.atualizar(id_recorrencia, request.get_json() or {})
        return (jsonify(recorrencia), 200) if recorrencia else _nao_encontrada()

    def excluir(self, id_recorrencia):
        if not self.service.excluir(id_recorrencia):
            return _nao_encontrada()
        return "", 204

    def processar_vencidas(self, id_usuario):
        gastos = self.service.processar_vencidas(id_usuario)
        return jsonify({"gerados": len(gastos), "gastos": gastos}), 200


recorrencia_gasto_controller = RecorrenciaGastoController()
recorrencia_gasto_bp = recorrencia_gasto_controller.blueprint