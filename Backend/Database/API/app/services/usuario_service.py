from app.repositories.usuario_repository import UsuarioRepository


class UsuarioService:

    def __init__(self):
        self.repository = UsuarioRepository()

    def listar(self):
        return [u.to_dict() for u in self.repository.listar()]

    def buscar_por_id(self, id_usuario):
        usuario = self.repository.buscar_por_id(id_usuario)
        return usuario.to_dict() if usuario else None

    def inserir(self, usuario):
        self.repository.inserir(usuario)

    def atualizar(self, usuario):
        self.repository.atualizar(usuario)

    def excluir(self, id_usuario):
        self.repository.excluir(id_usuario)
