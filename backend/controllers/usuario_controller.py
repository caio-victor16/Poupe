from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.extensions import db
from backend.services.usuario_service import UsuarioService


class UsuarioController:
    def __init__(self):
        self.blueprint = Blueprint("usuario", __name__)
        self.service = UsuarioService()
        self._registrar_rotas()

    def _registrar_rotas(self):
        self.blueprint.add_url_rule("/usuarios", view_func=self.listar, methods=["GET"])
        self.blueprint.add_url_rule("/usuarios/<int:usuario_id>", view_func=self.obter_usuario, methods=["GET"])
        self.blueprint.add_url_rule("/usuarios", view_func=self.cadastrar_usuario, methods=["POST"])
        self.blueprint.add_url_rule("/usuarios/<int:usuario_id>", view_func=self.atualizar_usuario, methods=["PUT"])
        self.blueprint.add_url_rule("/usuarios/<int:usuario_id>", view_func=self.excluir_usuario, methods=["DELETE"])
        self.blueprint.add_url_rule("/login", view_func=self.login, methods=["POST"])
        self.blueprint.add_url_rule("/usuarios/login", view_func=self.login, methods=["POST"])

    def listar(self):
        return jsonify(self.service.listar()), 200

    def obter_usuario(self, usuario_id):
        usuario = self.service.buscar_por_id(usuario_id)
        if usuario is None:
            return jsonify({"erro": "Usuário não encontrado."}), 404
        return jsonify(usuario), 200

    def cadastrar_usuario(self):
        try:
            usuario = self.service.criar(request.get_json() or {})
            return jsonify({"mensagem": "Usuário cadastrado com sucesso!", "usuario_id": usuario["id_usuario"]}), 201
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao cadastrar usuário."}), 500

    def atualizar_usuario(self, usuario_id):
        try:
            usuario = self.service.atualizar(usuario_id, request.get_json() or {})
            if usuario is None:
                return jsonify({"erro": "Usuário não encontrado."}), 404
            return jsonify(usuario), 200
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao atualizar usuário."}), 500

    def excluir_usuario(self, usuario_id):
        try:
            if not self.service.excluir(usuario_id):
                return jsonify({"erro": "Usuário não encontrado."}), 404
            return "", 204
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"erro": "Erro ao excluir usuário."}), 500

    def login(self):
        dados = request.get_json(silent=True) or {}
        email = dados.get("email")
        senha = dados.get("senha")
        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400

        usuario = self.service.autenticar(email, senha)
        if usuario is None:
            return jsonify({"erro": "Email ou senha incorretos"}), 401

        return jsonify({
            "mensagem": "Login realizado com sucesso",
            "usuario_id": usuario["id_usuario"],
            "nome": usuario["nome"],
        }), 200


usuario_controller = UsuarioController()
usuario_bp = usuario_controller.blueprint
