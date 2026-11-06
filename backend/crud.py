"""CRUD simples por usuário: validação declarativa + blueprint com 4 rotas.

Usado por contas, metas e cofrinhos (item 10c). Cada recurso declara seus
campos; as rotas seguem o padrão já protegido por backend/auth.py:

    POST   /<prefixo>                       cria para o usuário da sessão
    GET    /<prefixo>/usuario/<id_usuario>  lista do usuário
    PUT    /<prefixo>/<pk>                  altera (parcial)
    DELETE /<prefixo>/<pk>                  exclui

O blueprint e o modelo também precisam ser registrados em backend/auth.py
(CRIACAO, RECURSOS e POR_USUARIO); sem isso as rotas são negadas.
"""
import re
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend.extensions import db

LIMITE_DINHEIRO = Decimal("99999999.99")  # decimal(10,2)


# ---- validadores: recebem o valor bruto e o nome do campo -------------------

def texto(maximo):
    def validar(valor, campo):
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"O campo '{campo}' é obrigatório.")
        valor = valor.strip()
        if len(valor) > maximo:
            raise ValueError(f"O campo '{campo}' deve ter até {maximo} caracteres.")
        return valor
    return validar


def escolha(opcoes):
    def validar(valor, campo):
        if valor not in opcoes:
            raise ValueError(f"O campo '{campo}' deve ser: {', '.join(sorted(opcoes))}.")
        return valor
    return validar


def dinheiro(minimo=None, incluir_minimo=True):
    """Valor em reais com 2 casas (meio centavo para cima)."""
    def validar(valor, campo):
        if isinstance(valor, bool) or valor is None:
            raise ValueError(f"O campo '{campo}' deve ser um número válido.")
        try:
            numero = Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError) as erro:
            raise ValueError(f"O campo '{campo}' deve ser um número válido.") from erro
        if not numero.is_finite() or abs(numero) > LIMITE_DINHEIRO:
            raise ValueError(f"O campo '{campo}' deve ser um número válido.")
        if minimo is not None:
            if numero < minimo or (numero == minimo and not incluir_minimo):
                regra = "maior ou igual a" if incluir_minimo else "maior que"
                raise ValueError(f"O campo '{campo}' deve ser {regra} {minimo}.")
        return numero.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return validar


def inteiro(minimo, maximo):
    def validar(valor, campo):
        if isinstance(valor, bool) or not isinstance(valor, (int, str)):
            raise ValueError(f"O campo '{campo}' deve ser um número inteiro.")
        try:
            numero = int(valor)
        except ValueError as erro:
            raise ValueError(f"O campo '{campo}' deve ser um número inteiro.") from erro
        if not minimo <= numero <= maximo:
            raise ValueError(f"O campo '{campo}' deve estar entre {minimo} e {maximo}.")
        return numero
    return validar


def data_iso(valor, campo):
    try:
        data = date.fromisoformat(valor)
    except (TypeError, ValueError) as erro:
        raise ValueError(f"O campo '{campo}' deve estar no formato AAAA-MM-DD.") from erro
    # Evita datas absurdas digitadas por engano (ano 0026, 20260 etc.).
    if not 1900 <= data.year <= 2100:
        raise ValueError(f"O campo '{campo}' deve ter ano entre 1900 e 2100.")
    return data


def texto_opcional(maximo):
    """None ou texto vazio viram None; senão, igual a texto(maximo)."""
    obrigatorio = texto(maximo)

    def validar(valor, campo):
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            return None
        return obrigatorio(valor, campo)
    return validar


def booleano(valor, campo):
    if not isinstance(valor, bool):
        raise ValueError(f"O campo '{campo}' deve ser verdadeiro ou falso.")
    return valor


EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
TELEFONE = re.compile(r"[0-9()+\-\s]{8,20}")


def email(valor, campo):
    valor = texto(150)(valor, campo)
    if not EMAIL.fullmatch(valor):
        raise ValueError(f"O campo '{campo}' deve ser um e-mail válido.")
    return valor


