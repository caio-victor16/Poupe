from sqlalchemy import text
from backend.extensions import db

class CaixaRepository:
    def calcular(self, id_usuario):
        sql = text("""
            select
                (select coalesce(sum(g.valor), 0) / 30
                   from gasto g
                  where g.id_usuario = u.id_usuario
                    and g.data >= date_sub(curdate(), interval 30 day)
                    and g.data <= curdate()
                ) as media_diaria,
                (select coalesce(sum(b.valor), 0)
                   from boleto b
                  where b.id_usuario = u.id_usuario
                    and coalesce(b.status, '') <> 'pago'
                    and b.vencimento <= date_add(curdate(), interval 30 day)
                ) as boletos_30_dias
            from usuario u
            where u.id_usuario = :id_usuario
        """)
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return dict(linhas[0]) if linhas else None