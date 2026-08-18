from sqlalchemy import text

from app.database import db


class RelatorioRepository:
    def financeiro(self, id_usuario):
        sql = text("CALL sp_relatorio_financeiro(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return dict(linhas[0]) if linhas else None
