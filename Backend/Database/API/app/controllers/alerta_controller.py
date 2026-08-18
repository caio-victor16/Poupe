from flask import Blueprint, jsonify, request

from app.models.alerta import Alerta
from app.services.alerta_service import AlertaService


alerta_bp = Blueprint("alerta", __name__)

service = AlertaService()


@alerta_bp.route("/alertas/usuario/<int:id_usuario>", methods=["GET"])
def listar_por_usuario(id_usuario):
    return jsonify(service.listar_por_usuario(id_usuario))


@alerta_bp.route("/alertas/<int:id_alerta>", methods=["GET"])
def buscar(id_alerta):

    alerta = service.buscar_por_id(id_alerta)

    if alerta is None:
        return jsonify({"erro": "alerta não encontrado"}), 404

    return jsonify(alerta)


@alerta_bp.route("/alertas", methods=["POST"])
def inserir():

    dados = request.get_json()

    alerta = Alerta(
        id_usuario=dados["id_usuario"],
        tipo=dados["tipo"],
        mensagem=dados["mensagem"],
        data=dados.get("data"),
        visualizado=dados.get("visualizado", False)
    )

    service.inserir(alerta)

    return jsonify({"mensagem": "alerta criado"}), 201


@alerta_bp.route("/alertas/<int:id_alerta>/visualizar", methods=["PUT"])
def visualizar(id_alerta):

    service.marcar_como_visualizado(id_alerta)

    return jsonify({"mensagem": "alerta marcado como visualizado"})


@alerta_bp.route("/alertas/<int:id_alerta>", methods=["DELETE"])
def excluir(id_alerta):

    service.excluir(id_alerta)

    return jsonify({"mensagem": "alerta removido"})


@alerta_bp.route(
    "/alertas/usuario/<int:id_usuario>/gerar-limite", methods=["POST"]
)
def gerar_alerta_limite(id_usuario):

    service.gerar_alerta_limite(id_usuario)

    return jsonify({"mensagem": "verificação de limite realizada"})
