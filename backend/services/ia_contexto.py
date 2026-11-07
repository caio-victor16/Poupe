"""Resumo das finanças do usuário logado, enviado à IA junto com a pergunta.

Só dados do próprio usuário (id da sessão), agregados e com limite de tamanho.
Não inclui e-mail, telefone, senha, código de barras nem ids internos.
Textos digitados pelo usuário (descrições, títulos) vão cortados e marcados como
dados: a instrução do sistema manda a IA não obedecer ao que estiver neles.
"""
import calendar
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, or_

from backend.extensions import db
from backend.models.alerta import Alerta
from backend.models.boleto import Boleto
from backend.models.categoria import Categoria
from backend.models.cofrinho import Cofrinho
from backend.models.conta import Conta
from backend.models.gasto import Gasto
from backend.models.meta import Meta
from backend.models.orcamento_categoria import OrcamentoCategoria
from backend.models.receita import Receita
from backend.models.receita_recorrente import ReceitaRecorrente
from backend.models.recorrencia_gasto import RecorrenciaGasto
from backend.models.usuario import Usuario

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
MAX_ITENS = 8
MAX_TEXTO = 60
MAX_CONTEXTO = 6000


def brl(valor):
    """Decimal → 'R$ 1.234,56'."""
    texto = f"{Decimal(valor or 0):,.2f}"
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")


def curto(texto):
    """Texto do usuário numa linha só, sem aspas e com tamanho limitado."""
    texto = " ".join(str(texto or "").split()).replace('"', "'")
    return texto if len(texto) <= MAX_TEXTO else texto[:MAX_TEXTO - 1] + "…"


def pct(parte, total):
    return f"{(Decimal(parte) / Decimal(total) * 100):.0f}%" if total else "—"


def _inicio_mes(d):
    return d.replace(day=1)


def _mes_seguinte(d):
    return (d.replace(day=28) + timedelta(days=4)).replace(day=1)


def _mes_anterior(d):
    return (d.replace(day=1) - timedelta(days=1)).replace(day=1)


def _soma(modelo, uid, inicio, fim):
    return db.session.query(func.coalesce(func.sum(modelo.valor), 0)).filter(
        modelo.id_usuario == uid, modelo.data >= inicio, modelo.data < fim).scalar()


