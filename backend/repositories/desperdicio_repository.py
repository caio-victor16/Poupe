from sqlalchemy import text
from backend.extensions import db

class DesperdicioRepository:
    def categorias_acima_da_media(self, id_usuario):
        sql = text("""
            select
                categoria,
                mes_atual,
                round(media, 2) as media_mensal,
                round(mes_atual - media, 2) as excesso
            from (
                select
                    c.nome as categoria,
                    coalesce(sum(case when g.data >= date_format(curdate(), '%Y-%m-01')
                                      then g.valor end), 0) as mes_atual,
                    coalesce(sum(case when g.data < date_format(curdate(), '%Y-%m-01')
                                      then g.valor end), 0)
                    / nullif(count(distinct case when g.data < date_format(curdate(), '%Y-%m-01')
                                                 then date_format(g.data, '%Y-%m') end), 0) as media
                from gasto g
                inner join categoria c on c.id_categoria = g.id_categoria
                where g.id_usuario = :id_usuario
                  and g.data >= date_sub(date_format(curdate(), '%Y-%m-01'), interval 3 month)
                group by c.nome
            ) t
            where media >= 30
              and mes_atual > media
            order by excesso desc
        """)
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(linha) for linha in linhas]

    def assinaturas_provaveis(self, id_usuario):
        sql = text("""
            select
                lower(trim(descricao)) as descricao,
                count(distinct date_format(data, '%Y-%m')) as meses,
                round(avg(valor), 2) as valor_mensal,
                round(avg(valor) * 12, 2) as custo_anual
            from gasto
            where id_usuario = :id_usuario
              and trim(coalesce(descricao, '')) <> ''
              and data >= date_sub(curdate(), interval 4 month)
            group by lower(trim(descricao))
            having count(distinct date_format(data, '%Y-%m')) >= 2
               and count(*) <= count(distinct date_format(data, '%Y-%m'))
               and (max(valor) - min(valor)) <= avg(valor) * 0.1
            order by avg(valor) desc
        """)
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(linha) for linha in linhas]

    def gastos_duplicados(self, id_usuario):
        sql = text("""
            select descricao, valor, data, count(*) as vezes
            from gasto
            where id_usuario = :id_usuario
              and data >= date_sub(curdate(), interval 30 day)
            group by descricao, valor, data
            having count(*) > 1
            order by data desc
        """)
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(linha) for linha in linhas]