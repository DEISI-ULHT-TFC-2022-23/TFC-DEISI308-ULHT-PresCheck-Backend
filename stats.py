import statistics

from flask import Blueprint, jsonify, request

from models import *
from sqlalchemy.sql import distinct, desc

stats = Blueprint('stats', __name__)


# /stats/unidades?tipo=total
# /stats/unidades?tipo=total&unidades=1,2,3
# /stats/unidades?tipo=prof&professor_id=1
# /stats/unidades?tipo=prof&professor_id=1&unidades=1,2,3
@stats.route("/stats/unidades", methods=["GET"])
def stats_unidades():
    tipo_arg = request.args.get('tipo')
    professor_id_arg = request.args.get('professor_id', type=int)
    unidades_arg = request.args.get('unidades')

    if not request.args or not tipo_arg:
        return jsonify(error="Falta parâmetros para completar o processo!"), 400

    if tipo_arg not in ['total', 'prof']:
        return jsonify(error="Parâmetros incorretos!"), 400

    if tipo_arg == 'prof' and not professor_id_arg:
        return jsonify(error="Falta parâmetros para completar o processo!"), 400

    subquery = (
        db.session.query(Presenca.aula_id, func.count().label("presencas"))
        .join(Aula, Presenca.aula_id == Aula.id)
        .group_by(Presenca.aula_id)
        .subquery()
    )
    query = (
        db.session.query(
            Unidade.nome.label("unidade"),
            func.avg(subquery.c.presencas).label("media_presencas"),
            func.sum(distinct(subquery.c.presencas)).label("total_presencas"),
        )
        .join(Aula, subquery.c.aula_id == Aula.id)
        .join(Unidade, Aula.unidade_id == Unidade.id)
        .group_by(Aula.unidade_id)
    )

    if tipo_arg == 'prof':
        query = query.filter(Aula.professor_id == professor_id_arg)

    if unidades_arg is not None:
        unidades_arg = unidades_arg.split(',')
        query = query.filter(Aula.unidade_id.in_(unidades_arg))

    query = query.group_by(Unidade.nome)

    return jsonify(results=[{
        'unidade': row.unidade,
        'num_presencas_total': row.total_presencas,
        'media': round(row.media_presencas, 2),
        'mediana': statistics.median([result[0] for result in db.session.query(subquery.c.presencas)
                                     .join(Aula, subquery.c.aula_id == Aula.id)
                                     .join(Unidade, Aula.unidade_id == Unidade.id)
                                     .filter(Unidade.nome == row.unidade)])
    } for row in query.all()]), 200


# /stats/turmas?tipo=total
# /stats/turmas?tipo=total&unidades=1,2,3
# /stats/turmas?tipo=total&unidades=1,2,3&turma_id=1,2,3
# /stats/turmas?tipo=total&unidades=1,2,3&turma_id=1,2,3&atraso=15
# /stats/turmas?tipo=prof&professor_id=1
# /stats/turmas?tipo=prof&professor_id=1&unidades=1,2,3
# /stats/turmas?tipo=prof&professor_id=1&unidades=1,2,3&turma_id=1,2,3
# /stats/turmas?tipo=prof&professor_id=1&unidades=1,2,3&turma_id=1,2,3&atraso=15
@stats.route("/stats/turmas", methods=["GET"])
def stats_turmas():
    tipo_arg = request.args.get('tipo')
    professor_id_arg = request.args.get('professor_id', type=int)
    unidades_arg = request.args.get('unidades')
    turmas_arg = request.args.get('turmas')
    atraso_arg = request.args.get('atraso', type=int)

    if not request.args or not tipo_arg:
        return jsonify(error="Falta parâmetros para completar o processo!"), 400

    if tipo_arg not in ['total', 'prof']:
        return jsonify(error="Parâmetros incorretos!"), 400

    if tipo_arg == 'prof' and not professor_id_arg:
        return jsonify(error="Falta parâmetros para completar o processo!"), 400

    subquery = (
        db.session.query(Presenca.aula_id, func.count().label("presencas"))
        .join(Aula, Presenca.aula_id == Aula.id)
        .group_by(Presenca.aula_id)
        .subquery()
    )
    query = (
        db.session.query(
            Unidade.nome.label("unidade"),
            Turma.nome.label("turma"),
            func.avg(subquery.c.presencas).label("media_presencas"),
            func.sum(distinct(subquery.c.presencas)).label("total_presencas"),
        )
        .join(Aula, subquery.c.aula_id == Aula.id)
        .join(Unidade, Aula.unidade_id == Unidade.id)
        .join(Turma, Aula.turma_id == Turma.id)
        .join(Aluno, Turma.id == Aluno.turma_id)
        .group_by(Aula.unidade_id)
    )

    if tipo_arg == 'prof':
        query = query.filter(Aula.professor_id == professor_id_arg)

    if unidades_arg is not None:
        unidades_arg = unidades_arg.split(',')
        query = query.filter(Aula.unidade_id.in_(unidades_arg))

    if turmas_arg is not None:
        turmas_arg = turmas_arg.split(',')
        query = query.filter(Aula.turma_id.in_(turmas_arg))

    if atraso_arg is not None:
        query = query.filter(
            func.datetime(Aula.created_at, f'+{atraso_arg} minutes') < func.datetime(Presenca.created_at)
        )

    query = query.group_by(Unidade.nome, Turma.nome)

    return jsonify(results=[{
        'unidade': row.unidade,
        'turma': row.turma,
        'num_presencas_total': row.total_presencas,
        'media': round(row.media_presencas, 2),
        'mediana': statistics.median([result[0] for result in db.session.query(subquery.c.presencas)
                                     .join(Aula, subquery.c.aula_id == Aula.id)
                                     .join(Unidade, Aula.unidade_id == Unidade.id)
                                     .filter(Unidade.nome == row.unidade)])
    } for row in query.all()]), 200


