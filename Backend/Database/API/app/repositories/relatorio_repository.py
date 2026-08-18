from app.database import get_raw_connection


class RelatorioRepository:

    def financeiro(self, id_usuario):

        conn = get_raw_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.callproc("sp_relatorio_financeiro", [id_usuario])

        resultado = []
        for result in cursor.stored_results():
            resultado.extend(result.fetchall())

        cursor.close()
        conn.close()

        return resultado[0] if resultado else None
