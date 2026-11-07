from datetime import date

from backend.extensions import db


class Boleto(db.Model):
    """Conta a pagar (aba Boletos). "fixo" repete todo mês: ao pagar, o boleto
    do mês seguinte é criado. Com "debito_automatico", o pagamento é lançado
    sozinho no vencimento. Pagar cria o gasto correspondente (id_gasto)."""
    __tablename__ = "boleto"

    id_boleto = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    descricao = db.Column(db.String(100), nullable=False, default="")
    id_categoria = db.Column(db.Integer, db.ForeignKey("categoria.id_categoria"))
    codigo_barras = db.Column(db.String(100))          # opcional
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30))                  # pendente | pago
    fixo = db.Column(db.Boolean, nullable=False, default=False)
    debito_automatico = db.Column(db.Boolean, nullable=False, default=False)
    dia_vencimento = db.Column(db.Integer)             # dia original (31 → 30/28 nos meses curtos)
    data_pagamento = db.Column(db.Date)
    id_gasto = db.Column(db.Integer, db.ForeignKey("gasto.id_gasto", ondelete="SET NULL"))

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    def deletar(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def listar_todos():
        return Boleto.query.order_by(Boleto.vencimento.asc()).all()

    @staticmethod
    def listar_por_usuario(id_usuario):
        return (
            Boleto.query
            .filter_by(id_usuario=id_usuario)
            .order_by(Boleto.vencimento.asc(), Boleto.id_boleto.asc())
            .all()
        )

    @staticmethod
    def buscar_por_id(id_boleto):
        return db.session.get(Boleto, id_boleto)

    def situacao(self, hoje=None):
        if self.status == "pago":
            return "pago"
        return "vencido" if self.vencimento < (hoje or date.today()) else "pendente"

    def to_dict(self, hoje=None):
        hoje = hoje or date.today()
        return {
            "id_boleto": self.id_boleto,
            "id_usuario": self.id_usuario,
            "descricao": self.descricao,
            "id_categoria": self.id_categoria,
            "codigo_barras": self.codigo_barras,
            "valor": float(self.valor),
            "vencimento": self.vencimento.isoformat(),
            "status": self.status,
            "situacao": self.situacao(hoje),
            "dias_para_vencer": (self.vencimento - hoje).days,
            "fixo": bool(self.fixo),
            "debito_automatico": bool(self.debito_automatico),
            "data_pagamento": self.data_pagamento.isoformat() if self.data_pagamento else None,
            "id_gasto": self.id_gasto,
        }
