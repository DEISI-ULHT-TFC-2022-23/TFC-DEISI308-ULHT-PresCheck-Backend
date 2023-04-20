import csv
import datetime

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash

from models import *

main = Blueprint('main', __name__)

""" Dicionário principal de controlo das presenças.
Formato:
{
    [ID Sala] : {
        status: STOP/GO,
        unidade_id: (ID da unidade),
        professor_id: (ID do professor),
        alunos : [(Número aluno 1), (Número aluno 2), ...]
    }
}
"""
aulas_a_decorrer = {}


@main.route("/getPresencas", methods=["GET"])
def get_presencas():
    if not request.args or not request.args.get('sala'):
        return jsonify(error="Falta o parâmetro 'sala'"), 400

    return jsonify(alunos=aulas_a_decorrer[request.args.get('sala')]['alunos']), 200


# @main.route("/iniciarAula", methods=["GET", "POST"])
# def iniciar_aula():
#     # Obtém as unidades curriculares associadas ao professor logado
#     unidades_associadas = Unidade.query.filter_by(professor_id='OK')
#
#     if request.method == "POST":
#         sala_a_abrir = request.form.get('sala')
#
#         # Verifica se existe o parâmetro 'sala' no corpo
#         if not sala_a_abrir:
#             jsonify(error="Falta o parâmetro 'sala'"), 400
#
#         # Verifica se a sala já está registada e ativa nas aulas em andamento
#         if sala_a_abrir in aulas_a_decorrer:
#             jsonify(error="A sala já está registada e ativa!"), 200
#
#         # Cria um dicionário com os dados da aula que será iniciada
#         data = {
#             'status': 'GO',
#             'unidade_id': request.form.get('unidade'),
#             'professor_id': 'OK',
#             'alunos': []
#         }
#         # Adiciona a aula em andamento à lista de aulas em andamento, usando o nome da sala como chave
#         aulas_a_decorrer[sala_a_abrir] = data
#         # Redireciona para a página de controle de aula
#         return redirect(url_for('main.controlar_aula'))
#
#     # Renderiza a página de formulário de início de aula, passando as unidades curriculares associadas
#     return {'unidades': unidades_associadas}
#
#
# @main.route("/controlarAula", methods=["GET", "POST"])
# def controlar_aula():
#     if request.method == "POST":
#         sala = request.form.get('sala')
#         # Verifica qual ação foi realizada no formulário
#         match request.form.get('action'):
#             case "GO":
#                 # Atualiza o estado da aula em andamento para "GO"
#                 aulas_a_decorrer[sala]['status'] = 'GO'
#             case "STOP":
#                 # Atualiza o estado da aula em andamento para "STOP"
#                 aulas_a_decorrer[sala]['status'] = 'STOP'
#             case "FINISH":
#                 # Obtém os dados da sala em andamento
#                 dados_sala = aulas_a_decorrer[sala]
#                 # Obtém a sala a partir do nome
#                 sala = Sala.query.filter_by(name=sala).first()
#                 # Cria uma aula no banco de dados com base nos dados da sala em andamento
#                 nova_aula = Aula(date=datetime.date.today(),
#                                  unidade_id=dados_sala['unidade_id'],
#                                  sala_id=sala.id)
#                 db.session.add(nova_aula)
#
#                 # Para cada aluno presente na sala em andamento, cria uma presença no banco de dados
#                 for aluno in dados_sala['alunos']:
#                     aluno_selecionado = Aluno.query.filter_by(num_aluno=aluno).first()
#                     nova_presenca = Presenca(aula_id=nova_aula.id,
#                                              aluno_id=aluno_selecionado.id)
#                     db.session.add(nova_presenca)
#
#                 db.session.commit()
#                 # Remove a sala em andamento da lista de aulas em andamento
#                 del aulas_a_decorrer[sala]
#                 # Redireciona para a página de exportação de presenças da nova aula criada
#                 return redirect(url_for('main.exportar_presencas', id=nova_aula.id))
#
#         # Renderiza a página de controlo de aula com os dados da sala em andamento
#         return 0
#
#     # Renderiza a página de controlo de aula sem dados da sala em andamento
#     return 0
#
#
# @main.route("/exportarPresencas", methods=["GET", "POST"])
# def exportar_presencas():
#     # Verifica se o parâmetro 'id' está presente nos argumentos da requisição
#     if not request.args.get('id'):
#         # Se não estiver presente, retorna uma resposta HTTP 400 Bad Request
#         abort(400)
#
#     # Obtém o valor do parâmetro 'id' da requisição
#     id_aula = request.args.get('id')
#
#     # Consulta o modelo de banco de dados "Aula" usando o valor do parâmetro 'id'
#     aula_selecionada = Aula.query.get(id=id_aula)
#
#     # Consulta os modelos de banco de dados "Presenca" usando o valor do parâmetro 'id'
#     presencas_aula = Presenca.query.filter_by(aula_id=id_aula).all()
#
#     # Verifica se o método da requisição é POST
#     if request.method == "POST":
#         # Lista para armazenar os dados das presenças
#         data = []
#         for presenca in presencas_aula:
#             # Obtém o ‘id’ do aluno e a data de marcação da presença formatada
#             aluno_id = presenca.aluno_id
#             created_at = presenca.created_at.strftime('%d/%m/%Y às %H:%M')
#             # Adiciona os dados na lista
#             data.append([aluno_id, created_at])
#
#         # Obtém o caminho de arquivo a ser guardado
#         file_path = request.form['file_path']
#
#         # Escreve os dados num arquivo CSV
#         with open(file_path, 'w', newline='') as csvfile:
#             writer = csv.writer(csvfile)
#             writer.writerow(['Num. Aluno', 'Marcação da Presença'])
#             writer.writerows(data)
#
#         # Exibe uma mensagem de sucesso usando o mecanismo de "flash" do Flask
#         flash("Presenças exportadas com sucesso.", 'success')
#
#         # Redireciona para a página inicial após a exportação
#         return redirect(url_for('main.index'))
#
#     # Se o método da requisição não for POST, renderiza um template HTML passando aula selecionada e presenças como
#     # variáveis
#     return 0
#
#
# @main.route("/marcarPresenca", methods=["POST"])
# def arduino_presenca():
#     # Verifica se o tipo de conteúdo da solicitação é "application/json"
#     # e se o cabeçalho "User-Agent" contém a ‘string’ "ArduinoULHT"
#     if request.content_type != "application/json" or "ArduinoULHT" not in request.headers.get("User-Agent"):
#         # Se não atender às condições acima, retorna uma resposta HTTP 412 Precondition Failed
#         abort(412)
#
#     # Obtém os dados JSON da solicitação POST
#     data = request.get_json()
#
#     # Verifica se os dados JSON obtidos são válidos e contêm as chaves "identifier" e "aluno"
#     if not data or 'identifier' not in data or 'aluno_uid' not in data:
#         # Se não atender às condições acima, retorna uma resposta HTTP 404 Not Found
#         abort(404)
#
#     # Consulta o modelo de banco de dados "Sala" usando o valor da chave "identifier" obtida dos dados JSON
#     sala = Sala.query.filter_by(arduino_id=data['identifier']).first()
#
#     # Verifica se a sala obtida da consulta não existe ou se o nome da sala não está presente na lista
#     # "aulas_a_decorrer"
#     if not sala or sala.name not in aulas_a_decorrer:
#         # Se não atender às condições acima, retorna o valor -1 como resposta
#         return -1
#
#     # Verifica se o valor da chave "status" do dicionário correspondente ao nome da sala na lista "aulas_a_decorrer"
#     # é igual a "STOP"
#     if aulas_a_decorrer[sala.name]['status'] == "STOP":
#         # Se não atender à condição acima, retorna o valor -2 como resposta
#         return -2
#
#     # Gera um hash do UID do dispositivo do aluno obtida dos dados JSON usando o algoritmo de hash SHA256
#     req_uid = generate_password_hash(data['aluno_uid'], method='sha256')
#
#     # Consulta os modelos de banco de dados "Aluno" e "Dispositivo" usando o valor hash do UID gerado anteriormente
#     aluno = Aluno.query.join(Dispositivo).filter(Dispositivo.uid == req_uid).first()
#
#     # Verifica se o aluno obtido da consulta não existe
#     if not aluno:
#         # Se não atender à condição acima, retorna o valor -3 como resposta
#         return -3
#
#     # Caso todas as condições anteriores se verificarem verdadeiras, adiciona o número do aluno à lista de presenças
#     # e retorna OK como resposta
#     aulas_a_decorrer[sala.name]['alunos'].append(aluno.id)
#     return "OK"
#
#
# @main.route("/registarAluno", methods=["GET", "POST"])
# def registar_aluno():
#     # Função para registrar um novo aluno, acessível apenas para utilizadores autenticados
#     if request.method == "POST":
#         num_novo_aluno = request.form.get('num_aluno')
#         uid_disp_novo_aluno = request.form.get('uid_aluno')
#
#         # Verifica se os campos obrigatórios estão presentes no formulário
#         if not num_novo_aluno or not uid_disp_novo_aluno:
#             flash("Um ou mais campos estão em falta.", 'error')
#             return redirect(url_for('main.registar_aluno'))
#
#         # Verifica se o aluno já existe no banco de dados
#         aluno_existe = Aluno.query.get(id=num_novo_aluno)
#         if not aluno_existe:
#             # Se o aluno não existe, cria uma instância de Aluno
#             novo_aluno = Aluno(id=num_novo_aluno)
#             db.session.add(novo_aluno)
#
#         # Cria uma instância de Dispositivo associada ao aluno
#         novo_dispositivo = Dispositivo(uid=uid_disp_novo_aluno, aluno_id=num_novo_aluno)
#         db.session.add(novo_dispositivo)
#         db.session.commit()
#
#         # Exibe mensagem de sucesso e redireciona para a página de registro de aluno
#         flash("Aluno e/ou dispositivo foi registado.", 'success')
#         return redirect(url_for('main.registar_aluno'))
#
#     # Renderiza o template para a página de registro de aluno
#     return 0
