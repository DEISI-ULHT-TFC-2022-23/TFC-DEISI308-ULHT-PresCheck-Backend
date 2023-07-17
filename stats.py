from flask import Blueprint, jsonify, request

from models import *

stats = Blueprint('stats', __name__)


@stats.route("/stats/unidades/media/total", methods=["GET"])
def media_unidades_total():
    # Média de presenças de todas as aulas por unidade curricular
    results = [{'unidade': unidade,
                'media': round(media, 2)}
               for unidade, media
               in db.session.query(Unidade.nome, func.coalesce(func.avg(Presenca.id), 0.0))
               .join(Presenca)
               .join(Aula)
               .group_by(Unidade.nome).all()]
    return jsonify(results=results), 200


@stats.route("/stats/unidades/media/<int:professor_id>", methods=["GET"])
def media_unidades_by_professor(professor_id):
    # Média de presenças de todas as aulas por unidade curricular associada ao professor
    results = [{'unidade': unidade,
                'media': round(media, 2)}
               for unidade, media
               in db.session.query(Unidade.nome, func.coalesce(func.avg(Presenca.id), 0.0))
               .join(Presenca)
               .join(Aula)
               .filter_by(professor_id=professor_id)
               .group_by(Unidade.nome).all()]
    return jsonify(results=results), 200


@stats.route("/stats/presencas", methods=["GET"])
def presencas_by_unidade():
    if not request.args or not request.args.get('unidade_id', type=int) or not request.args.get('professor_id',
                                                                                                type=int):
        return jsonify(error="Falta parâmetros para completar o processo!"), 400

    try:
        unidade_id = int(request.args.get('unidade_id'))
        professor_id = int(request.args.get('professor_id'))
    except ValueError:
        return jsonify(error="Parâmetros incorretos - só se aceitam números!"), 400

    unidade = Unidade.query.get(unidade_id)
    professor = Professor.query.get(professor_id)

    if not unidade or not professor or unidade not in professor.unidades:
        return jsonify(error="Unidade não existe ou não está associada ao professor!"), 400

    # Número de presenças de todas as aulas por unidade curricular associada ao professor
    results = [{'numero': aluno_id,
                'presencas': presencas}
               for aluno_id, presencas
               in db.session.query(Presenca.aluno_id, func.count(Presenca.id))
               .join(Aula)
               .filter_by(professor_id=professor_id, unidade_id=unidade_id)
               .group_by(Presenca.aluno_id).all()]
    return jsonify(results=results), 200
