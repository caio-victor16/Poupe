from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def init_extensions(app):
    db.init_app(app)
    # Frontend e API são servidos pela mesma origem; não habilitar CORS global.
