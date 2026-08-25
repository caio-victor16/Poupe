"""
Extensões (add-ons) do Flask utilizadas pela aplicação.

Mantemos as instâncias aqui (fora do __init__.py) para evitar imports
circulares: Models, Repositories e Controllers importam `db` deste
módulo, e a Application Factory (backend/__init__.py) apenas inicializa
essas extensões dentro do app criado.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Instância única do ORM, usada por todas as Models e Repositories
db = SQLAlchemy()

# Instância única do CORS, usada para liberar o consumo da API pelo frontend
cors = CORS()


def init_extensions(app):
    """Inicializa todas as extensões na instância do Flask app."""
    db.init_app(app)
    cors.init_app(app)
