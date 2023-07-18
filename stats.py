import statistics

from flask import Blueprint, jsonify, request

from models import *

stats = Blueprint('stats', __name__)


# @stats.before_request
# def check_auth():
#     print([header for header in request.headers])
#     authorization_header = request.headers.get("Authorization")
#     if not authorization_header or not authorization_header.startswith("Bearer "):
#         return jsonify(error="Não autorizado"), 401
#
#     try:
#         token = authorization_header.split(" ")[1]
#         if not token:
#             return jsonify(error="Não autorizado"), 401
#
#         user = User.verify_session_token(token)
#         if not user:
#             return jsonify(error="Não autorizado"), 401
#
#         if not user['active']:
#             return jsonify(error="Não autorizado"), 401
#
#     except jwt.ExpiredSignatureError:
#         return jsonify(error='Token expirado'), 401
#     except jwt.InvalidSignatureError:
#         return jsonify(error='Token inválido'), 401
#     except jwt.InvalidTokenError:
#         return jsonify(error='Token inválido'), 401


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
            func.count(distinct(Aula.id)).label("total_aulas"),
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
        'num_aulas_total': row.total_aulas,
        'media': round(row.media_presencas, 2),
        'mediana': statistics.median([result[0] for result in db.session.query(subquery.c.presencas)
                                     .join(Aula, subquery.c.aula_id == Aula.id)
                                     .join(Unidade, Aula.unidade_id == Unidade.id)
                                     .filter(Unidade.nome == row.unidade)])
    } for row in query.all()]), 200


# /stats/turmas?tipo=total
# /stats/turmas?tipo=total&unidade_id=1
# /stats/turmas?tipo=total&unidade_id=1&turma_id=1
# /stats/turmas?tipo=total&unidade_id=1&turma_id=1&atraso=15
# /stats/turmas?tipo=prof&professor_id=1
# /stats/turmas?tipo=prof&professor_id=1&unidade_id=1
# /stats/turmas?tipo=prof&professor_id=1&unidade_id=1&turma_id=1
# /stats/turmas?tipo=prof&professor_id=1&unidade_id=1&turma_id=1&atraso=15
@stats.route("/stats/turmas", methods=["GET"])
def stats_turmas():
    tipo_arg = request.args.get('tipo')
    professor_id_arg = request.args.get('professor_id', type=int)
    unidade_id_arg = request.args.get('unidade_id', type=int)
    turma_id_arg = request.args.get('turma_id', type=int)
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
            func.count(distinct(Aula.id)).label("total_aulas"),
            func.count(distinct(Aluno.id)).label("num_alunos_turma"),
        )
        .join(Aula, subquery.c.aula_id == Aula.id)
        .join(Unidade, Aula.unidade_id == Unidade.id)
        .join(Turma, Aula.turma_id == Turma.id)
        .join(Aluno, Turma.id == Aluno.turma_id)
        .group_by(Aula.unidade_id)
    )

    if tipo_arg == 'prof':
        query = query.filter(Aula.professor_id == professor_id_arg)

    if unidade_id_arg is not None:
        query = query.filter(Aula.unidade_id == unidade_id_arg)

    if turma_id_arg is not None:
        query = query.filter(Aula.turma_id == turma_id_arg)

    if atraso_arg is not None:
        query = query.filter(
            func.datetime(Aula.created_at, f'+{atraso_arg} minutes') < func.datetime(Presenca.created_at)
        )

    query = query.group_by(Unidade.nome, Turma.nome)

    return jsonify(results=[{
        'unidade': row.unidade,
        'turma': row.turma,
        'num_presencas_total': row.total_presencas,
        'num_aulas_total': row.total_aulas,
        'num_alunos_turma': row.num_alunos_turma,
        'media': round(row.media_presencas, 2),
        'mediana': statistics.median([result[0] for result in db.session.query(subquery.c.presencas)
                                     .join(Aula, subquery.c.aula_id == Aula.id)
                                     .join(Unidade, Aula.unidade_id == Unidade.id)
                                     .filter(Unidade.nome == row.unidade)])
    } for row in query.all()]), 200


# /stats/alunos?aluno_id=1
# /stats/alunos?aluno_id=1&unidade_id=1
@stats.route("/stats/alunos", methods=["GET"])
def stats_alunos():
    aluno_id_arg = request.args.get('aluno_id', type=int)
    unidade_id_arg = request.args.get('unidade_id', type=int)

    if not request.args or not aluno_id_arg:
        return jsonify(error="Falta parâmetros para completar o processo!"), 400

    query = (
        db.session.query(
            Unidade.nome.label("unidade"),
            Turma.nome.label("turma"),
            Presenca.created_at.label("presenca")
        )
        .join(Aula, Presenca.aula_id == Aula.id)
        .join(Unidade, Aula.unidade_id == Unidade.id)
        .join(Turma, Aula.turma_id == Turma.id)
        .filter(Presenca.aluno_id == aluno_id_arg)
        .order_by(Presenca.created_at)
    )

    if unidade_id_arg is not None:
        query = query.filter(Aula.unidade_id == unidade_id_arg)

    return jsonify(results=[{
        'unidade': row.unidade,
        'turma': row.turma,
        'presenca': row.presenca
    } for row in query.all()]), 200
