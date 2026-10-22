from sqlalchemy import text

from backend.extensions import db


class OrcamentoRepository:
    def status_do_mes(self, id_usuario):
        sql = text("""
            select
                o.id_orcamento,
                o.id_categoria,
                c.nome as categoria,
                o.limite,
                coalesce(sum(g.valor), 0) as gasto_mes
            from orcamento_categoria o
            inner join categoria c on c.id_categoria = o.id_categoria
            left join gasto g
                on g.id_usuario = o.id_usuario
               and g.id_categoria = o.id_categoria
               and g.data >= date_format(curdate(), '%Y-%m-01')
               and g.data <  date_add(date_format(curdate(), '%Y-%m-01'), interval 1 month)
            where o.id_usuario = :id_usuario
            group by o.id_orcamento, o.id_categoria, c.nome, o.limite
            order by c.nome
        """)
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(l) for l in linhas]