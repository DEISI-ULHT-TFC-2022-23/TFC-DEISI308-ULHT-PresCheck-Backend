import random
from time import time

import jwt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet

db = SQLAlchemy()
fernet = Fernet(Fernet.generate_key())

professor_unidade = db.Table('professor_unidade',
                             db.Column('unidade_id', db.Integer, db.ForeignKey('unidade.id')),
                             db.Column('professor_id', db.Integer, db.ForeignKey('professor.id'))
                             )


class Unidade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    aulas = db.relationship('Aula', backref='unidade')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Unidade %r>' % self.id

    def __str__(self):
        return self.nome

    @staticmethod
    def create(unidade_id, nome):
        unidade_exists = Unidade.query.get(unidade_id)
        if unidade_exists:
            return False, unidade_exists

        unidade = Unidade()
        unidade.id = unidade_id
        unidade.nome = nome

        db.session.add(unidade)
        db.session.commit()
        return True, unidade


class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.relationship('User', backref='professor')
    unidades = db.relationship('Unidade', secondary='professor_unidade', backref='professores')
    aulas = db.relationship('Aula', backref='professor')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Professor %r>' % self.id

    def __str__(self):
        return '%s' % self.id

    def associate_unidades(self, unidades):
        for unidade in unidades:
            self.unidades.append(unidade)
        db.session.commit()

    @staticmethod
    def get_unidades(professor_id):
        prof = Professor.query.get(professor_id)
        return [{'id': unidade.id, 'nome': unidade.nome} for unidade in prof.unidades]

    @staticmethod
    def create(professor_id, unidades=None):
        prof_exists = Professor.query.get(professor_id)

        if prof_exists:
            return False, prof_exists

        prof = Professor()
        prof.id = professor_id

        if unidades:
            prof.associate_unidades(unidades)

        db.session.add(prof)
        db.session.commit()
        return True, prof


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(8), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean(), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey("professor.id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<User %r>' % self.username

    def __str__(self):
        return '%s' % self.username

    def associate_prof(self, professor_id, commit=False):
        self.professor_id = professor_id

        if commit:
            db.session.commit()

    def set_password(self, password, commit=False):
        self.password = generate_password_hash(password, method='sha256')

        if commit:
            db.session.commit()

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def get_reset_token(self):
        import app
        return jwt.encode(payload={'reset_password': self.username,
                                   'exp': time() + 5 * 60},
                          key=app.Configuration.SECRET_KEY)

    @staticmethod
    def verify_reset_token(token):
        try:
            import app
            data = jwt.decode(token, key=app.Configuration.SECRET_KEY, algorithms=['HS256', ])
            username = data['reset_password']
            if time() > data['exp']:
                raise Exception
        except Exception as e:
            print(e)
            return None
        return User.query.filter_by(username=username).first()

    @staticmethod
    def create(username, password, is_admin, is_active, professor_id=None):

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            return False, user_exists

        user = User()
        user.username = username
        user.is_admin = is_admin
        user.is_active = is_active
        user.set_password(password)

        if professor_id:
            user.associate_prof(professor_id)

        db.session.add(user)
        db.session.commit()
        return True, user

    @staticmethod
    def login_user(username, password):

        user = User.query.filter_by(username=username).first()

        if user:
            if user.verify_password(password) and user.is_active:
                return True, {'professor_id': user.professor_id, 'is_admin': user.is_admin}

        return False, {}

    @staticmethod
    def verify_user(username):
        return User.query.filter_by(username=username).first()


class Aluno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    presencas = db.relationship('Presenca', backref='aluno')
    dispositivos = db.relationship('Dispositivo', backref='aluno')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Aluno %r>' % self.id

    def __str__(self):
        return self.id

    @staticmethod
    def create(aluno_id):
        aluno_exists = Aluno.query.get(aluno_id)
        if aluno_exists:
            return False, aluno_exists

        aluno = Aluno()
        aluno.id = aluno_id

        db.session.add(aluno)
        db.session.commit()
        return True, aluno

    @staticmethod
    def get_aluno_by_disp(disp_uid):
        aluno_uid_hash = generate_password_hash(disp_uid, method='sha256')
        return Aluno.query.join(Dispositivo).filter(Dispositivo.uid == aluno_uid_hash).first()


class Dispositivo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.String(100), unique=True, nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Dispositivo %r>' % self.id

    def __str__(self):
        return '%s (de: %s)' % (self.uid, self.aluno_id)

    @staticmethod
    def create(uid, aluno_id):
        aluno_exists = Aluno.query.get(aluno_id)
        if not aluno_exists:
            return False, aluno_exists

        uid_exists = Dispositivo.query.filter_by(uid=uid).first()
        if uid_exists:
            return False, uid_exists

        disp = Dispositivo()
        disp.uid = uid
        disp.aluno_id = aluno_id

        db.session.add(disp)
        db.session.commit()
        return True, disp


class Sala(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(7), nullable=False, unique=True)
    arduino_id = db.Column(db.String(100), nullable=False, unique=True)
    aulas = db.relationship('Aula', backref='sala')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Sala %r>' % self.nome

    def __str__(self):
        return self.nome

    @staticmethod
    def create(nome, arduino_id):
        sala_exists = Sala.query.filter_by(nome=nome)
        if sala_exists:
            return False, sala_exists

        uid_exists = Sala.query.filter_by(arduino_id=arduino_id).first()
        if uid_exists:
            return False, uid_exists

        sala = Sala()
        sala.nome = nome
        sala.arduino_id = generate_password_hash(arduino_id, method="sha256")

        db.session.add(sala)
        db.session.commit()
        return True, sala

    @staticmethod
    def get_sala_by_arduino(arduino_id):
        arduino_id_hash = generate_password_hash(arduino_id, method="sha256")
        return Sala.query.filter_by(arduino_id=arduino_id_hash).first()


class Aula(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidade.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=False)
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    presencas = db.relationship('Presenca', backref='aula')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Aula %r %r>' % (self.id, self.created_at)

    def __str__(self):
        unidade = Unidade.query.get(self.unidade_id)
        data_formatada = self.created_at.strftime('%d/%m/%Y')
        return '%s em %s' % (unidade.nome, data_formatada)

    @staticmethod
    def create(nome_sala, unidade_id, professor_id):
        sala = Sala.query.filter_by(nome=nome_sala).first()
        aula = Aula()
        aula.sala_id = sala.id
        aula.unidade_id = unidade_id
        aula.professor_id = professor_id

        db.session.add(aula)
        db.session.commit()
        return True, aula

    @staticmethod
    def export(aula_id):
        presencas_aula = Presenca.query.filter_by(aula_id=aula_id).all()
        data = [[presenca.aluno_id, presenca.created_at.strftime('%d/%m/%Y às %H:%M')] for presenca in presencas_aula]
        return data


class Presenca(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    aula_id = db.Column(db.Integer, db.ForeignKey('aula.id'))
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'))
    created_at = db.Column(db.DateTime, server_default=func.now())

    def __repr__(self):
        return '<Presença %r>' % self.id

    def __str__(self):
        data_formatada = self.created_at.strftime('%d/%m/%Y às %H:%M')
        return '%s em %s' % (self.aluno_id, data_formatada)

    @staticmethod
    def create(aula_id, alunos):
        presencas = []
        for aluno in alunos:
            aluno_selecionado = Aluno.create(aluno)
            if not aluno_selecionado:
                aluno_selecionado = aluno_selecionado[1]

            nova_presenca = Presenca(aula_id=aula_id, aluno_id=aluno_selecionado[1].id)
            presencas.append(nova_presenca)

        db.session.add_all(presencas)
        db.session.commit()
        return True, presencas
