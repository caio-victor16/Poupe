from flask import Blueprint
from flask import jsonify
from flask import request

from app.models.boleto import Boleto
from app.services.boleto_service import BoletoService


boleto_bp = Blueprint("boleto", __name__)

service = BoletoService()


@boleto_bp.route("/boletos", methods=["GET"])
def listar():

    return jsonify(service.listar())


@boleto_bp.route("/boletos/<int:id_boleto>", methods=["GET"])
def buscar(id_boleto):

    boleto = service.buscar_por_id(id_boleto)

    if boleto is None:

        return jsonify({
            "erro": "boleto não encontrado"
        }), 404

    return jsonify(boleto)


@boleto_bp.route("/boletos", methods=["POST"])
def inserir():

    dados = request.get_json()

    boleto = Boleto(
        id_usuario=dados["id_usuario"],
        codigo_barras=dados["codigo_barras"],
        valor=dados["valor"],
        vencimento=dados["vencimento"],
        status=dados.get("status", "pendente")
    )

    service.inserir(boleto)

    return jsonify({
        "mensagem": "boleto cadastrado"
    }), 201


@boleto_bp.route("/boletos/<int:id_boleto>", methods=["PUT"])
def atualizar(id_boleto):

    dados = request.get_json()

    boleto = Boleto(
        id_boleto=id_boleto,
        id_usuario=dados["id_usuario"],
        codigo_barras=dados["codigo_barras"],
        valor=dados["valor"],
        vencimento=dados["vencimento"],
        status=dados["status"]
    )

    service.atualizar(boleto)

    return jsonify({
        "mensagem": "boleto atualizado"
    })


@boleto_bp.route("/boletos/<int:id_boleto>", methods=["DELETE"])
def excluir(id_boleto):

    service.excluir(id_boleto)

    return jsonify({
        "mensagem": "boleto removido"
    })


@boleto_bp.route(
    "/boletos/usuario/<int:id_usuario>/proximos",
    methods=["GET"]
)
def proximos_vencimentos(id_usuario):

    resultado = service.proximos_vencimentos(
        id_usuario
    )

    return jsonify(resultado)