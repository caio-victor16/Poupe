from sqlalchemy import text

from backend.extensions import db
from backend.models.boleto import Boleto


class BoletoRepository:
    def listar(self):
        return Boleto.listar_todos()

    def buscar_por_id(self, id_boleto):
        return Boleto.buscar_por_id(id_boleto)

    def inserir(self, boleto):
        boleto.salvar()

    def atualizar(self, boleto, dados):
        boleto.atualizar(
            codigo_barras=dados.get("codigo_barras"),
            valor=dados.get("valor"),
            vencimento=dados.get("vencimento"),
            status=dados.get("status"),
        )

    def excluir(self, boleto):
        boleto.deletar()

    def proximos_vencimentos(self, id_usuario):
        sql = text("CALL sp_boletos_proximos_vencimento(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(linha) for linha in linhas]
