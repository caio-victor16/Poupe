from sqlalchemy import text

from backend.extensions import db


class ScoreRepository:
    def indicadores(self, id_usuario):
        sql = text("""
            select
                u.renda_mensal,
                u.limite_gastos,
                (select coalesce(sum(g.valor), 0)
                   from gasto g
                  where g.id_usuario = u.id_usuario
                    and g.data >= date_format(curdate(), '%Y-%m-01')
                    and g.data <  date_add(date_format(curdate(), '%Y-%m-01'), interval 1 month)
                ) as gasto_mes,
                (select count(*)
                   from boleto b
                  where b.id_usuario = u.id_usuario
                    and b.status <> 'pago'
                    and b.vencimento < curdate()
                ) as boletos_atrasados,
                (select count(*)
                   from boleto b
                  where b.id_usuario = u.id_usuario
                    and b.status <> 'pago'
                    and b.vencimento between curdate() and date_add(curdate(), interval 7 day)
                ) as boletos_na_semana
            from usuario u
            where u.id_usuario = :id_usuario
        """)
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return dict(linhas[0]) if linhas else None