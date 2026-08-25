from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.services.categoria_service import CategoriaService
from backend.extensions import db

categoria_bp = Blueprint("categoria", __name__)
service = CategoriaService()


@categoria_bp.get("/categorias")
def listar():
    return jsonify(service.listar()), 200


@categoria_bp.get("/categorias/<int:id_categoria>")
def buscar(id_categoria):
    categoria = service.buscar_por_id(id_categoria)
    if categoria is None:
        return jsonify({"erro": "Categoria não encontrada."}), 404
    return jsonify(categoria), 200


@categoria_bp.post("/categorias")
def criar():
    try:
        dados = request.get_json() or {}
        categoria = service.criar(dados)
        return jsonify(categoria), 201

    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar categoria."}), 500


@categoria_bp.put("/categorias/<int:id_categoria>")
def atualizar(id_categoria):
    try:
        dados = request.get_json() or {}
        categoria = service.atualizar(id_categoria, dados)

        if categoria is None:
            return jsonify({"erro": "Categoria não encontrada."}), 404

        return jsonify(categoria), 200

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao atualizar categoria."}), 500


@categoria_bp.delete("/categorias/<int:id_categoria>")
def excluir(id_categoria):
    try:
        deletado = service.excluir(id_categoria)
        if not deletado:
            return jsonify({"erro": "Categoria não encontrada."}), 404
        return "", 204

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao excluir categoria."}), 500
