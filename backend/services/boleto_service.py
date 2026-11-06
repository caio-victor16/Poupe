import re
from decimal import Decimal

from backend.crud import data_iso, dinheiro, escolha, validar_campos
from backend.extensions import db
from backend.models.boleto import Boleto
from backend.repositories.boleto_repository import BoletoRepository


def codigo_barras(valor, campo):
    """Código de barras (44) ou linha digitável (47/48); aceita espaços, pontos e
    hífens e grava só os dígitos."""
    if not isinstance(valor, str) or not re.fullmatch(r"[0-9 .\-]+", valor.strip() or "x"):
        raise ValueError(f"O campo '{campo}' deve conter só números (espaços, pontos e hífens são ignorados).")
    digitos = re.sub(r"\D", "", valor)
    if not 44 <= len(digitos) <= 48:
        raise ValueError(f"O campo '{campo}' deve ter de 44 a 48 dígitos.")
    return digitos


STATUS_BOLETO = {"pendente", "pago", "vencido"}
CAMPOS_BOLETO = {
    "codigo_barras": codigo_barras,
    "valor": dinheiro(Decimal("0"), incluir_minimo=False),
    "vencimento": data_iso,
}


class BoletoService:
    def __init__(self):
        self.repository = BoletoRepository()

    def listar(self):
        return [b.to_dict() for b in Boleto.listar_todos()]

    def listar_por_usuario(self, id_usuario):
        return [b.to_dict() for b in Boleto.listar_por_usuario(id_usuario)]

    def buscar_por_id(self, id_boleto):
        boleto = Boleto.buscar_por_id(id_boleto)
        return boleto.to_dict() if boleto else None

    def criar(self, dados):
        limpos = validar_campos(CAMPOS_BOLETO, dados)
        limpos.update(validar_campos({"status": escolha(STATUS_BOLETO)}, dados, parcial=True))
        limpos.setdefault("status", "pendente")
        if dados.get("id_usuario") is None:
            raise ValueError("O campo 'id_usuario' é obrigatório.")
        boleto = Boleto(id_usuario=dados["id_usuario"], **limpos)
        boleto.salvar()
        return boleto.to_dict()

    def atualizar(self, id_boleto, dados):
        boleto = Boleto.buscar_por_id(id_boleto)
        if boleto is None:
            return None
        limpos = validar_campos({**CAMPOS_BOLETO, "status": escolha(STATUS_BOLETO)}, dados, parcial=True)
        for campo, valor in limpos.items():
            setattr(boleto, campo, valor)
        db.session.commit()
        return boleto.to_dict()

    def excluir(self, id_boleto):
        boleto = Boleto.buscar_por_id(id_boleto)
        if boleto is None:
            return False
        boleto.deletar()
        return True

    def proximos_vencimentos(self, id_usuario):
        return self.repository.proximos_vencimentos(id_usuario)
