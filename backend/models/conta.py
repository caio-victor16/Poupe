from backend.extensions import db


class Conta(db.Model):
    """Conta do caixa (corrente, poupança, dinheiro, investimentos)."""
    __tablename__ = "conta"

    id_conta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    saldo = db.Column(db.Numeric(10, 2), nullable=False)

    def to_dict(self):
        return {"id_conta": self.id_conta, "id_usuario": self.id_usuario, "nome": self.nome,
                "tipo": self.tipo, "saldo": float(self.saldo)}
