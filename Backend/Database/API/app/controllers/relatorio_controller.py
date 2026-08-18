from flask import Blueprint, jsonify

from app.services.relatorio_service import RelatorioService

relatorio_bp = Blueprint("relatorio", __name__)
service = RelatorioService()


@relatorio_bp.get("/relatorios/usuario/<int:id_usuario>")
def financeiro(id_usuario):
    resultado = service.financeiro(id_usuario)
    if resultado is None:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    return jsonify(resultado), 200
