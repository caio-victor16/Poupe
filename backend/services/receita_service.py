from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from backend.extensions import db
from backend.models.receita import Receita


class ReceitaService:
    # Mesmas opções do formulário de receitas.html.
    CATEGORIAS = {"Salário", "Trabalho", "Investimentos", "Outros"}
    VALOR_MAXIMO = Decimal("99999999.99")  # decimal(10,2)

    @staticmethod
    def _texto(valor, campo, maximo):
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"O campo '{campo}' é obrigatório.")
        valor = valor.strip()
        if len(valor) > maximo:
            raise ValueError(f"O campo '{campo}' deve ter até {maximo} caracteres.")
        return valor

    @classmethod
    def _categoria(cls, valor):
        if valor not in cls.CATEGORIAS:
            opcoes = ", ".join(sorted(cls.CATEGORIAS))
            raise ValueError(f"Categoria inválida. Use: {opcoes}.")
        return valor

    @classmethod
    def _valor(cls, valor):
        if isinstance(valor, bool):
            raise ValueError("O campo 'valor' deve ser um número válido.")
        try:
            numero = Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError) as erro:
            raise ValueError("O campo 'valor' deve ser um número válido.") from erro
        if not numero.is_finite() or numero <= 0:
            raise ValueError("O campo 'valor' deve ser maior que zero.")
        if numero > cls.VALOR_MAXIMO:
            raise ValueError("O campo 'valor' é grande demais.")
        return numero.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _data(valor):
        try:
            return date.fromisoformat(valor)
        except (TypeError, ValueError) as erro:
            raise ValueError("O campo 'data' deve estar no formato AAAA-MM-DD.") from erro

    def _validar(self, dados, parcial=False):
        if not isinstance(dados, dict):
            raise ValueError("O corpo da requisição deve ser um objeto JSON.")
        regras = {
            "descricao": lambda v: self._texto(v, "descricao", 255),
            "categoria": self._categoria,
            "valor": self._valor,
            "data": self._data,
        }
        limpos = {}
        for campo, regra in regras.items():
            if campo in dados:
                limpos[campo] = regra(dados[campo])
            elif not parcial:
                raise ValueError(f"O campo '{campo}' é obrigatório.")
        return limpos

    def listar_por_usuario(self, id_usuario):
        receitas = (
            Receita.query.filter_by(id_usuario=id_usuario)
            .order_by(Receita.data.desc(), Receita.id_receita.desc())
            .all()
        )
        return [r.to_dict() for r in receitas]

    def criar(self, dados):
        limpos = self._validar(dados)
        receita = Receita(id_usuario=int(dados["id_usuario"]), **limpos)
        db.session.add(receita)
        db.session.commit()
        return receita.to_dict()

    def atualizar(self, id_receita, dados):
        receita = db.session.get(Receita, id_receita)
        if receita is None:
            return None
        for campo, valor in self._validar(dados, parcial=True).items():
            setattr(receita, campo, valor)
        db.session.commit()
        return receita.to_dict()

    def excluir(self, id_receita):
        receita = db.session.get(Receita, id_receita)
        if receita is None:
            return False
        db.session.delete(receita)
        db.session.commit()
        return True
