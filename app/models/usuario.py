class Usuario:

    def __init__(
        self,
        id_usuario=None,
        nome=None,
        email=None,
        telefone=None,
        senha=None,
        renda_mensal=None,
        limite_gastos=None
    ):
        self.id_usuario = id_usuario
        self.nome = nome
        self.email = email
        self.telefone = telefone
        self.senha = senha
        self.renda_mensal = renda_mensal
        self.limite_gastos = limite_gastos