from flask import Blueprint, jsonify
from app.services.gasto_service import GastoService

gasto_bp = Blueprint("gasto", __name__)

service = GastoService()

@gasto_bp.route("/gastos/categorias/<int:id_usuario>")
def listar_gastos_categoria(id_usuario):

    dados = service.buscar_gastos_categoria(id_usuario)

    return jsonify(dados)