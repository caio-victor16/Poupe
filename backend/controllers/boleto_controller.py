from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.services.boleto_service import BoletoService
from backend.extensions import db

boleto_bp = Blueprint("boleto", __name__)
service = BoletoService()


@boleto_bp.get("/boletos")
def listar():
    return jsonify(service.listar()), 200


@boleto_bp.get("/boletos/<int:id_boleto>")
def buscar(id_boleto):
    boleto = service.buscar_por_id(id_boleto)
    if boleto is None:
        return jsonify({"erro": "Boleto não encontrado."}), 404
    return jsonify(boleto), 200


@boleto_bp.post("/boletos")
def criar():
    try:
        dados = request.get_json() or {}
        boleto = service.criar(dados)
        return jsonify(boleto), 201

    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar boleto."}), 500


@boleto_bp.put("/boletos/<int:id_boleto>")
def atualizar(id_boleto):
    try:
        dados = request.get_json() or {}
        boleto = service.atualizar(id_boleto, dados)

        if boleto is None:
            return jsonify({"erro": "Boleto não encontrado."}), 404

        return jsonify(boleto), 200

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao atualizar boleto."}), 500


@boleto_bp.delete("/boletos/<int:id_boleto>")
def excluir(id_boleto):
    try:
        deletado = service.excluir(id_boleto)
        if not deletado:
            return jsonify({"erro": "Boleto não encontrado."}), 404
        return "", 204

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao excluir boleto."}), 500


@boleto_bp.get("/boletos/usuario/<int:id_usuario>/proximos")
def proximos_vencimentos(id_usuario):
    return jsonify(service.proximos_vencimentos(id_usuario)), 200
