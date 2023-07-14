import datetime
from flask import Blueprint, request, jsonify

from models import *

main = Blueprint('main', __name__)

""" Dicionário principal de controlo das presenças.
Formato:
{
    [Nome da Sala] : {
        estado: STOP/GO,
        unidade_id: (ID da unidade),
        professor_id: (ID do professor),
        turma_id: (ID da turma),
        ip_address: (IP do arduino),
        inicio: (Timestamp de início da aula),
        alunos : [
            {
                "numero": (Número do aluno 1),
                "timpestamp": (Timestamp de entrada do aluno 1)
            },
            {
                "numero": (Número do aluno 2),
                "timpestamp": (Timestamp de entrada do aluno 2)
            }
        ]
    }
}
"""
aulas_a_decorrer = {}


@main.route("/unidades", methods=["GET"])
def get_unidades():
    if not request.args or not request.args.get('professor_id', type=int):
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        professor_id = int(request.args.get('professor_id'))
    except ValueError:
        return jsonify(error="[CRITICAL] Parâmetro incorreto - só se aceitam números!"), 400

    unidades = Professor.get_unidades(professor_id)
    if not unidades:
        return jsonify(error="Não existem professores com esse id"), 404

    return jsonify(unidades=unidades), 200


@main.route("/aulas", methods=["GET"])
def get_aulas():
    if not request.args or not request.args.get('professor_id', type=int):
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        professor_id = int(request.args.get('professor_id'))
    except ValueError:
        return jsonify(error="[CRITICAL] Parâmetro incorreto - só se aceitam números!"), 400

    aula_ativa = {}
    for sala, dados in aulas_a_decorrer.items():
        if dados['professor_id'] == professor_id:
            unidade = Unidade.query.get(dados['unidade_id'])
            aula_ativa = {'sala': sala, 'unidade': unidade.nome, 'estado': dados['estado']}

    return jsonify(aula_ativa), 200


@main.route("/aula/iniciar", methods=["POST"])
def iniciar_aula():
    params = request.get_json()
    sala_a_abrir, professor_id, unidade_id, turma_id = params['sala'], params['professor_id'], params['unidade_id'], \
        params['turma_id']

    if not sala_a_abrir or not professor_id or not unidade_id or not turma_id:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        professor_id = int(professor_id)
        unidade_id = int(unidade_id)
    except ValueError:
        return jsonify(error="[CRITICAL] Parâmetros incorretos de ID não é número!"), 400

    if not Sala.query.filter_by(nome=sala_a_abrir).first():
        return jsonify(error="Não existem registos dessa sala."), 404

    if sala_a_abrir in aulas_a_decorrer:
        return jsonify(error="Já existe um registo ativo desta sala."), 409

    arduino = Arduino.get_arduino_by_sala("nome", sala_a_abrir)
    if not arduino:
        return jsonify(error="Não existe nenhum arduino associado a esta sala."), 404

    data = {
        'estado': 'GO',
        'unidade_id': unidade_id,
        'professor_id': professor_id,
        'turma_id': turma_id,
        'ip_address': arduino.ip_address,
        'inicio': datetime.datetime.now(),
        'alunos': []
    }

    from app import acao_arduino
    acao_arduino(arduino.ip_address, "aula")
    aulas_a_decorrer[sala_a_abrir] = data
    return jsonify(message="Aula iniciada."), 200


@main.route("/aula/controlar", methods=["POST"])
def controlar_aula():
    params = request.get_json()
    sala_param, acao_param = params['sala'], params['acao']

    if not sala_param or not acao_param:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    match acao_param:
        case "GO":
            # Atualiza o estado da aula em andamento para "GO"
            aulas_a_decorrer[sala_param]['estado'] = 'GO'
            return jsonify(state="GO"), 200

        case "STOP":
            # Atualiza o estado da aula em andamento para "STOP"
            aulas_a_decorrer[sala_param]['estado'] = 'STOP'
            return jsonify(state="STOP"), 200

        case "CANCEL":
            aula = aulas_a_decorrer[sala_param]
            from app import acao_arduino
            acao_arduino(aula['ip_address'], "encerrar")
            del aula
            return jsonify(state="CANCEL"), 200

        case "FINISH":
            aula = aulas_a_decorrer[sala_param]

            nova_aula = Aula.create(sala_param,
                                    aula['unidade_id'],
                                    aula['professor_id'],
                                    aula['turma_id'],
                                    aula['inicio'])

            Presenca.create(nova_aula[1].id, aula['alunos'])
            from app import acao_arduino
            acao_arduino(aula['ip_address'], "encerrar")
            del aula
            return jsonify(message="Registos inseridos e aula terminada.", aula_id=nova_aula[1].id), 200

    return jsonify(status=aulas_a_decorrer[sala_param]['estado']), 200


