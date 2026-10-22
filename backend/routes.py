
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
from backend.controllers.ia_controller import ia_bp
from backend.controllers.recorrencia_gasto_controller import recorrencia_gasto_bp
from backend.controllers.orcamento_controller import orcamento_bp
from backend.controllers.score_controller import score_bp 
from backend.controllers.caixa_controller import caixa_bp
from backend.controllers.desperdicio_controller import desperdicio_bp
from backend.controllers.cofrinho_controller import cofrinho_bp


def register_routes(app):
    """Registra todos os Blueprints (rotas) da API na aplicação Flask."""
    app.register_blueprint(usuario_bp)
    app.register_blueprint(gasto_bp)
    app.register_blueprint(categoria_bp)
    app.register_blueprint(boleto_bp)
    app.register_blueprint(alerta_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(previsao_bp)
    app.register_blueprint(ia_bp)
    app.register_blueprint(recorrencia_gasto_bp)
    app.register_blueprint(orcamento_bp)
    app.register_blueprint(score_bp)
    app.register_blueprint(caixa_bp)
    app.register_blueprint(desperdicio_bp)
    app.register_blueprint(cofrinho_bp)