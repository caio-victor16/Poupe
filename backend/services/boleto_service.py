from backend.repositories.boleto_repository import BoletoRepository
from backend.models.boleto import Boleto


class BoletoService:
    def __init__(self):
        self.repository = BoletoRepository()

    def listar(self):
        return [b.to_dict() for b in self.repository.listar()]

    def listar_por_usuario(self, id_usuario):
        return [b.to_dict() for b in self.repository.listar_por_usuario(id_usuario)]

    def buscar_por_id(self, id_boleto):
        boleto = self.repository.buscar_por_id(id_boleto)
        return boleto.to_dict() if boleto else None

    def criar(self, dados):
        campos_obrigatorios = ["id_usuario", "codigo_barras", "valor", "vencimento"]
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                raise ValueError(f"O campo '{campo}' é obrigatório.")

        boleto = Boleto(
            id_usuario=dados["id_usuario"],
            codigo_barras=dados["codigo_barras"],
            valor=dados["valor"],
            vencimento=dados["vencimento"],
            status=dados.get("status", "pendente"),
        )

        self.repository.inserir(boleto)
        return boleto.to_dict()

    def atualizar(self, id_boleto, dados):
        boleto = self.repository.buscar_por_id(id_boleto)
        if boleto is None:
            return None

        self.repository.atualizar(boleto, dados)
        return boleto.to_dict()

    def excluir(self, id_boleto):
        boleto = self.repository.buscar_por_id(id_boleto)
        if boleto is None:
            return False

        self.repository.excluir(boleto)
        return True

    def proximos_vencimentos(self, id_usuario):
        return self.repository.proximos_vencimentos(id_usuario)
