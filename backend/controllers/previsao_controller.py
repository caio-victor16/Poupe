from flask import Blueprint, jsonify

from backend.services.previsao_service import PrevisaoService

previsao_bp = Blueprint("previsao", __name__)
service = PrevisaoService()


@previsao_bp.get("/previsoes/usuario/<int:id_usuario>")
def calcular(id_usuario):
    resultado = service.calcular(id_usuario)
    if resultado is None:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    return jsonify(resultado), 200
