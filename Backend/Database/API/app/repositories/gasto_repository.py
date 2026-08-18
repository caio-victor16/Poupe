from sqlalchemy import text

from app.database import db
from app.models.gasto import Gasto


class GastoRepository:
    def listar(self):
        return Gasto.listar_todos()

    def buscar_por_id(self, id_gasto):
        return Gasto.buscar_por_id(id_gasto)

    def inserir(self, gasto):
        gasto.salvar()

    def atualizar(self, gasto, dados):
        gasto.atualizar(
            id_categoria=dados.get("id_categoria"),
            valor=dados.get("valor"),
            data=dados.get("data"),
            descricao=dados.get("descricao"),
            recorrente=dados.get("recorrente"),
            tipo_pagamento=dados.get("tipo_pagamento"),
            status_gasto=dados.get("status_gasto"),
        )

    def excluir(self, gasto):
        gasto.deletar()

    def gastos_por_categoria(self, id_usuario):
        sql = text("CALL sp_gastos_categoria(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(linha) for linha in linhas]

    def gastos_por_periodo(self, id_usuario, data_inicio, data_fim):
        sql = text("CALL sp_gastos_por_periodo(:id_usuario, :inicio, :fim)")
        resultado = db.session.execute(sql, {
            "id_usuario": id_usuario,
            "inicio": data_inicio,
            "fim": data_fim,
        })
        linhas = resultado.mappings().all()
        resultado.close()
        return [dict(linha) for linha in linhas]

    def verificar_limite(self, id_usuario):
        sql = text("CALL sp_verificar_limite_gastos(:id_usuario)")
        resultado = db.session.execute(sql, {"id_usuario": id_usuario})
        linhas = resultado.mappings().all()
        resultado.close()
        return dict(linhas[0]) if linhas else None
