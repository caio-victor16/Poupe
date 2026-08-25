from sqlalchemy import text

from backend.extensions import db
from backend.models.alerta import Alerta


class AlertaRepository:
    def listar_por_usuario(self, id_usuario):
        return Alerta.listar_por_usuario(id_usuario)

    def buscar_por_id(self, id_alerta):
        return Alerta.buscar_por_id(id_alerta)

    def inserir(self, alerta):
        alerta.salvar()

    def marcar_como_visualizado(self, alerta):
        alerta.marcar_como_visualizado()

    def excluir(self, alerta):
        alerta.deletar()

    def gerar_alerta_limite(self, id_usuario):
        sql = text("CALL sp_gerar_alerta_limite(:id_usuario)")
        db.session.execute(sql, {"id_usuario": id_usuario})
        db.session.commit()