def montar_contexto(uid, hoje=None):
    hoje = hoje or date.today()
    usuario = db.session.get(Usuario, uid)
    if usuario is None:
        return ""
    inicio = _inicio_mes(hoje)
    fim = _mes_seguinte(hoje)
    dias_no_mes = calendar.monthrange(hoje.year, hoje.month)[1]
    nomes_categoria = {c.id_categoria: c.nome for c in Categoria.query.all()}

    gasto_mes = Decimal(_soma(Gasto, uid, inicio, fim))
    receita_mes = Decimal(_soma(Receita, uid, inicio, fim))
    renda = Decimal(usuario.renda_mensal or 0)
    limite = Decimal(usuario.limite_gastos or 0)

    linhas = [
        f"Data de hoje: {hoje:%d/%m/%Y} (dia {hoje.day} de {dias_no_mes}).",
        f"Nome: {curto(usuario.nome.split()[0] if usuario.nome else '')}.",
        f"Renda mensal informada no cadastro: {brl(renda)}. Limite de gastos mensal: {brl(limite)}.",
        "",
        f"## {MESES[hoje.month - 1].capitalize()} de {hoje.year} (mês atual, até hoje)",
        f"- Gastos: {brl(gasto_mes)} ({pct(gasto_mes, limite)} do limite).",
        f"- Receitas lançadas: {brl(receita_mes)}.",
        f"- Saldo do mês (receitas lançadas − gastos): {brl(receita_mes - gasto_mes)}.",
    ]
    if limite and hoje.day < dias_no_mes:
        restante = limite - gasto_mes
        por_dia = restante / (dias_no_mes - hoje.day) if restante > 0 else Decimal(0)
        linhas.append(f"- Ainda cabe no limite: {brl(max(restante, Decimal(0)))} "
                      f"(≈ {brl(por_dia)} por dia até o fim do mês).")

    # Gastos por categoria no mês, com orçamento quando houver.
    por_categoria = (db.session.query(Gasto.id_categoria, func.sum(Gasto.valor))
                     .filter(Gasto.id_usuario == uid, Gasto.data >= inicio, Gasto.data < fim)
                     .group_by(Gasto.id_categoria).order_by(func.sum(Gasto.valor).desc()).all())
    orcamentos = {o.id_categoria: Decimal(o.limite) for o in
                  OrcamentoCategoria.query.filter_by(id_usuario=uid).all()}
    if por_categoria or orcamentos:
        linhas += ["", "## Gastos do mês por categoria"]
        vistas = set()
        for cid, total in por_categoria[:MAX_ITENS]:
            vistas.add(cid)
            texto = f"- {nomes_categoria.get(cid, 'Outros')}: {brl(total)}"
            if cid in orcamentos:
                texto += f" de {brl(orcamentos[cid])} orçados ({pct(total, orcamentos[cid])})"
            linhas.append(texto + ".")
        for cid, lim in orcamentos.items():
            if cid not in vistas:
                linhas.append(f"- {nomes_categoria.get(cid, 'Outros')}: {brl(0)} de {brl(lim)} orçados.")

    # Três meses anteriores, para comparação.
    historico, ref = [], inicio
    for _ in range(3):
        ant = _mes_anterior(ref)
        historico.append(f"{MESES[ant.month - 1]}/{ant.year}: gastos {brl(_soma(Gasto, uid, ant, ref))}, "
                         f"receitas {brl(_soma(Receita, uid, ant, ref))}")
        ref = ant
    linhas += ["", "## Meses anteriores", *("- " + h + "." for h in historico)]

    ultimos = (Gasto.query.filter_by(id_usuario=uid).order_by(Gasto.data.desc(), Gasto.id_gasto.desc())
               .limit(MAX_ITENS).all())
    if ultimos:
        linhas += ["", "## Últimos gastos"]
        linhas += [f'- {g.data:%d/%m}: {brl(g.valor)} em {nomes_categoria.get(g.id_categoria, "Outros")}'
                   + (f' — "{curto(g.descricao)}"' if g.descricao else "") + "." for g in ultimos]

    fixos = (RecorrenciaGasto.query.filter_by(id_usuario=uid, ativa=True)
             .order_by(RecorrenciaGasto.valor.desc()).all())
    if fixos:
        total = sum(Decimal(f.valor) for f in fixos)
        linhas += ["", f"## Gastos fixos ativos (total {brl(total)})"]
        linhas += [f'- "{curto(f.descricao) or nomes_categoria.get(f.id_categoria, "Outros")}": '
                   f"{brl(f.valor)}, {f.frequencia}, próximo em {f.proxima_data:%d/%m}." for f in fixos[:MAX_ITENS]]

    receitas_fixas = ReceitaRecorrente.query.filter_by(id_usuario=uid, ativa=True).all()
    if receitas_fixas:
        total = sum(Decimal(r.valor) for r in receitas_fixas)
        linhas += ["", f"## Receitas fixas ativas (total {brl(total)})"]
        linhas += [f'- "{curto(r.descricao)}": {brl(r.valor)} todo dia {r.dia_mes}.'
                   for r in receitas_fixas[:MAX_ITENS]]

    objetivos = [("Meta", m.titulo, m.valor_guardado, m.valor_alvo, None)
                 for m in Meta.query.filter_by(id_usuario=uid).all()]
    objetivos += [("Cofrinho", c.titulo, c.valor_guardado, c.valor_alvo, c.prazo_meses)
                  for c in Cofrinho.query.filter_by(id_usuario=uid).all()]
    if objetivos:
        linhas += ["", "## Metas e cofrinhos"]
        for tipo, titulo, guardado, alvo, prazo in objetivos[:MAX_ITENS]:
            linhas.append(f'- {tipo} "{curto(titulo)}": {brl(guardado)} de {brl(alvo)} '
                          f"({pct(guardado, alvo)})" + (f", prazo {prazo} meses" if prazo else "") + ".")

    contas = Conta.query.filter_by(id_usuario=uid).all()
    if contas:
        linhas += ["", f"## Contas (saldo total {brl(sum(Decimal(c.saldo) for c in contas))})"]
        linhas += [f'- "{curto(c.nome)}" ({curto(c.tipo)}): {brl(c.saldo)}.' for c in contas[:MAX_ITENS]]

    boletos = (Boleto.query.filter(Boleto.id_usuario == uid, or_(Boleto.status.is_(None), Boleto.status != "pago"),
                                   Boleto.vencimento <= hoje + timedelta(days=30))
               .order_by(Boleto.vencimento).limit(MAX_ITENS).all())
    if boletos:
        linhas += ["", "## Boletos a pagar (vencidos ou nos próximos 30 dias)"]
        linhas += [f'- "{curto(b.descricao) or "sem nome"}": {brl(b.valor)}, vence {b.vencimento:%d/%m/%Y}'
                   + (" (VENCIDO)" if b.vencimento < hoje else "")
                   + (", repete todo mês" if b.fixo else "")
                   + (", débito automático" if b.debito_automatico else "") + "." for b in boletos]
    fixos_boleto = (Boleto.query.filter(Boleto.id_usuario == uid, Boleto.fixo.is_(True),
                                        or_(Boleto.status.is_(None), Boleto.status != "pago"))
                    .all())
    if fixos_boleto:
        linhas.append(f"Total de contas fixas por mês (boletos que repetem): "
                      f"{brl(sum(Decimal(b.valor) for b in fixos_boleto))}.")

    nao_lidos = Alerta.query.filter_by(id_usuario=uid, visualizado=False).count()
    if nao_lidos:
        linhas += ["", f"Alertas não lidos no app: {nao_lidos}."]

    texto = "\n".join(linhas)
    return texto if len(texto) <= MAX_CONTEXTO else texto[:MAX_CONTEXTO] + "\n[resumo cortado]"
