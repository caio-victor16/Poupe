from flask import Blueprint
from flask import jsonify

from app.services.previsao_service import PrevisaoService


previsao_bp = Blueprint(
    "previsao",
    __name__
)

service = PrevisaoService()


@previsao_bp.route(
    "/previsoes/usuario/<int:id_usuario>",
    methods=["GET"]
)
def calcular(id_usuario):

    resultado = service.calcular(
        id_usuario
    )

    if resultado is None:

        return jsonify({
            "erro": "usuário não encontrado"
        }), 404

    return jsonify(resultado)