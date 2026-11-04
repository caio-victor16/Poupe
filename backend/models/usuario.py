from backend.extensions import db


class Usuario(db.Model):
    __tablename__ = "usuario"

    id_usuario = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    telefone = db.Column(db.String(20))
    senha = db.Column(db.String(255), nullable=False)
    renda_mensal = db.Column(db.Numeric(10, 2), nullable=False)
    limite_gastos = db.Column(db.Numeric(10, 2), nullable=False)

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    def atualizar(self, nome=None, email=None, telefone=None,
                   senha=None, renda_mensal=None, limite_gastos=None):
        if nome is not None:
            self.nome = nome
        if email is not None:
            self.email = email
        if telefone is not None:
            self.telefone = telefone
        if senha is not None:
            self.senha = senha
        if renda_mensal is not None:
            self.renda_mensal = renda_mensal
        if limite_gastos is not None:
            self.limite_gastos = limite_gastos

        db.session.commit()

    def deletar(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def listar_todos():
        return Usuario.query.order_by(Usuario.id_usuario.asc()).all()

    @staticmethod
    def buscar_por_id(id_usuario):
        return Usuario.query.get(id_usuario)

    @staticmethod
    def buscar_por_email(email):
        return Usuario.query.filter_by(email=email).first()

    def to_dict(self):
        return {
            "id_usuario": self.id_usuario,
            "nome": self.nome,
            "email": self.email,
            "telefone": self.telefone,
            "renda_mensal": float(self.renda_mensal),
            "limite_gastos": float(self.limite_gastos),
        }
