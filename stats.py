from flask import Blueprint, jsonify

stats = Blueprint('stats', __name__)

@stats.route("/unidades/media", methods=["GET"])
def media_unidades():
    unidades = [
        #{unidade.nome}:
    ]
    return jsonify(
        media=10
    ), 200