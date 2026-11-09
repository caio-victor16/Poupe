from sqlalchemy import text
from backend.extensions import db

class DesperdicioRepository:
    def categorias_acima_da_media(self, id_usuario):
        sql = text("CALL sp_desperdicio_categorias_acima_media(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(linha) for linha in linhas]

    def assinaturas_provaveis(self, id_usuario):
        sql = text("CALL sp_desperdicio_assinaturas_provaveis(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(linha) for linha in linhas]

    def gastos_duplicados(self, id_usuario):
        sql = text("CALL sp_desperdicio_gastos_duplicados(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(linha) for linha in linhas]
