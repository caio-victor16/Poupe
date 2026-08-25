from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.services.alerta_service import AlertaService
from backend.extensions import db

alerta_bp = Blueprint("alerta", __name__)
service = AlertaService()


@alerta_bp.get("/alertas/usuario/<int:id_usuario>")
def listar_por_usuario(id_usuario):
    return jsonify(service.listar_por_usuario(id_usuario)), 200


@alerta_bp.get("/alertas/<int:id_alerta>")
def buscar(id_alerta):
    alerta = service.buscar_por_id(id_alerta)
    if alerta is None:
        return jsonify({"erro": "Alerta não encontrado."}), 404
    return jsonify(alerta), 200


@alerta_bp.post("/alertas")
def criar():
    try:
        dados = request.get_json() or {}
        alerta = service.criar(dados)
        return jsonify(alerta), 201

    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar alerta."}), 500


@alerta_bp.put("/alertas/<int:id_alerta>/visualizar")
def visualizar(id_alerta):
    alerta = service.marcar_como_visualizado(id_alerta)
    if alerta is None:
        return jsonify({"erro": "Alerta não encontrado."}), 404
    return jsonify(alerta), 200


@alerta_bp.delete("/alertas/<int:id_alerta>")
def excluir(id_alerta):
    try:
        deletado = service.excluir(id_alerta)
        if not deletado:
            return jsonify({"erro": "Alerta não encontrado."}), 404
        return "", 204

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao excluir alerta."}), 500


@alerta_bp.post("/alertas/usuario/<int:id_usuario>/gerar-limite")
def gerar_alerta_limite(id_usuario):
    try:
        service.gerar_alerta_limite(id_usuario)
        return jsonify({"mensagem": "Verificação de limite realizada."}), 200

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao gerar alerta de limite."}), 500
