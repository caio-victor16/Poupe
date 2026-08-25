from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.models.usuario import Usuario

usuario_bp = Blueprint('usuario_bp', __name__)

# ROTA DE CADASTRO
@usuario_bp.route('/usuarios', methods=['POST'])
def cadastrar_usuario():
    dados = request.get_json() or {}
    
    nome = dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')
    renda_mensal = dados.get('renda_mensal')
    limite_gastos = dados.get('limite_gastos', 0.0)

    if not nome or not email or not senha or renda_mensal is None:
        return jsonify({"erro": "Campos obrigatórios ausentes"}), 400

    usuario_existente = Usuario.query.filter_by(email=email).first()
    if usuario_existente:
        return jsonify({"erro": "Email já cadastrado"}), 400

    novo_usuario = Usuario(
        nome=nome,
        email=email,
        senha=senha,
        renda_mensal=renda_mensal,
        limite_gastos=limite_gastos
    )

    db.session.add(novo_usuario)
    db.session.commit()

    return jsonify({"mensagem": "Usuário cadastrado com sucesso!", "usuario_id": novo_usuario.id_usuario}), 201

# ROTA DE LOGIN
@usuario_bp.route('/login', methods=['POST'])
@usuario_bp.route('/usuarios/login', methods=['POST'])
def login():
    dados = request.get_json() or {}
    email = dados.get('email')
    senha = dados.get('senha')

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario or usuario.senha != senha:
        return jsonify({"erro": "Credenciais inválidas"}), 401

    return jsonify({
        "mensagem": "Login realizado com sucesso",
        "usuario_id": usuario.id_usuario,
        "nome": usuario.nome
    }), 200

# ROTA OBTER PERFIL
@usuario_bp.route('/usuarios/<int:usuario_id>', methods=['GET'])
def obter_usuario(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    return jsonify({
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "renda_mensal": float(usuario.renda_mensal),
        "limite_gastos": float(usuario.limite_gastos)
    }), 200