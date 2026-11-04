from backend.models.usuario import Usuario
from backend.repositories.cofrinho_repository import CofrinhoRepository
class CofrinhoService:
    def __init__(self):
        self.repository = CofrinhoRepository()

    def simular(self, id_usuario, passo, dias):
        if passo not in (1, 5, 10):
            raise ValueError("O passo deve ser 1, 5 ou 10.")
        if not 7 <= dias <= 365:
            raise ValueError("O período deve estar entre 7 e 365 dias.")

        if Usuario.buscar_por_id(id_usuario) is None:
            return None

        dados = self.repository.simular(id_usuario, passo, dias)
        troco = float(dados["troco"])

        return {
            "passo": passo,
            "periodo_dias": dias,
            "gastos_arredondados": dados["quantidade"],
            "troco_acumulado": round(troco, 2),
            "projecao_12_meses": round(troco / dias * 365, 2),
        }