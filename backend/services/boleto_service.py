from backend.models.boleto import Boleto
from backend.repositories.boleto_repository import BoletoRepository


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
        for campo in ["id_usuario", "codigo_barras", "valor", "vencimento"]:
            if not dados.get(campo):
                raise ValueError(f"O campo '{campo}' é obrigatório.")

        boleto = Boleto(
            id_usuario=dados["id_usuario"],
            codigo_barras=dados["codigo_barras"],
            valor=dados["valor"],
            vencimento=dados["vencimento"],
            status=dados.get("status", "pendente"),
        )
        boleto.salvar()
        return boleto.to_dict()

    def atualizar(self, id_boleto, dados):
        boleto = Boleto.buscar_por_id(id_boleto)
        if boleto is None:
            return None
        boleto.atualizar(
            codigo_barras=dados.get("codigo_barras"),
            valor=dados.get("valor"),
            vencimento=dados.get("vencimento"),
            status=dados.get("status"),
        )
        return boleto.to_dict()

    def excluir(self, id_boleto):
        boleto = Boleto.buscar_por_id(id_boleto)
        if boleto is None:
            return False
        boleto.deletar()
        return True

    def proximos_vencimentos(self, id_usuario):
        return self.repository.proximos_vencimentos(id_usuario)
