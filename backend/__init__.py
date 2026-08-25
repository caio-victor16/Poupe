import os

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from backend.config import Config
from backend.extensions import db, init_extensions
from backend.routes import register_routes
from backend.models.usuario import Usuario

# frontend/ é irmã de backend/ na raiz do projeto
FRONTEND_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)
    init_extensions(app)

    # Rotas da API (Blueprints de cada Controller)
    register_routes(app)

    # Garante que erros inesperados sempre voltem como JSON (nunca HTML)
    @app.errorhandler(Exception)
    def tratar_erro_generico(erro):
        if isinstance(erro, HTTPException):
            return jsonify({"erro": erro.description}), erro.code
        app.logger.exception(erro)
        return jsonify({"erro": f"Erro interno no servidor: {str(erro)}"}), 500

    # Rota de login "garantida" no nível do app (compatibilidade com o frontend)
    @app.route("/login", methods=["POST"])
    @app.route("/usuarios/login", methods=["POST"])
    def api_login():
        dados = request.get_json(silent=True) or {}
        email = dados.get("email")
        senha = dados.get("senha")

        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or usuario.senha != senha:
            return jsonify({"erro": "Email ou senha incorretos"}), 401

        return jsonify({
            "mensagem": "Login realizado com sucesso",
            "usuario_id": usuario.id_usuario,
            "nome": usuario.nome
        }), 200

    # Rotas para servir o frontend (HTML/CSS/JS estáticos)
    @app.route("/")
    @app.route("/login.html")
    def login_page():
        return send_from_directory(FRONTEND_FOLDER, "login.html")

    @app.route("/cadastro.html")
    def cadastro_page():
        return send_from_directory(FRONTEND_FOLDER, "cadastro.html")

    @app.route("/<path:filename>", methods=["GET"])
    def serve_static(filename):
        file_path = os.path.join(FRONTEND_FOLDER, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(FRONTEND_FOLDER, filename)
        return jsonify({"erro": "Arquivo não encontrado"}), 404

    return app
