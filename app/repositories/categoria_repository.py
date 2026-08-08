from app.database import get_connection


class CategoriaRepository:

    def listar(self):

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("select * from categoria order by nome")

        categorias = cursor.fetchall()

        cursor.close()
        conn.close()

        return categorias

    def buscar_por_id(self, id_categoria):

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "select * from categoria where id_categoria = %s",
            (id_categoria,)
        )

        categoria = cursor.fetchone()

        cursor.close()
        conn.close()

        return categoria

    def inserir(self, categoria):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "insert into categoria (nome) values (%s)",
            (categoria.nome,)
        )

        conn.commit()

        cursor.close()
        conn.close()

    def atualizar(self, categoria):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            update categoria
            set nome = %s
            where id_categoria = %s
            """,
            (
                categoria.nome,
                categoria.id_categoria
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

    def excluir(self, id_categoria):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "delete from categoria where id_categoria = %s",
            (id_categoria,)
        )

        conn.commit()

        cursor.close()
        conn.close()