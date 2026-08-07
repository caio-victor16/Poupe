from database import get_connection


class UsuarioRepository:

    def listar(self):

        conn = get_connection()

        cursor = conn.cursor(dictionary=True)

        cursor.execute("select * from usuario")

        usuarios = cursor.fetchall()

        cursor.close()

        conn.close()

        return usuarios


    def buscar_por_id(self, id_usuario):

        conn = get_connection()

        cursor = conn.cursor(dictionary=True)

        sql = "select * from usuario where id_usuario = %s"

        cursor.execute(sql, (id_usuario,))

        usuario = cursor.fetchone()

        cursor.close()

        conn.close()

        return usuario


    def inserir(self, usuario):

        conn = get_connection()

        cursor = conn.cursor()

        sql = """
        insert into usuario
        (nome,email,telefone,senha,renda_mensal,limite_gastos)
        values (%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(sql, (
            usuario.nome,
            usuario.email,
            usuario.telefone,
            usuario.senha,
            usuario.renda_mensal,
            usuario.limite_gastos
        ))

        conn.commit()

        cursor.close()

        conn.close()


    def atualizar(self, usuario):

        conn = get_connection()

        cursor = conn.cursor()

        sql = """
        update usuario
        set
        nome=%s,
        email=%s,
        telefone=%s,
        senha=%s,
        renda_mensal=%s,
        limite_gastos=%s
        where id_usuario=%s
        """

        cursor.execute(sql, (

            usuario.nome,

            usuario.email,

            usuario.telefone,

            usuario.senha,

            usuario.renda_mensal,

            usuario.limite_gastos,

            usuario.id_usuario

        ))

        conn.commit()

        cursor.close()

        conn.close()


    def excluir(self, id_usuario):

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute(
            "delete from usuario where id_usuario=%s",
            (id_usuario,)
        )

        conn.commit()

        cursor.close()

        conn.close()

    def gastos_por_categoria(self, id_usuario):

        conn = get_connection()

        cursor = conn.cursor(dictionary=True)

        cursor.callproc(
            "sp_gastos_categoria",
            [id_usuario]
        )

        resultado = []

        for result in cursor.stored_results():
            resultado.extend(result.fetchall())

        cursor.close()

        conn.close()

        return resultado
