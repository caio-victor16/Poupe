from backend.models.usuario import Usuario


class UsuarioService:
    def listar(self):
        return [u.to_dict() for u in Usuario.listar_todos()]

    def buscar_por_id(self, id_usuario):
        usuario = Usuario.buscar_por_id(id_usuario)
        return usuario.to_dict() if usuario else None

    def criar(self, dados):
        for campo in ["nome", "email", "senha", "renda_mensal", "limite_gastos"]:
            if not dados.get(campo):
                raise ValueError(f"O campo '{campo}' é obrigatório.")

        if Usuario.buscar_por_email(dados["email"]):
            raise ValueError("Já existe um usuário cadastrado com este e-mail.")

        usuario = Usuario(
            nome=dados["nome"],
            email=dados["email"],
            telefone=dados.get("telefone"),
            senha=dados["senha"],
            renda_mensal=dados["renda_mensal"],
            limite_gastos=dados["limite_gastos"],
        )
        usuario.salvar()
        return usuario.to_dict()

    def atualizar(self, id_usuario, dados):
        usuario = Usuario.buscar_por_id(id_usuario)
        if usuario is None:
            return None

        novo_email = dados.get("email")
        if novo_email:
            existente = Usuario.buscar_por_email(novo_email)
            if existente and existente.id_usuario != usuario.id_usuario:
                raise ValueError("Já existe outro usuário com este e-mail.")

        usuario.atualizar(
            nome=dados.get("nome"),
            email=dados.get("email"),
            telefone=dados.get("telefone"),
            senha=dados.get("senha"),
            renda_mensal=dados.get("renda_mensal"),
            limite_gastos=dados.get("limite_gastos"),
        )
        return usuario.to_dict()

    def excluir(self, id_usuario):
        usuario = Usuario.buscar_por_id(id_usuario)
        if usuario is None:
            return False
        usuario.deletar()
        return True

    def autenticar(self, email, senha):
        usuario = Usuario.buscar_por_email(email)
        if usuario is None or usuario.senha != senha:
            return None
        return usuario.to_dict()
