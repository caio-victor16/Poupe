import os
from uuid import uuid4
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException
from backend.config import Config
from backend.extensions import init_extensions
from backend.routes import register_routes

FRONTEND_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)

# REV-003: só scripts da própria origem (lucide e Chart.js ficam em
# frontend/vendor/). 'unsafe-inline' continua porque as páginas ainda têm
# <script> e onclick embutidos; o ganho é bloquear qualquer script externo.
CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self' data:",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])
CABECALHOS_SEGURANCA = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
}


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_extensions(app)
    register_routes(app)
    from backend.auth import proteger_api
    app.before_request(proteger_api)

    @app.after_request
    def cabecalhos_seguranca(resposta):
        for nome, valor in CABECALHOS_SEGURANCA.items():
            resposta.headers.setdefault(nome, valor)
        return resposta

    @app.errorhandler(Exception)
    def tratar_erro_generico(erro):
        resposta_http = erro.get_response() if isinstance(erro, HTTPException) else None
        if resposta_http is not None and resposta_http.status_code < 500:
            # Mantém cabeçalhos como Allow (405) e Retry-After (429).
            resposta_http.set_data(app.json.dumps({"erro": erro.description}))
            resposta_http.mimetype = "application/json"
            return resposta_http

        referencia = uuid4().hex
        # Não registrar str(erro), exc_info ou dados da requisição: exceções de
        # banco podem incluir SQL, parâmetros, senhas e informações financeiras.
        app.logger.error(
            "Falha interna referencia=%s tipo=%s endpoint=%s",
            referencia, type(erro).__name__, request.endpoint,
        )
        resposta = jsonify({
            "erro": "Erro interno no servidor. Tente novamente mais tarde.",
            "referencia": referencia,
        })
        resposta.headers["Cache-Control"] = "no-store"
        if resposta_http is not None:
            resposta_http.set_data(resposta.get_data())
            resposta_http.mimetype = "application/json"
            resposta_http.headers["Cache-Control"] = "no-store"
            return resposta_http
        return resposta, 500

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
