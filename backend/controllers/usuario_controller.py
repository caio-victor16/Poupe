from flask import Blueprint, request, jsonify

from backend.services.usuario_service import UsuarioService

usuario_bp = Blueprint("usuario", __name__)
service = UsuarioService()


@usuario_bp.get("/usuarios")
def listar():
    return jsonify(service.listar()), 200


@usuario_bp.get("/usuarios/<int:usuario_id>")
def obter_usuario(usuario_id):
    usuario = service.buscar_por_id(usuario_id)
    if usuario is None:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    return jsonify(usuario), 200


# ROTA DE CADASTRO
@usuario_bp.post("/usuarios")
def cadastrar_usuario():
    try:
        dados = request.get_json() or {}
        usuario = service.criar(dados)
        return jsonify({
            "mensagem": "Usuário cadastrado com sucesso!",
            "usuario_id": usuario["id_usuario"],
        }), 201

    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400


@usuario_bp.put("/usuarios/<int:usuario_id>")
def atualizar_usuario(usuario_id):
    try:
        dados = request.get_json() or {}
        usuario = service.atualizar(usuario_id, dados)

        if usuario is None:
            return jsonify({"erro": "Usuário não encontrado."}), 404

        return jsonify(usuario), 200

    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400


@usuario_bp.delete("/usuarios/<int:usuario_id>")
def excluir_usuario(usuario_id):
    deletado = service.excluir(usuario_id)
    if not deletado:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    return "", 204


# ROTA DE LOGIN
# Mantemos as duas rotas (/login e /usuarios/login) pois o frontend
# tenta ambas por compatibilidade, mas agora só existe UMA implementação,
# reaproveitando o UsuarioService (sem duplicar a consulta ao banco).
@usuario_bp.post("/login")
@usuario_bp.post("/usuarios/login")
def login():
    dados = request.get_json(silent=True) or {}
    email = dados.get("email")
    senha = dados.get("senha")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    usuario = service.autenticar(email, senha)

    if usuario is None:
        return jsonify({"erro": "Email ou senha incorretos"}), 401

    return jsonify({
        "mensagem": "Login realizado com sucesso",
        "usuario_id": usuario["id_usuario"],
        "nome": usuario["nome"],
    }), 200
