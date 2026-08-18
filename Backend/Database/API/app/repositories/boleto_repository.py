from app.database import db, get_raw_connection
from app.models.boleto import Boleto


class BoletoRepository:

    def listar(self):
        return Boleto.query.order_by(Boleto.vencimento).all()

    def buscar_por_id(self, id_boleto):
        return Boleto.query.get(id_boleto)

    def inserir(self, boleto):
        db.session.add(boleto)
        db.session.commit()

    def atualizar(self, boleto):

        existente = Boleto.query.get(boleto.id_boleto)

        if not existente:
            return

        existente.id_usuario = boleto.id_usuario
        existente.codigo_barras = boleto.codigo_barras
        existente.valor = boleto.valor
        existente.vencimento = boleto.vencimento
        existente.status = boleto.status

        db.session.commit()

    def excluir(self, id_boleto):

        boleto = Boleto.query.get(id_boleto)

        if boleto:
            db.session.delete(boleto)
            db.session.commit()

    def proximos_vencimentos(self, id_usuario):

        conn = get_raw_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.callproc("sp_boletos_proximos_vencimento", [id_usuario])

        resultado = []
        for result in cursor.stored_results():
            resultado.extend(result.fetchall())

        cursor.close()
        conn.close()

        return resultado
