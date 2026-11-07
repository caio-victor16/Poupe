from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.extensions import db
from backend.services.boleto_service import BoletoService


class BoletoController:
    def __init__(self):
        self.blueprint = Blueprint("boleto", __name__)
        self.service = BoletoService()
        self._registrar_rotas()

    def _registrar_rotas(self):
        self.blueprint.add_url_rule("/boletos", view_func=self.listar, methods=["GET"])
        self.blueprint.add_url_rule("/boletos/<int:id_boleto>", view_func=self.buscar, methods=["GET"])
        self.blueprint.add_url_rule("/boletos", view_func=self.criar, methods=["POST"])
        self.blueprint.add_url_rule("/boletos/<int:id_boleto>", view_func=self.atualizar, methods=["PUT"])
        self.blueprint.add_url_rule("/boletos/<int:id_boleto>", view_func=self.excluir, methods=["DELETE"])
        self.blueprint.add_url_rule("/boletos/usuario/<int:id_usuario>", view_func=self.listar_por_usuario, methods=["GET"])
        self.blueprint.add_url_rule("/boletos/usuario/<int:id_usuario>/proximos", view_func=self.proximos_vencimentos, methods=["GET"])
        self.blueprint.add_url_rule("/boletos/<int:id_boleto>/pagar", view_func=self.pagar, methods=["POST"])
        self.blueprint.add_url_rule("/boletos/<int:id_boleto>/desfazer-pagamento", view_func=self.desfazer, methods=["POST"])
        self.blueprint.add_url_rule("/boletos/usuario/<int:id_usuario>/processar", view_func=self.processar, methods=["POST"])

    def listar(self):
        return jsonify(self.service.listar()), 200

    def buscar(self, id_boleto):
        boleto = self.service.buscar_por_id(id_boleto)
        if boleto is None:
            return jsonify({"erro": "Boleto não encontrado."}), 404
        return jsonify(boleto), 200

    def criar(self):
        try:
            boleto = self.service.criar(request.get_json() or {})
            return jsonify(boleto), 201
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao salvar boleto."}), 500

    def atualizar(self, id_boleto):
        try:
            boleto = self.service.atualizar(id_boleto, request.get_json() or {})
            if boleto is None:
                return jsonify({"erro": "Boleto não encontrado."}), 404
            return jsonify(boleto), 200
        except ValueError as erro:
            db.session.rollback()
            return jsonify({"erro": str(erro)}), 400
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao atualizar boleto."}), 500

    def excluir(self, id_boleto):
        try:
            if not self.service.excluir(id_boleto):
                return jsonify({"erro": "Boleto não encontrado."}), 404
            return "", 204
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao excluir boleto."}), 500

    def listar_por_usuario(self, id_usuario):
        return jsonify(self.service.listar_por_usuario(id_usuario)), 200

    def proximos_vencimentos(self, id_usuario):
        return jsonify(self.service.proximos_vencimentos(id_usuario)), 200

    def _executar(self, acao, mensagem_erro):
        try:
            resultado = acao()
            if resultado is None:
                return jsonify({"erro": "Boleto não encontrado."}), 404
            return jsonify(resultado), 200
        except ValueError as erro:
            db.session.rollback()
            return jsonify({"erro": str(erro)}), 400
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": mensagem_erro}), 500

    def pagar(self, id_boleto):
        """Marca como pago e lança o gasto. Corpo opcional: {data_pagamento, valor}."""
        return self._executar(lambda: self.service.pagar(id_boleto, request.get_json(silent=True)),
                              "Erro ao registrar o pagamento.")

    def desfazer(self, id_boleto):
        return self._executar(lambda: self.service.desfazer_pagamento(id_boleto),
                              "Erro ao desfazer o pagamento.")

    def processar(self, id_usuario):
        """Débitos automáticos vencidos + avisos de vencimento (chamado ao abrir as telas)."""
        return self._executar(lambda: self.service.processar(id_usuario),
                              "Erro ao processar os boletos.")


boleto_controller = BoletoController()
boleto_bp = boleto_controller.blueprint
