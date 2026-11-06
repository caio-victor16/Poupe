from backend.extensions import db


class Receita(db.Model):
    __tablename__ = "receita"

    id_receita = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    descricao = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(60), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    data = db.Column(db.Date, nullable=False)

    def to_dict(self):
        return {
            "id_receita": self.id_receita,
            "id_usuario": self.id_usuario,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "valor": float(self.valor),
            "data": self.data.isoformat(),
        }
