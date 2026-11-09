from sqlalchemy import text

from backend.extensions import db


class OrcamentoRepository:
    def status_do_mes(self, id_usuario):
        sql = text("CALL sp_orcamento_status_mes(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(l) for l in linhas]
