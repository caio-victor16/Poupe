from flask import Flask

from app.controllers.usuario_controller import usuario_bp
from app.controllers.gasto_controller import gasto_bp
from app.controllers.categoria_controller import categoria_bp
from app.controllers.boleto_controller import boleto_bp
from app.controllers.alerta_controller import alerta_bp
from app.controllers.previsao_controller import previsao_bp

app = Flask(__name__)

app.register_blueprint(usuario_bp)

app.register_blueprint(gasto_bp)

app.register_blueprint(categoria_bp)

app.register_blueprint(boleto_bp)

app.register_blueprint(alerta_bp)

app.register_blueprint(previsao_bp)

if __name__ == "__main__":

    app.run(debug=True)