from sqlalchemy import text

from backend.extensions import db


class PrevisaoRepository:
    def calcular(self, id_usuario):
        sql = text("CALL sp_previsao_financeira(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return dict(linhas[0]) if linhas else None
