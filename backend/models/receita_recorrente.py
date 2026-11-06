from backend.extensions import db


class ReceitaRecorrente(db.Model):
    """Receita fixa mensal; o processamento gera registros em `receita`."""
    __tablename__ = "receita_recorrente"

    id_receita_recorrente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(60), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    dia_mes = db.Column(db.Integer, nullable=False)
    proxima_data = db.Column(db.Date, nullable=False)
    ativa = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {"id_receita_recorrente": self.id_receita_recorrente, "id_usuario": self.id_usuario,
                "descricao": self.descricao, "categoria": self.categoria,
                "valor": float(self.valor), "dia_mes": self.dia_mes,
                "proxima_data": self.proxima_data.isoformat(), "ativa": self.ativa}
