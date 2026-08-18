from app.database import db


class Boleto(db.Model):
    __tablename__ = "boleto"

    id_boleto = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    codigo_barras = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30))

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    def atualizar(self, codigo_barras=None, valor=None,
                   vencimento=None, status=None):
        if codigo_barras is not None:
            self.codigo_barras = codigo_barras
        if valor is not None:
            self.valor = valor
        if vencimento is not None:
            self.vencimento = vencimento
        if status is not None:
            self.status = status

        db.session.commit()

    def deletar(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def listar_todos():
        return Boleto.query.order_by(Boleto.vencimento.asc()).all()

    @staticmethod
    def buscar_por_id(id_boleto):
        return Boleto.query.get(id_boleto)

    def to_dict(self):
        return {
            "id_boleto": self.id_boleto,
            "id_usuario": self.id_usuario,
            "codigo_barras": self.codigo_barras,
            "valor": float(self.valor),
            "vencimento": self.vencimento.isoformat(),
            "status": self.status,
        }
