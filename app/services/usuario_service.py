from app.repositories.usuario_repository import UsuarioRepository


class UsuarioService:

    def __init__(self):
        self.repository = UsuarioRepository()

    def listar(self):
        return self.repository.listar()

    def buscar_por_id(self, id_usuario):
        return self.repository.buscar_por_id(id_usuario)

    def inserir(self, usuario):
        self.repository.inserir(usuario)

    def atualizar(self, usuario):
        self.repository.atualizar(usuario)

    def excluir(self, id_usuario):
        self.repository.excluir(id_usuario)

    def gastos_por_categoria(self, id_usuario):
        return self.repository.gastos_por_categoria(id_usuario)