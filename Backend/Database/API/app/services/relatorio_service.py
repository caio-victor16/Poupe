from app.repositories.relatorio_repository import RelatorioRepository


class RelatorioService:

    def __init__(self):

        self.repository = RelatorioRepository()

    def financeiro(self, id_usuario):

        return self.repository.financeiro(
            id_usuario
        )