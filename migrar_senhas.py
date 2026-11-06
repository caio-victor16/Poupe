"""Executar uma vez: python migrar_senhas.py. Não executa setup_db.py."""
from backend import create_app
from backend.extensions import db
from backend.models.usuario import Usuario
from backend.passwords import gerar_hash, senha_tem_hash


def migrar():
    quantidade = 0
    try:
        for usuario in Usuario.query.with_for_update().all():
            if not senha_tem_hash(usuario.senha):
                usuario.senha = gerar_hash(usuario.senha)
                quantidade += 1
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return quantidade


if __name__ == "__main__":
    with create_app().app_context():
        print(f"Senhas migradas: {migrar()}")
