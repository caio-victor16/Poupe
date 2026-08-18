from app.repositories.boleto_repository import BoletoRepository


class BoletoService:

    def __init__(self):
        self.repository = BoletoRepository()

    def listar(self):
        return [b.to_dict() for b in self.repository.listar()]

    def buscar_por_id(self, id_boleto):
        boleto = self.repository.buscar_por_id(id_boleto)
        return boleto.to_dict() if boleto else None

    def inserir(self, boleto):
        self.repository.inserir(boleto)

    def atualizar(self, boleto):
        self.repository.atualizar(boleto)

    def excluir(self, id_boleto):
        self.repository.excluir(id_boleto)

    def proximos_vencimentos(self, id_usuario):
        return self.repository.proximos_vencimentos(id_usuario)
