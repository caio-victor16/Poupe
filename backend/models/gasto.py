from backend.extensions import db


class Gasto(db.Model):
    __tablename__ = "gasto"

    id_gasto = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    id_categoria = db.Column(
        db.Integer, db.ForeignKey("categoria.id_categoria"), nullable=False
    )
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    data = db.Column(db.Date, nullable=False)
    descricao = db.Column(db.String(255))
    recorrente = db.Column(db.Boolean, default=False)
    tipo_pagamento = db.Column(db.String(50))
    status_gasto = db.Column(db.String(30))

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    def atualizar(self, id_categoria=None, valor=None, data=None,
                   descricao=None, recorrente=None,
                   tipo_pagamento=None, status_gasto=None):
        if id_categoria is not None:
            self.id_categoria = id_categoria
        if valor is not None:
            self.valor = valor
        if data is not None:
            self.data = data
        if descricao is not None:
            self.descricao = descricao
        if recorrente is not None:
            self.recorrente = recorrente
        if tipo_pagamento is not None:
            self.tipo_pagamento = tipo_pagamento
        if status_gasto is not None:
            self.status_gasto = status_gasto

        db.session.commit()

    def deletar(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def listar_todos():
        return Gasto.query.order_by(Gasto.data.desc()).all()

    @staticmethod
    def buscar_por_id(id_gasto):
        return Gasto.query.get(id_gasto)

    def to_dict(self):
        return {
            "id_gasto": self.id_gasto,
            "id_usuario": self.id_usuario,
            "id_categoria": self.id_categoria,
            "valor": float(self.valor),
            "data": self.data.isoformat(),
            "descricao": self.descricao,
            "recorrente": self.recorrente,
            "tipo_pagamento": self.tipo_pagamento,
            "status_gasto": self.status_gasto,
        }
