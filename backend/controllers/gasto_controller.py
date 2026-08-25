from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.services.gasto_service import GastoService
from backend.extensions import db

gasto_bp = Blueprint("gasto", __name__)
service = GastoService()


@gasto_bp.get("/gastos")
def listar():
    return jsonify(service.listar()), 200


@gasto_bp.get("/gastos/<int:id_gasto>")
def buscar(id_gasto):
    gasto = service.buscar_por_id(id_gasto)
    if gasto is None:
        return jsonify({"erro": "Gasto não encontrado."}), 404
    return jsonify(gasto), 200


@gasto_bp.post("/gastos")
def criar():
    try:
        dados = request.get_json() or {}
        gasto = service.criar(dados)
        return jsonify(gasto), 201

    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar gasto."}), 500


@gasto_bp.put("/gastos/<int:id_gasto>")
def atualizar(id_gasto):
    try:
        dados = request.get_json() or {}
        gasto = service.atualizar(id_gasto, dados)

        if gasto is None:
            return jsonify({"erro": "Gasto não encontrado."}), 404

        return jsonify(gasto), 200

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao atualizar gasto."}), 500


@gasto_bp.delete("/gastos/<int:id_gasto>")
def excluir(id_gasto):
    try:
        deletado = service.excluir(id_gasto)
        if not deletado:
            return jsonify({"erro": "Gasto não encontrado."}), 404
        return "", 204

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao excluir gasto."}), 500


@gasto_bp.get("/gastos/usuario/<int:id_usuario>/categorias")
def gastos_por_categoria(id_usuario):
    return jsonify(service.gastos_por_categoria(id_usuario)), 200


@gasto_bp.get("/gastos/usuario/<int:id_usuario>/periodo")
def gastos_por_periodo(id_usuario):
    data_inicio = request.args.get("inicio")
    data_fim = request.args.get("fim")

    if not data_inicio or not data_fim:
        return jsonify({"erro": "Informe os parâmetros 'inicio' e 'fim'."}), 400

    resultado = service.gastos_por_periodo(id_usuario, data_inicio, data_fim)
    return jsonify(resultado), 200


@gasto_bp.get("/gastos/usuario/<int:id_usuario>/limite")
def verificar_limite(id_usuario):
    resultado = service.verificar_limite(id_usuario)
    if resultado is None:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    return jsonify(resultado), 200
