from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from app.services.usuario_service import UsuarioService
from app.database import db

usuario_bp = Blueprint("usuario", __name__)
service = UsuarioService()


@usuario_bp.get("/usuarios")
def listar():
    return jsonify(service.listar()), 200


@usuario_bp.get("/usuarios/<int:id_usuario>")
def buscar(id_usuario):
    usuario = service.buscar_por_id(id_usuario)
    if usuario is None:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    return jsonify(usuario), 200


@usuario_bp.post("/usuarios")
def criar():
    try:
        dados = request.get_json() or {}
        usuario = service.criar(dados)
        return jsonify(usuario), 201

    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar usuário no banco de dados."}), 500


@usuario_bp.put("/usuarios/<int:id_usuario>")
def atualizar(id_usuario):
    try:
        dados = request.get_json() or {}
        usuario = service.atualizar(id_usuario, dados)

        if usuario is None:
            return jsonify({"erro": "Usuário não encontrado."}), 404

        return jsonify(usuario), 200

    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao atualizar usuário."}), 500


@usuario_bp.delete("/usuarios/<int:id_usuario>")
def excluir(id_usuario):
    try:
        deletado = service.excluir(id_usuario)
        if not deletado:
            return jsonify({"erro": "Usuário não encontrado."}), 404
        return "", 204

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao excluir usuário."}), 500
