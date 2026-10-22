from sqlalchemy import text
from backend.extensions import db
class CofrinhoRepository:
    def simular(self, id_usuario, passo, dias):
        sql = text("""
            select
                coalesce(sum(ceil(valor / :passo) * :passo - valor), 0) as troco,
                count(*) as quantidade
            from gasto
            where id_usuario = :id_usuario
              and data >= date_sub(curdate(), interval :dias day)
              and data <= curdate()
        """)
        resultado = db.session.execute(sql, {
            "id_usuario": id_usuario,
            "passo": passo,
            "dias": dias,
        })
        linhas = resultado.mappings().all()
        resultado.close()
        return dict(linhas[0]) if linhas else None