from flask import Blueprint, jsonify

from models import *

stats = Blueprint('stats', __name__)


@stats.route("/stats/unidades/media/total", methods=["GET"])
def media_unidades_total():
    # Média de presenças de todas as aulas por unidade curricular
    results = [{'unidade': unidade.nome,
                'media': round(db.session.query(func.coalesce(func.avg(Aula.presencas), 0.0)).group_by(
                    unidade).scalar(), 2)}
               for unidade in Unidade.query.all()]
    return jsonify(results=results), 200


@stats.route("/stats/unidades/media/<int:professor_id>", methods=["GET"])
def media_unidades_by_professor(professor_id):
    # Média de presenças de todas as aulas por unidade curricular associada ao professor
    results = [{'unidade': unidade.nome,
                'media': round(db.session.query(func.coalesce(func.avg(Aula.presencas), 0.0)).filter_by(
                    unidade=unidade).scalar(), 2)}
               for unidade in Professor.query.get(professor_id).unidades]
    return jsonify(results=results), 200
