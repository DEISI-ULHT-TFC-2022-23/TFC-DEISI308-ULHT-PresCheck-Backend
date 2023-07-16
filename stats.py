from flask import Blueprint, jsonify, request

from models import *

stats = Blueprint('stats', __name__)


@stats.route("/stats/unidades/media/total", methods=["GET"])
def media_unidades_total():
    # Média de presenças de todas as aulas por unidade curricular
    results = [{'unidade': unidade.nome,
                'media': round(db.session.query(func.coalesce(func.avg(Aula.presencas), 0.0)).filter_by(
                    unidade=unidade).scalar(), 2)}
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

@stats.route("/stats/presencas", methods=["GET"])
def presenca_by_unidade():
    if not request.args or not request.args.get('unidade_id') or not request.args.get('professor_id'):
        return jsonify(error="Falta parâmetros para completar o processo!"), 400

    try:
        unidade_id = int(request.args.get('unidade_id'))
        professor_id = int(request.args.get('professor_id'))
    except ValueError:
        return jsonify(error="Parâmetros incorretos - só se aceitam números!"), 400

    unidade = Unidade.query.get(unidade_id)
    professor = Professor.query.get(professor_id)

    if not unidade or unidade not in professor.unidades:
        return jsonify(error="Unidade não existe ou não está associada ao professor!"), 400

    results = [{'numero': aluno_id,
                'presencas': presencas}
               for aluno_id, presencas
               in db.session.query(Presenca.aluno_id, func.sum(Aula.presencas)).join(Aula).filter(
            Aula.unidade_id == unidade_id).group_by(Presenca.aluno_id).all()]

    return jsonify(results=results), 200