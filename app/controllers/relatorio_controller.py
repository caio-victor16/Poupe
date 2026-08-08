from flask import Blueprint
from flask import jsonify

from app.services.relatorio_service import RelatorioService


relatorio_bp = Blueprint(
    "relatorio",
    __name__
)

service = RelatorioService()


@relatorio_bp.route(
    "/relatorios/usuario/<int:id_usuario>",
    methods=["GET"]
)
def financeiro(id_usuario):

    resultado = service.financeiro(
        id_usuario
    )

    if resultado is None:

        return jsonify({
            "erro": "usuário não encontrado"
        }), 404

    return jsonify(resultado)