@main.route("/aula/exportar", methods=["GET"])
def exportar_aula():
    if not request.args or not request.args.get('aula_id', type=int):
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    presencas = Aula.export(request.args.get('aula_id'))
    return jsonify(presencas=presencas[0], data_aula=presencas[1]), 200


@main.route("/presencas", methods=["GET"])
def get_presencas():
    if not request.args or not request.args.get('sala', type=str):
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    if request.args.get('sala') not in aulas_a_decorrer:
        return jsonify(error="A sala não tem marcação registada."), 404

    sala_selecionada = aulas_a_decorrer[request.args.get('sala')]

    return jsonify(alunos=[{
        "numero": aluno["numero"],
        "timestamp": aluno["timestamp"].strftime("%d/%m/%Y %H:%M")
    } for aluno in sala_selecionada['alunos']]), 200


@main.route("/presencas/arduino", methods=["PUT"])
def arduino_presenca():
    params = request.get_json()
    token = params['token']

    if not token:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    from app import Configuration
    data = jwt.decode(token,
                      key=Configuration.ARDUINO_SECRET_KEY,
                      algorithms=['HS256', ])

    arduino_uid, disp_uid = data["identifier"], data["uid"]
    sala = Sala.get_sala_by_arduino(arduino_uid)
    if not sala:
        return jsonify(error="Sala não encontrada."), 404

    aluno = Aluno.get_aluno_by_disp(disp_uid)
    if not aluno:
        return jsonify(error="Aluno não encontrado."), 404

    sala_selecionada = aulas_a_decorrer[sala.nome]
    if not sala_selecionada:
        return jsonify(error="Não existe nenhuma aula a decorrer nesta sala."), 404

    if sala_selecionada['estado'] == "STOP":
        return jsonify(error="Não pode marcar presença numa sala que se encontra com marcações em pausa."), 403

    if any(aluno["numero"] == aluno.id for aluno in sala_selecionada['alunos']):
        return jsonify(error="Aluno já está na lista de presenças"), 409

    sala_selecionada['alunos'].append({"numero": aluno.id, "timestamp": datetime.datetime.now()})
    return jsonify(message="Marcação da presença efetuada com sucesso."), 200


@main.route("/presencas/marcar", methods=["PUT"])
def marcar_presenca():
    params = request.get_json()
    sala_a_controlar, num_aluno = params['sala'], params['aluno']

    if not sala_a_controlar or not num_aluno:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    if sala_a_controlar not in aulas_a_decorrer:
        return jsonify(error="A sala não tem nenhum registo ativo."), 404

    sala_selecionada = aulas_a_decorrer[sala_a_controlar]

    if sala_selecionada['estado'] == "STOP":
        return jsonify(error="Não pode marcar presença numa sala que se encontra com marcações em pausa."), 403

    if any(aluno["numero"] == num_aluno for aluno in sala_selecionada['alunos']):
        return jsonify(error="Este aluno já tem a sua presença registada."), 409

    sala_selecionada['alunos'].append({"numero": num_aluno, "timestamp": datetime.datetime.now()})
    return jsonify(message="Marcação da presença efetuada com sucesso."), 200


@main.route("/presencas/eliminar", methods=["POST"])
def eliminar_presenca():
    params = request.get_json()
    sala_a_controlar, num_aluno = params['sala'], params['aluno']

    if not sala_a_controlar or not num_aluno:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    if sala_a_controlar not in aulas_a_decorrer:
        return jsonify(error="A sala não tem nenhum registo ativo."), 404

    sala_selecionada = aulas_a_decorrer[sala_a_controlar]

    if not any(aluno["numero"] == num_aluno for aluno in sala_selecionada['alunos']):
        return jsonify(error="Este aluno não consta na lista de presenças."), 409

    sala_selecionada['alunos'] = [aluno for aluno in sala_selecionada['alunos'] if aluno["numero"] != num_aluno]
    return jsonify(message="Aluno retirado da lista com sucesso"), 200
