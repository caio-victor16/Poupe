from decimal import Decimal

from backend.crud import (booleano, data_iso, dinheiro, id_existente, texto_opcional,
                          validar_campos)
from backend.extensions import db
from backend.models.categoria import Categoria
from backend.models.gasto import Gasto
from backend.repositories.gasto_repository import GastoRepository

# Item 12: todo valor gravado passa por validação (antes só se checava presença).
CAMPOS_OBRIGATORIOS = {
    "id_categoria": id_existente(Categoria, "categoria"),
    "valor": dinheiro(Decimal("0"), incluir_minimo=False),
    "data": data_iso,
}
CAMPOS_OPCIONAIS = {
    "descricao": texto_opcional(255),
    "recorrente": booleano,
    "tipo_pagamento": texto_opcional(50),
    "status_gasto": texto_opcional(30),
}


class GastoService:
    def __init__(self):
        self.repository = GastoRepository()

    def listar(self):
        return [g.to_dict() for g in Gasto.listar_todos()]

    def listar_por_usuario(self, id_usuario):
        return [g.to_dict() for g in Gasto.listar_por_usuario(id_usuario)]

    def buscar_por_id(self, id_gasto):
        gasto = Gasto.buscar_por_id(id_gasto)
        return gasto.to_dict() if gasto else None

    def criar(self, dados):
        limpos = validar_campos(CAMPOS_OBRIGATORIOS, dados)
        limpos.update(validar_campos(CAMPOS_OPCIONAIS, dados, parcial=True))
        limpos.setdefault("recorrente", False)
        if dados.get("id_usuario") is None:
            raise ValueError("O campo 'id_usuario' é obrigatório.")
        gasto = Gasto(id_usuario=dados["id_usuario"], **limpos)
        gasto.salvar()
        return gasto.to_dict()

    def atualizar(self, id_gasto, dados):
        gasto = Gasto.buscar_por_id(id_gasto)
        if gasto is None:
            return None
        # Valida tudo antes de alterar qualquer campo (parcial: só o que veio).
        limpos = validar_campos({**CAMPOS_OBRIGATORIOS, **CAMPOS_OPCIONAIS}, dados, parcial=True)
        for campo, valor in limpos.items():
            setattr(gasto, campo, valor)
        db.session.commit()
        return gasto.to_dict()

    def excluir(self, id_gasto):
        gasto = Gasto.buscar_por_id(id_gasto)
        if gasto is None:
            return False
        gasto.deletar()
        return True

    def gastos_por_categoria(self, id_usuario):
        return self.repository.gastos_por_categoria(id_usuario)

    def gastos_por_periodo(self, id_usuario, data_inicio, data_fim):
        inicio = data_iso(data_inicio, "inicio")
        fim = data_iso(data_fim, "fim")
        if inicio > fim:
            raise ValueError("A data 'inicio' deve ser anterior ou igual a 'fim'.")
        return self.repository.gastos_por_periodo(id_usuario, inicio, fim)

    def verificar_limite(self, id_usuario):
        return self.repository.verificar_limite(id_usuario)
