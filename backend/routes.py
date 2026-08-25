"""
Registro centralizado das rotas (Blueprints) da API.

Cada Controller define seu próprio Blueprint com as rotas HTTP de um
recurso (usuários, gastos, categorias, boletos, alertas, relatórios e
previsões). Este módulo apenas importa e registra todos eles na
aplicação Flask, mantendo o backend/__init__.py enxuto.
"""

from backend.controllers.usuario_controller import usuario_bp
from backend.controllers.gasto_controller import gasto_bp
from backend.controllers.categoria_controller import categoria_bp
from backend.controllers.boleto_controller import boleto_bp
from backend.controllers.alerta_controller import alerta_bp
from backend.controllers.relatorio_controller import relatorio_bp
from backend.controllers.previsao_controller import previsao_bp


def register_routes(app):
    """Registra todos os Blueprints (rotas) da API na aplicação Flask."""
    app.register_blueprint(usuario_bp)
    app.register_blueprint(gasto_bp)
    app.register_blueprint(categoria_bp)
    app.register_blueprint(boleto_bp)
    app.register_blueprint(alerta_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(previsao_bp)
