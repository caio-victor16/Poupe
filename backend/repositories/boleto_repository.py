from sqlalchemy import text
from backend.extensions import db


class BoletoRepository:
    def proximos_vencimentos(self, id_usuario):
        sql = text("CALL sp_boletos_proximos_vencimento(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(linha) for linha in linhas]
