from app.repositories.gasto_repository import GastoRepository
from app.models.gasto import Gasto


class GastoService:
    def __init__(self):
        self.repository = GastoRepository()

    def listar(self):
        return [g.to_dict() for g in self.repository.listar()]

    def buscar_por_id(self, id_gasto):
        gasto = self.repository.buscar_por_id(id_gasto)
        return gasto.to_dict() if gasto else None

    def criar(self, dados):
        campos_obrigatorios = ["id_usuario", "id_categoria", "valor", "data"]
        for campo in campos_obrigatorios:
            if dados.get(campo) is None:
                raise ValueError(f"O campo '{campo}' é obrigatório.")

        gasto = Gasto(
            id_usuario=dados["id_usuario"],
            id_categoria=dados["id_categoria"],
            valor=dados["valor"],
            data=dados["data"],
            descricao=dados.get("descricao"),
            recorrente=dados.get("recorrente", False),
            tipo_pagamento=dados.get("tipo_pagamento"),
            status_gasto=dados.get("status_gasto"),
        )

        self.repository.inserir(gasto)
        return gasto.to_dict()

    def atualizar(self, id_gasto, dados):
        gasto = self.repository.buscar_por_id(id_gasto)
        if gasto is None:
            return None

        self.repository.atualizar(gasto, dados)
        return gasto.to_dict()

    def excluir(self, id_gasto):
        gasto = self.repository.buscar_por_id(id_gasto)
        if gasto is None:
            return False

        self.repository.excluir(gasto)
        return True

    def gastos_por_categoria(self, id_usuario):
        return self.repository.gastos_por_categoria(id_usuario)

    def gastos_por_periodo(self, id_usuario, data_inicio, data_fim):
        return self.repository.gastos_por_periodo(id_usuario, data_inicio, data_fim)

    def verificar_limite(self, id_usuario):
        return self.repository.verificar_limite(id_usuario)
