import os

from flask import Flask, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException

from backend.config import Config
from backend.extensions import init_extensions
from backend.routes import register_routes

FRONTEND_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_extensions(app)
    register_routes(app)

    @app.errorhandler(Exception)
    def tratar_erro_generico(erro):
        if isinstance(erro, HTTPException):
            return jsonify({"erro": erro.description}), erro.code
        app.logger.exception(erro)
        return jsonify({"erro": f"Erro interno no servidor: {str(erro)}"}), 500

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
