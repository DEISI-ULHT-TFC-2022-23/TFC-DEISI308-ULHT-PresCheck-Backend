import datetime

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash

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
        alunos : [(Número aluno 1), (Número aluno 2), ...],
        alunos_novos : True/False
    }
}
"""
aulas_a_decorrer = {}


@main.route("/unidades", methods=["GET"])
def get_unidades():
    # Verifica se não há argumentos na requisição ou se o argumento 'professor_id' está em falta
    if not request.args or not request.args.get('professor_id'):
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    professor = Professor.query.get(request.args.get('professor_id'))

    # Verifica se o professor não existe na base de dados
    if not professor:
        return jsonify(error="Não existem professores com esse id"), 404

    # Retorna a lista de unidades associadas ao professor como resposta e com código de status 200 (OK)
    return jsonify(unidades=professor.get_unidades()), 200


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
            aulas_ativas = {'sala': sala, 'unidade': unidade.nome, 'estado':dados['estado']}

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
        'alunos': [],
        'alunos_novos': False
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
            # Obtém a sala registada na base de dados a partir do nome
            sala = Sala.query.filter_by(nome=sala_param).first()
            # Cria uma aula na base de dados com as informações da sala em andamento
            nova_aula = Aula(data_aula=datetime.date.today(),
                             unidade_id=dados_sala['unidade_id'],
                             professor_id=dados_sala['professor_id'],
                             sala_id=sala.id)
            db.session.add(nova_aula)

            # Para cada aluno presente na sala em andamento, cria uma presença na base de dados
            for aluno in dados_sala['alunos']:
                aluno_selecionado = Aluno.query.get(aluno)
                if not aluno_selecionado:
                    aluno_selecionado = Aluno(aluno_id=aluno)
                    db.session.add(aluno_selecionado)

                nova_presenca = Presenca(aula_id=nova_aula.id,
                                         aluno_id=aluno_selecionado.id)
                db.session.add(nova_presenca)

            db.session.commit()
            # Remove a sala em andamento da lista de aulas em andamento e retorna o código a informar que foi processado
            del aulas_a_decorrer[sala_param]
            return jsonify(message="Registos inseridos e aula terminada.", aula_id=nova_aula.id), 204

    # Retorna o estado da aula atualizado
    return jsonify(status=aulas_a_decorrer[sala_param]['estado']), 200


@main.route("/aula/exportar", methods=["GET"])
def exportar_aula():
    # Verifica se não há argumentos na requisição ou se o argumento 'aula_id' está em falta
    if not request.args or not request.args.get('aula_id'):
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    # Busca todas as presenças associadas à aula e verifica se existe alguma presença
    presencas_aula = Presenca.query.filter_by(aula_id=request.args.get('aula_id')).all()
    if not presencas_aula:
        return jsonify(error="Não existem presençar marcadas para esta aula."), 404

    # Itera sobre todas as presenças e guarda na lista corretamente.
    data = []
    for presenca in presencas_aula:
        aluno_id = presenca.aluno_id
        created_at = presenca.created_at.strftime('%d/%m/%Y às %H:%M')
        data.append([aluno_id, created_at])

    # Retorna a lista de todas as presenças
    return jsonify(presencas=data), 200


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
    # Verifica se o tipo de conteúdo da solicitação é "application/json"
    # e se o cabeçalho "User-Agent" contém a ‘string’ "ArduinoULHT"
    if request.content_type != "application/json" or "ArduinoULHT" not in request.headers.get("User-Agent"):
        jsonify(error="[CRITICAL] O cabeçalho da requisição é inválido!"), 400

    # Obtém os dados JSON da solicitação POST
    params = request.get_json()
    arduino_id, disp_uid = params['identifier'].strip(), params['sent_uid'].strip()

    # Verifica se os dados JSON obtidos são inválidos
    if not arduino_id or not disp_uid:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    # Consulta o modelo de banco de dados "Sala" usando o valor da chave "identifier" obtida dos dados JSON
    arduino_id_hash = generate_password_hash(arduino_id, method='sha256')
    sala = Sala.query.filter_by(arduino_id=arduino_id_hash).first()

    # Verifica se a sala obtida da consulta não existe ou se o ‘id’ da sala não está presente na lista
    # "aulas_a_decorrer"
    if not sala or sala.nome not in aulas_a_decorrer:
        return jsonify(error="A sala não foi encontrada ou não existe marcação ativa."), 404

    # Guarda o dicionário da sala selecionada numa variável
    sala_selecionada = aulas_a_decorrer[sala.id]

    # Verifica se o valor da chave "status" da sala selecionada é igual a "STOP"
    if sala_selecionada['estado'] == "STOP":
        return jsonify(error="Não pode marcar presença numa sala que se encontra com marcações em pausa."), 403

    # Gera um hash do UID do dispositivo do aluno obtida dos dados JSON usando o algoritmo de hash SHA256
    aluno_uid_hash = generate_password_hash(disp_uid, method='sha256')

    # Consulta os modelos da base de dados "Aluno" e "Dispositivo" usando o valor hash do UID gerado anteriormente
    aluno = Aluno.query.join(Dispositivo).filter(Dispositivo.uid == aluno_uid_hash).first()

    # Verifica se o aluno obtido da consulta não existe
    if not aluno:
        return jsonify(error="Não existe nenhum aluno associado ao UID lido."), 404

    # Adiciona o número do aluno à lista de presenças,
    # avisa que existem alunos novos na lista e retorna uma resposta JSON com o código 200 OK
    sala_selecionada['alunos'].append(aluno.id)
    sala_selecionada['alunos_novos'] = True
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
        return jsonify(error="Este aluno já tem a sua presença registada."), 409

    # Adiciona o número do aluno à lista de presenças,
    # altera a flag para informar que existem alunos novos na lista e retorna uma mensagem de sucesso.
    sala_selecionada['alunos'].append(num_aluno)
    sala_selecionada['alunos_novos'] = True
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
