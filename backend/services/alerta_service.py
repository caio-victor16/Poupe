from backend.models.alerta import Alerta
from backend.repositories.alerta_repository import AlertaRepository


class AlertaService:
    def __init__(self):
        self.repository = AlertaRepository()

    def listar_por_usuario(self, id_usuario):
        return [a.to_dict() for a in Alerta.listar_por_usuario(id_usuario)]

    def buscar_por_id(self, id_alerta):
        alerta = Alerta.buscar_por_id(id_alerta)
        return alerta.to_dict() if alerta else None

    def criar(self, dados):
        for campo in ["id_usuario", "tipo", "mensagem"]:
            if not dados.get(campo):
                raise ValueError(f"O campo '{campo}' é obrigatório.")

        alerta = Alerta(
            id_usuario=dados["id_usuario"],
            tipo=dados["tipo"],
            mensagem=dados["mensagem"],
            visualizado=dados.get("visualizado", False),
        )
        alerta.salvar()
        return alerta.to_dict()

    def marcar_como_visualizado(self, id_alerta):
        alerta = Alerta.buscar_por_id(id_alerta)
        if alerta is None:
            return None
        alerta.marcar_como_visualizado()
        return alerta.to_dict()

    def excluir(self, id_alerta):
        alerta = Alerta.buscar_por_id(id_alerta)
        if alerta is None:
            return False
        alerta.deletar()
        return True

    def gerar_alerta_limite(self, id_usuario):
        self.repository.gerar_alerta_limite(id_usuario)
