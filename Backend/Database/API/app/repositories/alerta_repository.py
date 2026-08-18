from app.database import db, get_raw_connection
from app.models.alerta import Alerta


class AlertaRepository:

    def listar_por_usuario(self, id_usuario):
        return (
            Alerta.query
            .filter_by(id_usuario=id_usuario)
            .order_by(Alerta.data.desc())
            .all()
        )

    def buscar_por_id(self, id_alerta):
        return Alerta.query.get(id_alerta)

    def inserir(self, alerta):
        db.session.add(alerta)
        db.session.commit()

    def marcar_como_visualizado(self, id_alerta):

        alerta = Alerta.query.get(id_alerta)

        if alerta:
            alerta.visualizado = True
            db.session.commit()

    def excluir(self, id_alerta):

        alerta = Alerta.query.get(id_alerta)

        if alerta:
            db.session.delete(alerta)
            db.session.commit()

    def gerar_alerta_limite(self, id_usuario):

        conn = get_raw_connection()
        cursor = conn.cursor()

        cursor.callproc("sp_gerar_alerta_limite", [id_usuario])

        conn.commit()
        cursor.close()
        conn.close()
