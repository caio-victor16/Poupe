from app.repositories.alerta_repository import AlertaRepository


class AlertaService:

    def __init__(self):
        self.repository = AlertaRepository()

    def listar_por_usuario(self, id_usuario):
        return [
            a.to_dict()
            for a in self.repository.listar_por_usuario(id_usuario)
        ]

    def buscar_por_id(self, id_alerta):
        alerta = self.repository.buscar_por_id(id_alerta)
        return alerta.to_dict() if alerta else None

    def inserir(self, alerta):
        self.repository.inserir(alerta)

    def marcar_como_visualizado(self, id_alerta):
        self.repository.marcar_como_visualizado(id_alerta)

    def excluir(self, id_alerta):
        self.repository.excluir(id_alerta)

    def gerar_alerta_limite(self, id_usuario):
        self.repository.gerar_alerta_limite(id_usuario)
