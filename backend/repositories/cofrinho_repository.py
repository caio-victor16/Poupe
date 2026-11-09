from sqlalchemy import text
from backend.extensions import db
class CofrinhoRepository:
    def simular(self, id_usuario, passo, dias):
        sql = text("CALL sp_cofrinho_simular(:id_usuario, :passo, :dias)")
        resultado = db.session.execute(sql, {
            "id_usuario": id_usuario,
            "passo": passo,
            "dias": dias,
        })
        linhas = resultado.mappings().all()
        resultado.close()
        return dict(linhas[0]) if linhas else None
