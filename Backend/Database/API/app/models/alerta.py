from app.database import db


class Alerta(db.Model):
    __tablename__ = "alerta"

    id_alerta = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    tipo = db.Column(db.String(60))
    mensagem = db.Column(db.Text)
    data = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    visualizado = db.Column(db.Boolean, default=False)

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    def marcar_como_visualizado(self):
        self.visualizado = True
        db.session.commit()

    def deletar(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def listar_por_usuario(id_usuario):
        return (
            Alerta.query
            .filter_by(id_usuario=id_usuario)
            .order_by(Alerta.data.desc())
            .all()
        )

    @staticmethod
    def buscar_por_id(id_alerta):
        return Alerta.query.get(id_alerta)

    def to_dict(self):
        return {
            "id_alerta": self.id_alerta,
            "id_usuario": self.id_usuario,
            "tipo": self.tipo,
            "mensagem": self.mensagem,
            "data": self.data.isoformat() if self.data else None,
            "visualizado": self.visualizado,
        }
