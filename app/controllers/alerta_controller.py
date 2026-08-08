from flask import Blueprint
from flask import jsonify
from flask import request

from app.models.alerta import Alerta
from app.services.alerta_service import AlertaService


alerta_bp = Blueprint(
    "alerta",
    __name__
)

service = AlertaService()


@alerta_bp.route(
    "/alertas/usuario/<int:id_usuario>",
    methods=["GET"]
)
def listar_por_usuario(id_usuario):

    return jsonify(
        service.listar_por_usuario(id_usuario)
    )


@alerta_bp.route(
    "/alertas/<int:id_alert>",
    methods=["GET"]
)
def buscar(id_alert):

    alerta = service.buscar_por_id(id_alert)

    if alerta is None:

        return jsonify({
            "erro": "alerta não encontrado"
        }), 404

    return jsonify(alerta)


@alerta_bp.route(
    "/alertas",
    methods=["POST"]
)
def inserir():

    dados = request.get_json()

    alerta = Alerta(
        id_usuario=dados["id_usuario"],
        tipo=dados["tipo"],
        mensagem=dados["mensagem"],
        data=dados.get("data"),
        visualizado=dados.get(
            "visualizado",
            False
        )
    )

    service.inserir(alerta)

    return jsonify({
        "mensagem": "alerta criado"
    }), 201


@alerta_bp.route(
    "/alertas/<int:id_alert>/visualizar",
    methods=["PUT"]
)
def visualizar(id_alert):

    service.marcar_como_visualizado(id_alert)

    return jsonify({
        "mensagem": "alerta marcado como visualizado"
    })


@alerta_bp.route(
    "/alertas/<int:id_alert>",
    methods=["DELETE"]
)
def excluir(id_alert):

    service.excluir(id_alert)

    return jsonify({
        "mensagem": "alerta removido"
    })

@alerta_bp.route(
    "/alertas/usuario/<int:id_usuario>/gerar-limite",
    methods=["POST"]
)
def gerar_alerta_limite(id_usuario):

    service.gerar_alerta_limite(
        id_usuario
    )

    return jsonify({
        "mensagem": "verificação de limite realizada"
    })