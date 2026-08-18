from flask import Flask, jsonify
from flask_cors import CORS

from app.config import Config
from app.database import db

from app.controllers.usuario_controller import usuario_bp
from app.controllers.gasto_controller import gasto_bp
from app.controllers.categoria_controller import categoria_bp
from app.controllers.boleto_controller import boleto_bp
from app.controllers.alerta_controller import alerta_bp
from app.controllers.relatorio_controller import relatorio_bp
from app.controllers.previsao_controller import previsao_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(usuario_bp)
    app.register_blueprint(gasto_bp)
    app.register_blueprint(categoria_bp)
    app.register_blueprint(boleto_bp)
    app.register_blueprint(alerta_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(previsao_bp)

    @app.get("/")
    def home():
        return jsonify({"mensagem": "API Poupe+ funcionando."})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
