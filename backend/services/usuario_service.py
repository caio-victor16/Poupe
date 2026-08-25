from backend.repositories.usuario_repository import UsuarioRepository
from backend.models.usuario import Usuario


class UsuarioService:
    def __init__(self):
        self.repository = UsuarioRepository()

    def listar(self):
        return [u.to_dict() for u in self.repository.listar()]

    def buscar_por_id(self, id_usuario):
        usuario = self.repository.buscar_por_id(id_usuario)
        return usuario.to_dict() if usuario else None

    def criar(self, dados):
        campos_obrigatorios = [
            "nome", "email", "senha", "renda_mensal", "limite_gastos"
        ]
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                raise ValueError(f"O campo '{campo}' é obrigatório.")

        if self.repository.buscar_por_email(dados["email"]):
            raise ValueError("Já existe um usuário cadastrado com este e-mail.")

        usuario = Usuario(
            nome=dados["nome"],
            email=dados["email"],
            telefone=dados.get("telefone"),
            senha=dados["senha"],
            renda_mensal=dados["renda_mensal"],
            limite_gastos=dados["limite_gastos"],
        )

        self.repository.inserir(usuario)
        return usuario.to_dict()

    def atualizar(self, id_usuario, dados):
        usuario = self.repository.buscar_por_id(id_usuario)
        if usuario is None:
            return None

        novo_email = dados.get("email")
        if novo_email:
            existente = self.repository.buscar_por_email(novo_email)
            if existente and existente.id_usuario != usuario.id_usuario:
                raise ValueError("Já existe outro usuário com este e-mail.")

        self.repository.atualizar(usuario, dados)
        return usuario.to_dict()

    def excluir(self, id_usuario):
        usuario = self.repository.buscar_por_id(id_usuario)
        if usuario is None:
            return False

        self.repository.excluir(usuario)
        return True
