from flask import Blueprint
from flask import jsonify
from flask import request

from app.models.categoria import Categoria
from app.services.categoria_service import CategoriaService


categoria_bp = Blueprint("categoria", __name__)

service = CategoriaService()


@categoria_bp.route("/categorias", methods=["GET"])
def listar():

    return jsonify(service.listar())


@categoria_bp.route("/categorias/<int:id_categoria>", methods=["GET"])
def buscar(id_categoria):

    categoria = service.buscar_por_id(id_categoria)

    if categoria is None:

        return jsonify({
            "erro": "categoria não encontrada"
        }), 404

    return jsonify(categoria)


@categoria_bp.route("/categorias", methods=["POST"])
def inserir():

    dados = request.get_json()

    categoria = Categoria(
        nome=dados["nome"]
    )

    service.inserir(categoria)

    return jsonify({
        "mensagem": "categoria cadastrada"
    }), 201


@categoria_bp.route("/categorias/<int:id_categoria>", methods=["PUT"])
def atualizar(id_categoria):

    dados = request.get_json()

    categoria = Categoria(
        id_categoria=id_categoria,
        nome=dados["nome"]
    )

    service.atualizar(categoria)

    return jsonify({
        "mensagem": "categoria atualizada"
    })


@categoria_bp.route("/categorias/<int:id_categoria>", methods=["DELETE"])
def excluir(id_categoria):

    service.excluir(id_categoria)

    return jsonify({
        "mensagem": "categoria removida"
    })