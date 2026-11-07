"""Política central: rotas novas são negadas até receberem autorização explícita."""
from flask import abort, request, session
from backend.extensions import db
from backend.models.usuario import Usuario
from backend.models.gasto import Gasto
from backend.models.boleto import Boleto
from backend.models.alerta import Alerta
from backend.models.orcamento_categoria import OrcamentoCategoria
from backend.models.recorrencia_gasto import RecorrenciaGasto
from backend.models.receita import Receita
from backend.models.conta import Conta
from backend.models.meta import Meta
from backend.models.cofrinho import Cofrinho
from backend.models.receita_recorrente import ReceitaRecorrente
from backend.seguranca import sessao_valida

PUBLICOS = {"usuario.login", "usuario.cadastrar_usuario", "senha.esqueci", "senha.redefinir"}
CRIACAO = {"gasto.criar", "boleto.criar", "alerta.criar",
           "orcamento.definir", "recorrencia_gasto.criar", "receita.criar",
           "conta.criar", "meta.criar", "cofrinho_meta.criar", "receita_recorrente.criar"}
RECURSOS = {"gasto": ("id_gasto", Gasto), "boleto": ("id_boleto", Boleto),
            "alerta": ("id_alerta", Alerta),
            "orcamento": ("id_orcamento", OrcamentoCategoria),
            "recorrencia_gasto": ("id_recorrencia", RecorrenciaGasto),
            "receita": ("id_receita", Receita),
            "conta": ("id_conta", Conta), "meta": ("id_meta", Meta),
            "cofrinho_meta": ("id_cofrinho", Cofrinho),
            "receita_recorrente": ("id_receita_recorrente", ReceitaRecorrente)}
POR_USUARIO = {"gasto", "boleto", "alerta", "orcamento", "recorrencia_gasto",
               "relatorio", "previsao", "score", "caixa", "cofrinho", "desperdicio",
               "receita", "conta", "meta", "cofrinho_meta", "receita_recorrente"}


def proteger_api():
    if request.blueprint is None:
        return
    # Cabeçalho não simples + ausência de CORS impedem POSTs de outras origens,
    # inclusive no login. O navegador só o envia após preflight autorizado.
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if request.headers.get("X-Poupe-Request") != "1":
            abort(403, description="Requisição sem proteção de origem.")
    if request.endpoint in PUBLICOS:
        return
    uid = session.get("usuario_id")
    # REV-002: o cookie só vale enquanto a sessão existir no banco
    # (logout e troca de senha apagam a linha).
    if (not isinstance(uid, int) or not sessao_valida(uid)
            or db.session.get(Usuario, uid) is None):
        session.clear()
        abort(401, description="Faça login para continuar.")
    args = request.view_args or {}
    if request.endpoint in {"usuario.logout", "usuario.sessao"}:
        return
    if request.blueprint == "usuario" and "usuario_id" in args:
        if args["usuario_id"] != uid:
            abort(403, description="Acesso não permitido.")
        return
    if request.blueprint == "categoria" and request.method in {"GET", "HEAD"}:
        return
    if request.endpoint == "ia.conversar_com_ia":
        return
    if request.blueprint in POR_USUARIO and "id_usuario" in args:
        if args["id_usuario"] != uid:
            abort(403, description="Acesso não permitido.")
        return
    if request.endpoint in CRIACAO:
        dados = request.get_json()
        if not isinstance(dados, dict):
            abort(400, description="Informe um objeto JSON.")
        if "id_usuario" in dados and str(dados["id_usuario"]) != str(uid):
            abort(403, description="Acesso não permitido.")
        dados["id_usuario"] = uid
        return
    recurso = RECURSOS.get(request.blueprint)
    if recurso and recurso[0] in args:
        registro = db.session.get(recurso[1], args[recurso[0]])
        if registro is None or registro.id_usuario != uid:
            abort(404, description="Registro não encontrado.")
        return
    # Listagens globais e alterações nas categorias compartilhadas são proibidas.
    abort(403, description="Operação não permitida.")
