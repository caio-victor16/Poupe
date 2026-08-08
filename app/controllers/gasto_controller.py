from flask import Blueprint
from flask import jsonify
from flask import request

from app.models.gasto import Gasto
from app.services.gasto_service import GastoService


gasto_bp = Blueprint("gasto", __name__)

service = GastoService()


@gasto_bp.route("/gastos", methods=["GET"])
def listar():

    return jsonify(service.listar())


@gasto_bp.route("/gastos/<int:id_gasto>", methods=["GET"])
def buscar(id_gasto):

    gasto = service.buscar_por_id(id_gasto)

    if gasto is None:
        return jsonify({
            "erro": "gasto não encontrado"
        }), 404

    return jsonify(gasto)


@gasto_bp.route("/gastos", methods=["POST"])
def inserir():

    dados = request.get_json()

    gasto = Gasto(

        id_usuario=dados["id_usuario"],

        id_categoria=dados["id_categoria"],

        valor=dados["valor"],

        data=dados["data"],

        descricao=dados.get("descricao"),

        recorrente=dados.get("recorrente", False),

        tipo_pagamento=dados.get("tipo_pagamento"),

        status_gasto=dados.get("status_gasto")

    )

    service.inserir(gasto)

    return jsonify({
        "mensagem": "gasto cadastrado"
    }), 201


@gasto_bp.route("/gastos/<int:id_gasto>", methods=["PUT"])
def atualizar(id_gasto):

    dados = request.get_json()

    gasto = Gasto(

        id_gasto=id_gasto,

        id_usuario=dados["id_usuario"],

        id_categoria=dados["id_categoria"],

        valor=dados["valor"],

        data=dados["data"],

        descricao=dados.get("descricao"),

        recorrente=dados.get("recorrente", False),

        tipo_pagamento=dados.get("tipo_pagamento"),

        status_gasto=dados.get("status_gasto")

    )

    service.atualizar(gasto)

    return jsonify({
        "mensagem": "gasto atualizado"
    })


@gasto_bp.route("/gastos/<int:id_gasto>", methods=["DELETE"])
def excluir(id_gasto):

    service.excluir(id_gasto)

    return jsonify({
        "mensagem": "gasto removido"
    })


@gasto_bp.route(
    "/gastos/usuario/<int:id_usuario>/categorias",
    methods=["GET"]
)
def gastos_por_categoria(id_usuario):

    resultado = service.gastos_por_categoria(id_usuario)

    return jsonify(resultado)

@gasto_bp.route(
    "/gastos/usuario/<int:id_usuario>/periodo",
    methods=["GET"]
)
def gastos_por_periodo(id_usuario):

    data_inicio = request.args.get("inicio")

    data_fim = request.args.get("fim")

    if not data_inicio or not data_fim:

        return jsonify({
            "erro": "informe inicio e fim"
        }), 400

    resultado = service.gastos_por_periodo(
        id_usuario,
        data_inicio,
        data_fim
    )

    return jsonify(resultado)

@gasto_bp.route(
    "/gastos/usuario/<int:id_usuario>/limite",
    methods=["GET"]
)
def verificar_limite(id_usuario):

    resultado = service.verificar_limite(id_usuario)

    if resultado is None:

        return jsonify({
            "erro": "usuário não encontrado"
        }), 404

    return jsonify(resultado)