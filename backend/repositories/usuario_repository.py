from backend.models.usuario import Usuario


class UsuarioRepository:
    def listar(self):
        return Usuario.listar_todos()

    def buscar_por_id(self, id_usuario):
        return Usuario.buscar_por_id(id_usuario)

    def buscar_por_email(self, email):
        return Usuario.buscar_por_email(email)

    def inserir(self, usuario):
        usuario.salvar()

    def atualizar(self, usuario, dados):
        usuario.atualizar(
            nome=dados.get("nome"),
            email=dados.get("email"),
            telefone=dados.get("telefone"),
            senha=dados.get("senha"),
            renda_mensal=dados.get("renda_mensal"),
            limite_gastos=dados.get("limite_gastos"),
        )

    def excluir(self, usuario):
        usuario.deletar()