# /stats/alunos?tipo=historico&aluno_id=1&professor_id=1&unidade_id=1
# /stats/alunos?tipo=dados&aluno_id=1&professor_id=1&unidade_id=1
@stats.route("/stats/alunos", methods=["GET"])
def stats_alunos():
    tipo_arg = request.args.get('tipo')
    aluno_id_arg = request.args.get('aluno_id', type=int)
    unidade_id_arg = request.args.get('unidade_id', type=int)
    professor_id_arg = request.args.get('professor_id', type=int)

    if not request.args or not aluno_id_arg or not tipo_arg or not unidade_id_arg or not professor_id_arg:
        return jsonify(error="Falta parâmetros para completar o processo!"), 400

    if tipo_arg not in ['historico', 'dados']:
        return jsonify(error="Parâmetros incorretos!"), 400

    if tipo_arg == 'dados':
        subquery = (
            db.session.query(Presenca.aula_id, func.count().label("presencas"))
            .join(Aula, Presenca.aula_id == Aula.id)
            .group_by(Presenca.aula_id)
            .subquery()
        )
        query = (
            db.session.query(
                Unidade.nome.label("unidade"),
                Turma.nome.label("turma"),
                func.avg(subquery.c.presencas).label("media_presencas"),
                func.sum(distinct(subquery.c.presencas)).label("total_presencas")
            )
            .join(Aula, subquery.c.aula_id == Aula.id)
            .join(Unidade, Aula.unidade_id == Unidade.id)
            .join(Turma, Aula.turma_id == Turma.id)
            .join(Aluno, Presenca.aluno_id == Aluno.id)
            .filter(Aluno.id == aluno_id_arg)
            .filter(Aula.unidade_id == unidade_id_arg)
            .filter(Aula.professor_id == professor_id_arg)
            .group_by(Aula.unidade_id, Aluno.id)
        )

        results = [{
            'unidade': row.unidade,
            'turma': row.turma,
            'num_presencas_total': row.total_presencas,
            'media': round(row.media_presencas, 2),
            'mediana': statistics.median([result[0] for result in db.session.query(subquery.c.presencas)
                                         .join(Aula, subquery.c.aula_id == Aula.id)
                                         .join(Unidade, Aula.unidade_id == Unidade.id)
                                         .filter(Unidade.nome == row.unidade)])
        } for row in query.all()]

    else:
        query = (
            db.session.query(
                Unidade.nome.label("unidade"),
                Turma.nome.label("turma"),
                Presenca.created_at.label("presenca")
            )
            .join(Aula, Presenca.aula_id == Aula.id)
            .join(Unidade, Aula.unidade_id == Unidade.id)
            .join(Turma, Aula.turma_id == Turma.id)
            .join(Aluno, Presenca.aluno_id == Aluno.id)
            .filter(Aluno.id == aluno_id_arg)
            .filter(Aula.unidade_id == unidade_id_arg)
            .filter(Aula.professor_id == professor_id_arg)
            .order_by(desc(Presenca.created_at))
        )

        results = [{
            'unidade': row.unidade,
            'turma': row.turma,
            'presenca': row.presenca.strftime("%d/%m/%Y %H:%M")
        } for row in query.all()]

    return jsonify(results=results), 200


# /stats/presencas?professor_id=1&unidade_id=1
@stats.route("/stats/presencas", methods=["GET"])
def stats_presencas():
    professor_id_arg = request.args.get('professor_id', type=int)
    unidade_id_arg = request.args.get('unidade_id', type=int)

    if not request.args or not professor_id_arg or not unidade_id_arg:
        return jsonify(error="Falta parâmetros para completar o processo!"), 400

    query = (
        db.session.query(
            Presenca.aluno_id.label("aluno"),
            Turma.nome.label("turma"),
            func.count(Aula.presencas).label("num_presencas")
        )
        .join(Aula, Presenca.aula_id == Aula.id)
        .join(Turma, Aula.turma_id == Turma.id)
        .filter(Aula.professor_id == professor_id_arg)
        .filter(Aula.unidade_id == unidade_id_arg)
        .group_by(Presenca.aluno_id)
    )

    return jsonify(results=[{
        'numero': row.aluno,
        'turma': row.turma,
        'presencas': row.num_presencas
    } for row in query.all()]), 200