def telefone(valor, campo):
    valor = texto_opcional(20)(valor, campo)
    if valor is not None and not TELEFONE.fullmatch(valor):
        raise ValueError(f"O campo '{campo}' deve conter só números, espaços, parênteses, + e -.")
    return valor


def id_existente(modelo, nome="registro"):
    """Inteiro positivo que existe na tabela do modelo (ex.: categoria)."""
    def validar(valor, campo):
        numero = inteiro(1, 2_147_483_647)(valor, campo)
        if db.session.get(modelo, numero) is None:
            raise ValueError(f"{nome.capitalize()} informada não existe.")
        return numero
    return validar


def validar_campos(campos, dados, parcial=False):
    """campos: {nome: validador}. Ignora chaves desconhecidas (ex.: id_usuario)."""
    if not isinstance(dados, dict):
        raise ValueError("O corpo da requisição deve ser um objeto JSON.")
    limpos = {}
    for nome, validador in campos.items():
        if nome in dados:
            limpos[nome] = validador(dados[nome], nome)
        elif not parcial:
            raise ValueError(f"O campo '{nome}' é obrigatório.")
    return limpos


# ---- blueprint genérico ------------------------------------------------------

class CrudSimples:
    def __init__(self, nome, prefixo, modelo, pk, campos, ordem, verificar=None,
                 criar=None, atualizar=None):
        """verificar(dados) valida regras entre campos; criar/atualizar substituem
        as views padrão quando o recurso precisa de lógica própria."""
        self.modelo, self.pk, self.campos, self.ordem = modelo, pk, campos, ordem
        self.verificar = verificar
        self.blueprint = Blueprint(nome, __name__)
        bp = self.blueprint
        bp.add_url_rule(prefixo, "criar", criar or self.criar, methods=["POST"])
        bp.add_url_rule(f"{prefixo}/usuario/<int:id_usuario>", "listar_por_usuario",
                        self.listar_por_usuario, methods=["GET"])
        bp.add_url_rule(f"{prefixo}/<int:{pk}>", "atualizar", atualizar or self.atualizar,
                        methods=["PUT"])
        bp.add_url_rule(f"{prefixo}/<int:{pk}>", "excluir", self.excluir, methods=["DELETE"])

        @bp.errorhandler(ValueError)
        def valor_invalido(erro):
            return jsonify({"erro": str(erro)}), 400

        @bp.errorhandler(SQLAlchemyError)
        def erro_banco(erro):
            db.session.rollback()
            return jsonify({"erro": "Erro ao processar a requisição."}), 500

    def _nao_encontrado(self):
        return jsonify({"erro": "Registro não encontrado."}), 404

    def _checar(self, registro):
        if self.verificar:
            self.verificar({c: getattr(registro, c) for c in self.campos})

    def criar(self):
        dados = request.get_json(silent=True)
        limpos = validar_campos(self.campos, dados)
        registro = self.modelo(id_usuario=int(dados["id_usuario"]), **limpos)
        self._checar(registro)
        db.session.add(registro)
        db.session.commit()
        return jsonify(registro.to_dict()), 201

    def listar_por_usuario(self, id_usuario):
        registros = (self.modelo.query.filter_by(id_usuario=id_usuario)
                     .order_by(*self.ordem).all())
        return jsonify([r.to_dict() for r in registros]), 200

    def atualizar(self, **kwargs):
        registro = db.session.get(self.modelo, kwargs[self.pk])
        if registro is None:
            return self._nao_encontrado()
        for campo, valor in validar_campos(self.campos, request.get_json(silent=True), parcial=True).items():
            setattr(registro, campo, valor)
        try:
            self._checar(registro)
        except ValueError:
            db.session.rollback()
            raise
        db.session.commit()
        return jsonify(registro.to_dict()), 200

    def excluir(self, **kwargs):
        registro = db.session.get(self.modelo, kwargs[self.pk])
        if registro is None:
            return self._nao_encontrado()
        db.session.delete(registro)
        db.session.commit()
        return "", 204
