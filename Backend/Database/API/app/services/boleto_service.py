from app.repositories.boleto_repository import BoletoRepository


class BoletoService:

    def __init__(self):
        self.repository = BoletoRepository()

    def listar(self):
        return self.repository.listar()

    def buscar_por_id(self, id_boleto):
        return self.repository.buscar_por_id(id_boleto)

    def inserir(self, boleto):
        self.repository.inserir(boleto)

    def atualizar(self, boleto):
        self.repository.atualizar(boleto)

    def excluir(self, id_boleto):
        self.repository.excluir(id_boleto)

    def proximos_vencimentos(self, id_usuario):
        return self.repository.proximos_vencimentos(id_usuario)