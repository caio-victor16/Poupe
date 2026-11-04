from backend.extensions import db


class RecorrenciaGasto(db.Model):
    __tablename__ = "recorrencia_gasto"

    id_recorrencia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    id_categoria = db.Column(
        db.Integer, db.ForeignKey("categoria.id_categoria"), nullable=False
    )
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    descricao = db.Column(db.String(255))
    frequencia = db.Column(db.String(20), nullable=False)
    proxima_data = db.Column(db.Date, nullable=False)
    dia_mes = db.Column(db.Integer, nullable=False)
    tipo_pagamento = db.Column(db.String(50))
    ativa = db.Column(db.Boolean, nullable=False, default=True)

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    def deletar(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def buscar_por_id(cls, id_recorrencia):
        return db.session.get(cls, id_recorrencia)

    @classmethod
    def listar_por_usuario(cls, id_usuario):
        return cls.query.filter_by(id_usuario=id_usuario).all()

    def to_dict(self):
        return {
            "id_recorrencia": self.id_recorrencia,
            "id_usuario": self.id_usuario,
            "id_categoria": self.id_categoria,
            "valor": float(self.valor),
            "descricao": self.descricao,
            "frequencia": self.frequencia,
            "proxima_data": self.proxima_data.isoformat(),
            "dia_mes": self.dia_mes,
            "tipo_pagamento": self.tipo_pagamento,
            "ativa": self.ativa,
        }