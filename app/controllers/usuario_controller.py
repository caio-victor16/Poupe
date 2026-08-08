from flask import Blueprint
from flask import jsonify
from flask import request

from app.models.usuario import Usuario
from app.services.usuario_service import UsuarioService

usuario_bp = Blueprint("usuario", __name__)

service = UsuarioService()


@usuario_bp.route("/usuarios", methods=["GET"])
def listar():

    return jsonify(service.listar())


@usuario_bp.route("/usuarios/<int:id_usuario>", methods=["GET"])
def buscar(id_usuario):

    return jsonify(service.buscar_por_id(id_usuario))


@usuario_bp.route("/usuarios", methods=["POST"])
def inserir():

    dados = request.get_json()

    usuario = Usuario(

        nome=dados["nome"],

        email=dados["email"],

        telefone=dados["telefone"],

        senha=dados["senha"],

        renda_mensal=dados["renda_mensal"],

        limite_gastos=dados["limite_gastos"]

    )

    service.inserir(usuario)

    return jsonify({"mensagem": "usuário cadastrado"}), 201


@usuario_bp.route("/usuarios/<int:id_usuario>", methods=["PUT"])
def atualizar(id_usuario):

    dados = request.get_json()

    usuario = Usuario(

        id_usuario=id_usuario,

        nome=dados["nome"],

        email=dados["email"],

        telefone=dados["telefone"],

        senha=dados["senha"],

        renda_mensal=dados["renda_mensal"],

        limite_gastos=dados["limite_gastos"]

    )

    service.atualizar(usuario)

    return jsonify({"mensagem": "usuário atualizado"})


@usuario_bp.route("/usuarios/<int:id_usuario>", methods=["DELETE"])
def excluir(id_usuario):

    service.excluir(id_usuario)

    return jsonify({"mensagem": "usuário removido"})


@usuario_bp.route("/usuarios/<int:id_usuario>/gastos-categoria", methods=["GET"])
def gastos_categoria(id_usuario):

    return jsonify(service.gastos_por_categoria(id_usuario))