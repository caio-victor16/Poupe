from sqlalchemy import text

from backend.extensions import db


class ScoreRepository:
    def indicadores(self, id_usuario):
        sql = text("CALL sp_score_indicadores(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return dict(linhas[0]) if linhas else None
