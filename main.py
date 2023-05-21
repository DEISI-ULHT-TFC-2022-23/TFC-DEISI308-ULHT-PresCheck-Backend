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
        timestamp_aula_iniciada: Datetime.timestamp,
        alunos : [(Número aluno 1), (Número aluno 2), ...]
    }
}
"""
aulas_a_decorrer = {}


@main.route("/unidades", methods=["GET"])
def get_unidades():
    # Verifica se não há argumentos na requisição ou se o argumento 'professor_id' está em falta
    if not request.args or not request.args.get('professor_id'):
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    unidades = Professor.get_unidades(request.args.get('professor_id'))

    # Verifica se o professor não existe na base de dados
    if not unidades:
        return jsonify(error="Não existem professores com esse id"), 404

    # Retorna a lista de unidades associadas ao professor como resposta e com código de status 200 (OK)
    return jsonify(unidades=unidades), 200


@main.route("/aulas", methods=["GET"])
def get_aulas():
    # Verifica se não há argumentos na requisição ou se o argumento 'professor_id' está em falta
    if not request.args or not request.args.get('professor_id'):
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    # Cria uma lista com o nome da sala e o nome da unidade correspondente
    aulas_ativas = {}
    for sala, dados in aulas_a_decorrer.items():
        if dados['professor_id'] == request.args.get('professor_id'):
            unidade = Unidade.query.get(dados['unidade_id'])
            aulas_ativas = {'sala': sala, 'unidade': unidade.nome, 'estado': dados['estado']}

    # Retorna a sala e o nome da unidade em formato JSON e um código de status 200
    return jsonify(sala=aulas_ativas['sala'], unidade=aulas_ativas['unidade'], state=aulas_ativas['estado']), 200


@main.route("/aula/iniciar", methods=["POST"])
def iniciar_aula():
    # Obtém os dados JSON da solicitação POST
    params = request.get_json()
    sala_a_abrir, professor_id, unidade_id = params['sala'], params['professor_id'], params['unidade_id']

    # Verifica se os dados JSON obtidos são inválidos
    if not sala_a_abrir or not professor_id or not unidade_id:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    # Verifica se a sala pretendida não existe na base de dados
    if not Sala.query.filter_by(nome=sala_a_abrir).first():
        return jsonify(error="Não existem registos dessa sala."), 404

    # Verifica se a sala já está registada e ativa nas aulas em andamento
    if sala_a_abrir in aulas_a_decorrer:
        return jsonify(error="Já existe um registo ativo desta sala."), 409

    # Cria um dicionário com os dados da aula que será iniciada
    data = {
        'estado': 'GO',
        'unidade_id': unidade_id,
        'professor_id': professor_id,
        'timestamp_aula_iniciada': datetime.datetime.now().timestamp(),
        'alunos': []
    }

    # Adiciona a aula em andamento à lista de aulas em andamento, usando o nome da sala como chave
    aulas_a_decorrer[sala_a_abrir] = data
    return jsonify(message="Aula iniciada."), 200


@main.route("/aula/controlar", methods=["POST"])
def controlar_aula():
    # Obtém os dados JSON da solicitação POST
    params = request.get_json()
    sala_param, acao_param = params['sala'], params['acao']

    # Verifica se os dados JSON obtidos são inválidos
    if not sala_param or not acao_param:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    # Verifica qual ação foi realizada no formulário
    match acao_param:
        case "GO":
            # Atualiza o estado da aula em andamento para "GO"
            aulas_a_decorrer[sala_param]['estado'] = 'GO'
            return jsonify(state="GO"), 200
        case "STOP":
            # Atualiza o estado da aula em andamento para "STOP"
            aulas_a_decorrer[sala_param]['estado'] = 'STOP'
            return jsonify(state="STOP"), 200

        case "FINISH":
            # Obtém os dados da sala em andamento
            dados_sala = aulas_a_decorrer[sala_param]

            # Cria uma aula na base de dados com as informações da sala em andamento
            nova_aula = Aula.create(sala_param,
                                    dados_sala['unidade_id'],
                                    dados_sala['professor_id'])

            # Cria as presenças na base de dados associadas à aula
            Presenca.create(nova_aula[1].id, dados_sala['alunos'])

            # Remove a sala em andamento da lista de aulas em andamento e retorna o código a informar que foi processado
            del aulas_a_decorrer[sala_param]
            return jsonify(message="Registos inseridos e aula terminada.", aula_id=nova_aula[1].id), 204

    # Retorna o estado da aula atualizado
    return jsonify(status=aulas_a_decorrer[sala_param]['estado']), 200


@main.route("/aula/exportar", methods=["GET"])
def exportar_aula():
    # Verifica se não há argumentos na requisição ou se o argumento 'aula_id' está em falta
    if not request.args or not request.args.get('aula_id'):
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    # Busca todas as presenças associadas à aula e verifica se existe alguma presença
    presencas = Aula.export(request.args.get('aula_id'))

    # Retorna a lista de todas as presenças
    return jsonify(presencas=presencas), 200


@main.route("/presencas", methods=["GET"])
def get_presencas():
    # Verifica se não há argumentos na requisição ou se o argumento 'sala' está em falta
    if not request.args or not request.args.get('sala'):
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    # Verifica se a sala informada não está registrada nas aulas em andamento
    if request.args.get('sala') not in aulas_a_decorrer:
        return jsonify(error="A sala não tem marcação registada."), 404

    # Obtém a sala selecionada a partir do dicionário de aulas em andamento
    sala_selecionada = aulas_a_decorrer[request.args.get('sala')]

    # Avisa que não há novos alunos na lista de presença da sala
    sala_selecionada['alunos_novos'] = False

    # Retorna a lista de alunos da sala como resposta com código de status 200 (OK)
    return jsonify(alunos=sala_selecionada['alunos']), 200


@main.route("/presencas/arduino", methods=["PUT"])
def arduino_presenca():
    # Obtém os dados JSON da solicitação POST
    params = request.get_json()
    arduino_id, disp_uid = params['identifier'].strip(), params['uid'].strip()

    # Verifica se os dados JSON obtidos são inválidos
    if not arduino_id or not disp_uid:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    # Consulta o modelo de banco de dados "Sala" usando o valor da chave "identifier" obtida dos dados JSON
    sala = Sala.get_sala_by_arduino(arduino_id)

    # Verifica se a sala obtida da consulta não existe ou se o ‘id’ da sala não está presente na lista
    # "aulas_a_decorrer"
    if not sala or sala.nome not in aulas_a_decorrer:
        return jsonify(error="A sala não foi encontrada ou não existe marcação ativa."), 404

    # Guarda o dicionário da sala selecionada numa variável
    sala_selecionada = aulas_a_decorrer[sala.id]

    # Verifica se o valor da chave "status" da sala selecionada é igual a "STOP"
    if sala_selecionada['estado'] == "STOP":
        return jsonify(error="Não pode marcar presença numa sala que se encontra com marcações em pausa."), 403

    # Consulta o modelo da base de dados "Aluno" e "Dispositivo" usando o valor hash do UID gerado anteriormente
    aluno = Aluno.get_aluno_by_disp(disp_uid)

    # Verifica se o aluno obtido da consulta não existe
    if not aluno:
        return jsonify(error="Não existe nenhum aluno associado ao UID lido."), 404

    if aluno.id in sala_selecionada['alunos']:
        return jsonify(error="Aluno já está na lista de presenças"), 304

    # Adiciona o número do aluno à lista de presenças,
    # avisa que existem alunos novos na lista e retorna uma resposta JSON com o código 200 OK
    sala_selecionada['alunos'].append(aluno.id)
    return jsonify(message="Marcação da presença efetuada com sucesso."), 201


@main.route("/presencas/marcar", methods=["PUT"])
def marcar_presenca():
    # Obtém os dados JSON da solicitação POST
    params = request.get_json()
    sala_a_controlar, num_aluno = params['sala'].strip(), params['aluno'].strip()

    # Verifica se os dados JSON obtidos são inválidos
    if not sala_a_controlar or not num_aluno:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    # Verifica se a sala a controlar está registada no dicionário "aulas_a_decorrer"
    if sala_a_controlar not in aulas_a_decorrer:
        return jsonify(error="A sala não tem nenhum registo ativo."), 404

    # Guarda o dicionário da sala selecionada numa variável
    sala_selecionada = aulas_a_decorrer[sala_a_controlar]

    # Verifica se o valor da chave "status" da sala selecionada é igual a "STOP"
    if sala_selecionada['estado'] == "STOP":
        return jsonify(error="Não pode marcar presença numa sala que se encontra com marcações em pausa."), 403

    # Verifica se o aluno inserido já consta na lista de alunos da aula a decorrer
    if num_aluno in sala_selecionada['alunos']:
        return jsonify(error="Este aluno já tem a sua presença registada."), 304

    # Adiciona o número do aluno à lista de presenças,
    # altera a flag para informar que existem alunos novos na lista e retorna uma mensagem de sucesso.
    sala_selecionada['alunos'].append(num_aluno)
    return jsonify(message="Marcação da presença efetuada com sucesso."), 201


@main.route("/presencas/eliminar", methods=["POST"])
def eliminar_presenca():
    # Obtém os dados JSON da solicitação POST
    params = request.get_json()
    sala_a_controlar, num_aluno = params['sala'].strip(), params['aluno'].strip()

    # Verifica se os dados JSON obtidos são inválidos
    if not sala_a_controlar or not num_aluno:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    # Verifica se a sala a controlar está registada no dicionário "aulas_a_decorrer"
    if sala_a_controlar not in aulas_a_decorrer:
        return jsonify(error="A sala não tem nenhum registo ativo."), 404

    # Guarda o dicionário da sala selecionada numa variável
    sala_selecionada = aulas_a_decorrer[sala_a_controlar]

    # Verifica se o aluno inserido não consta na lista de alunos da aula a decorrer
    if num_aluno not in sala_selecionada['alunos']:
        return jsonify(error="Este aluno não consta na lista de presenças."), 409

    # Adiciona o número do aluno à lista de presenças,
    # altera a flag para informar que existem alunos novos na lista e retorna uma mensagem de sucesso.
    sala_selecionada['alunos'].remove(num_aluno)
    return jsonify(message="Aluno retirado da lista com sucesso"), 200
