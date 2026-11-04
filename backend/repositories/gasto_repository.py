from sqlalchemy import text
from backend.extensions import db


class GastoRepository:
    def gastos_por_categoria(self, id_usuario):
        sql = text("CALL sp_gastos_categoria(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(linha) for linha in linhas]

    def gastos_por_periodo(self, id_usuario, data_inicio, data_fim):
        sql = text("CALL sp_gastos_por_periodo(:id_usuario, :inicio, :fim)")
        resultado = db.session.execute(sql, {
            "id_usuario": id_usuario,
            "inicio": data_inicio,
            "fim": data_fim,
        })
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(linha) for linha in linhas]

    def verificar_limite(self, id_usuario):
        sql = text("CALL sp_verificar_limite_gastos(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return dict(linhas[0]) if linhas else None
