from backend.extensions import db
from backend.models.recorrencia_gasto import RecorrenciaGasto


class RecorrenciaGastoRepository:
    def listar_por_usuario(self, id_usuario):
        return (
            RecorrenciaGasto.query
            .filter_by(id_usuario=id_usuario)
            .order_by(RecorrenciaGasto.proxima_data.asc())
            .all()
        )

    def buscar_por_id(self, id_recorrencia):
        return RecorrenciaGasto.query.get(id_recorrencia)

    def listar_vencidas(self, id_usuario, hoje):
        return (
            RecorrenciaGasto.query
            .filter(
                RecorrenciaGasto.id_usuario == id_usuario,
                RecorrenciaGasto.ativa.is_(True),
                RecorrenciaGasto.proxima_data <= hoje,
            )
            .order_by(RecorrenciaGasto.proxima_data.asc())
            .with_for_update()
            .all()
        )

    def salvar(self, recorrencia):
        db.session.add(recorrencia)
        db.session.commit()

    def excluir(self, recorrencia):
        db.session.delete(recorrencia)
        db.session.commit()