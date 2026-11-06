"""Contas do caixa, metas, cofrinhos e receitas fixas (item 10c, parte 2)."""
import calendar
from datetime import date
from decimal import Decimal

from flask import jsonify, request

from backend.crud import CrudSimples, dinheiro, escolha, inteiro, texto, validar_campos
from backend.extensions import db
from backend.models.cofrinho import Cofrinho
from backend.models.conta import Conta
from backend.models.meta import Meta
from backend.models.receita import Receita
from backend.models.receita_recorrente import ReceitaRecorrente
from backend.services.receita_service import ReceitaService

TIPOS_CONTA = {"Corrente", "Poupança", "Dinheiro Físico", "Investimentos"}


conta_crud = CrudSimples(
    "conta", "/contas", Conta, "id_conta",
    {"nome": texto(100), "tipo": escolha(TIPOS_CONTA), "saldo": dinheiro()},
    ordem=(Conta.id_conta,),
)

meta_crud = CrudSimples(
    "meta", "/metas", Meta, "id_meta",
    {"titulo": texto(100), "valor_alvo": dinheiro(Decimal("0"), incluir_minimo=False),
     "valor_guardado": dinheiro(Decimal("0"))},
    ordem=(Meta.id_meta,),
)

cofrinho_crud = CrudSimples(
    "cofrinho_meta", "/cofrinhos", Cofrinho, "id_cofrinho",
    {"titulo": texto(100), "valor_alvo": dinheiro(Decimal("0"), incluir_minimo=False),
     "valor_guardado": dinheiro(Decimal("0")), "prazo_meses": inteiro(1, 600)},
    ordem=(Cofrinho.id_cofrinho,),
)


def aportar(id_cofrinho):
    """Soma um aporte no próprio banco (sem ler-somar-gravar no navegador)."""
    valor = validar_campos({"valor": dinheiro(Decimal("0"), incluir_minimo=False)},
                           request.get_json(silent=True))["valor"]
    atualizados = (Cofrinho.query.filter_by(id_cofrinho=id_cofrinho)
                   .update({Cofrinho.valor_guardado: Cofrinho.valor_guardado + valor},
                           synchronize_session=False))
    if not atualizados:
        return jsonify({"erro": "Registro não encontrado."}), 404
    db.session.commit()
    cofrinho = db.session.get(Cofrinho, id_cofrinho)
    db.session.refresh(cofrinho)
    return jsonify(cofrinho.to_dict()), 200


cofrinho_crud.blueprint.add_url_rule("/cofrinhos/<int:id_cofrinho>/aportar", "aportar",
                                     aportar, methods=["POST"])


# ---- receitas fixas ------------------------------------------------------------

def _proxima_mensal(data_atual, dia_mes):
    ano = data_atual.year + (data_atual.month == 12)
    mes = data_atual.month % 12 + 1
    return date(ano, mes, min(dia_mes, calendar.monthrange(ano, mes)[1]))


def _primeira_data(dia_mes, hoje):
    """Próxima ocorrência do dia (hoje conta); dia 31 vira o último dia do mês."""
    data = date(hoje.year, hoje.month, min(dia_mes, calendar.monthrange(hoje.year, hoje.month)[1]))
    return data if data >= hoje else _proxima_mensal(data, dia_mes)


CAMPOS_RECEITA_RECORRENTE = {
    "descricao": texto(255), "categoria": escolha(ReceitaService.CATEGORIAS),
    "valor": dinheiro(Decimal("0"), incluir_minimo=False), "dia_mes": inteiro(1, 31),
}


def _criar_receita_recorrente():
    dados = request.get_json(silent=True)
    limpos = validar_campos(CAMPOS_RECEITA_RECORRENTE, dados)
    registro = ReceitaRecorrente(id_usuario=int(dados["id_usuario"]), ativa=True,
                                 proxima_data=_primeira_data(limpos["dia_mes"], date.today()),
                                 **limpos)
    db.session.add(registro)
    db.session.commit()
    return jsonify(registro.to_dict()), 201


def _atualizar_receita_recorrente(id_receita_recorrente):
    registro = db.session.get(ReceitaRecorrente, id_receita_recorrente)
    if registro is None:
        return jsonify({"erro": "Registro não encontrado."}), 404
    dados = request.get_json(silent=True)
    limpos = validar_campos(CAMPOS_RECEITA_RECORRENTE, dados, parcial=True)
    if "ativa" in (dados or {}):
        if not isinstance(dados["ativa"], bool):
            raise ValueError("O campo 'ativa' deve ser verdadeiro ou falso.")
        limpos["ativa"] = dados["ativa"]
    for campo, valor in limpos.items():
        setattr(registro, campo, valor)
    if "dia_mes" in limpos:
        registro.proxima_data = _primeira_data(limpos["dia_mes"], date.today())
    db.session.commit()
    return jsonify(registro.to_dict()), 200


def processar_receitas(id_usuario, hoje=None):
    """Gera as receitas vencidas até hoje e avança a próxima data (idempotente)."""
    hoje = hoje or date.today()
    vencidas = (ReceitaRecorrente.query
                .filter(ReceitaRecorrente.id_usuario == id_usuario,
                        ReceitaRecorrente.ativa.is_(True),
                        ReceitaRecorrente.proxima_data <= hoje)
                .with_for_update().all())
    geradas = []
    for r in vencidas:
        while r.proxima_data <= hoje:
            receita = Receita(id_usuario=r.id_usuario, descricao=r.descricao,
                              categoria=r.categoria, valor=r.valor, data=r.proxima_data)
            db.session.add(receita)
            geradas.append(receita)
            r.proxima_data = _proxima_mensal(r.proxima_data, r.dia_mes)
    db.session.commit()
    return [g.to_dict() for g in geradas]


def _processar(id_usuario):
    geradas = processar_receitas(id_usuario)
    return jsonify({"geradas": len(geradas), "receitas": geradas}), 200


receita_recorrente_crud = CrudSimples(
    "receita_recorrente", "/receitas-recorrentes", ReceitaRecorrente, "id_receita_recorrente",
    CAMPOS_RECEITA_RECORRENTE,
    ordem=(ReceitaRecorrente.proxima_data, ReceitaRecorrente.id_receita_recorrente),
    criar=_criar_receita_recorrente, atualizar=_atualizar_receita_recorrente,
)
receita_recorrente_crud.blueprint.add_url_rule("/receitas-recorrentes/usuario/<int:id_usuario>/processar", "processar",
                _processar, methods=["POST"])

conta_bp = conta_crud.blueprint
meta_bp = meta_crud.blueprint
cofrinho_meta_bp = cofrinho_crud.blueprint
receita_recorrente_bp = receita_recorrente_crud.blueprint
