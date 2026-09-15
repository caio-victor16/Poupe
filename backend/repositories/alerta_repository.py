from sqlalchemy import text
from backend.extensions import db


class AlertaRepository:
    def gerar_alerta_limite(self, id_usuario):
        sql = text("CALL sp_gerar_alerta_limite(:id_usuario)")
        db.session.execute(sql, {"id_usuario": id_usuario})
        db.session.commit()
