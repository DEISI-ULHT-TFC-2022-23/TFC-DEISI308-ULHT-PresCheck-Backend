import random
import re
import string

import jwt
from cryptography.fernet import Fernet
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import NoResultFound
from sqlalchemy.sql import func, distinct
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
fernet = Fernet(Fernet.generate_key())

professor_unidade = db.Table('professor_unidade',
                             db.Column('unidade_id', db.Integer, db.ForeignKey('unidade.id')),
                             db.Column('professor_id', db.Integer, db.ForeignKey('professor.id'))
                             )

professor_turma = db.Table('professor_turma',
                           db.Column('turma_id', db.Integer, db.ForeignKey('turma.id')),
                           db.Column('professor_id', db.Integer, db.ForeignKey('professor.id'))
                           )


class Unidade(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo = db.Column(db.String, unique=True, nullable=False)
    nome = db.Column(db.String, nullable=False)
    aulas = db.relationship('Aula', backref='unidade')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Unidade %r>' % self.id

    def __str__(self):
        return f"{self.codigo} | {self.nome}"

    @staticmethod
    def create(codigo, nome):
        unidade_exists = Unidade.query.filter_by(codigo=codigo).first()
        if unidade_exists:
            return False, unidade_exists

        unidade = Unidade()
        unidade.codigo = codigo
        unidade.nome = nome

        db.session.add(unidade)
        db.session.commit()
        return True, unidade

    @staticmethod
    def delete(unidade_id):
        unidade = Unidade.query.get(unidade_id)
        if unidade:
            db.session.delete(unidade)
            db.session.commit()
            return True
        return False


class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.relationship('User', backref='professor')
    unidades = db.relationship('Unidade', secondary='professor_unidade', backref='professores')
    turmas = db.relationship('Turma', secondary='professor_turma', backref='professores')
    aulas = db.relationship('Aula', backref='professor')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Professor %r>' % self.id

    def __str__(self):
        return '%s' % self.id

    def associate_unidades(self, unidades, commit=False):
        for unidade_id in unidades:
            unidade = Unidade.query.get(unidade_id)
            if unidade:
                self.unidades.append(unidade)

        if commit:
            db.session.commit()

    def remove_unidade(self, unidade_id, commit=False):
        unidade = Unidade.query.get(unidade_id)
        if unidade:
            self.unidades.remove(unidade)

        if commit:
            db.session.commit()

    def associate_turmas(self, turmas, commit=False):
        for turma_id in turmas:
            turma = Turma.query.get(turma_id)
            if turma:
                self.turmas.append(turma)

        if commit:
            db.session.commit()

    def remove_turma(self, turma_id, commit=False):
        turma = Turma.query.get(turma_id)
        if turma:
            self.turmas.remove(turma)

        if commit:
            db.session.commit()

    @staticmethod
    def get_unidades(professor_id):
        prof = Professor.query.get(professor_id)
        return [{'id': unidade.id, 'codigo': unidade.codigo, 'nome': unidade.nome}
                for unidade in prof.unidades] or []

    @staticmethod
    def get_turmas(professor_id):
        prof = Professor.query.get(professor_id)
        return [{'id': turma.id, 'nome': turma.nome, 'alunos': [aluno.id for aluno in turma.alunos]}
                for turma in prof.turmas] or []

    @staticmethod
    def create(professor_id, unidades, turmas):
        prof_exists = Professor.query.get(professor_id)
        if prof_exists:
            return False, prof_exists

        prof = Professor()
        prof.id = professor_id
        prof.associate_unidades(unidades)
        prof.associate_turmas(turmas)

        db.session.add(prof)
        db.session.commit()
        return True, prof


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(8), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    is_admin = db.Column(db.Boolean(), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False)
    reset_token = db.Column(db.Integer, nullable=True)
    professor_id = db.Column(db.Integer, db.ForeignKey("professor.id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<User %r>' % self.username

    def __str__(self):
        return '%s' % self.username

    def associate_prof(self, professor_id, commit=False):
        try:
            Professor.query.filter_by(id=professor_id).one()
        except NoResultFound:
            return False

        self.professor_id = professor_id

        if commit:
            db.session.commit()

        return True

    def set_password(self, password, commit=False):
        self.password = generate_password_hash(password, method='sha256')

        if commit:
            db.session.commit()

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def get_associated_unidades(self):
        if not self.professor_id:
            return []

        return Professor.get_unidades(self.professor_id)

    def get_associated_turmas(self):
        if not self.professor_id:
            return []

        return Professor.get_turmas(self.professor_id)

    def update(self, is_admin, is_active, commit=False):
        self.is_admin = is_admin
        self.is_active = is_active

        if commit:
            db.session.commit()

    def get_professor(self):
        return Professor.query.get(self.professor_id)

    def generate_session_token(self):
        from app import Configuration
        return jwt.encode(payload={'user': self.username,
                                   'active': self.is_active,
                                   'admin': self.is_admin},
                          key=Configuration.SECRET_KEY,
                          algorithm='HS256')

    def generate_reset_token(self):
        token = ''.join(str(random.randint(0, 9)) for _ in range(6))
        self.reset_token = token
        db.session.commit()
        return token

    @staticmethod
    def verify_session_token(token):
        from app import Configuration
        data = jwt.decode(token, key=Configuration.SECRET_KEY, algorithms=['HS256', ])
        user_exists = User.query.filter_by(username=data['user']).first()

        if not user_exists:
            return None

        return data

    @staticmethod
    def verify_reset_token(username, token):
        user = User.query.filter_by(username=username, token=token).first()
        if user:
            user.reset_token = None
            db.session.commit()
            return True
        return False

    @staticmethod
    def create(username, user_id=None, is_admin=False, is_professor=False, unidades=None, turmas=None, password=None):
        if unidades is None:
            unidades = []

        if turmas is None:
            turmas = []

        user_exists = User.verify_user(username)
        if user_exists:
            return False, user_exists

        random_password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))

        user = User()
        user.id = user_id
        user.username = username
        user.is_admin = is_admin
        user.is_active = True
        user.set_password(password or random_password)

        if is_professor:
            professor_id = re.findall(r'\d+', username)[0]
            Professor.create(professor_id, unidades, turmas)
            user.associate_prof(professor_id)

        db.session.add(user)
        db.session.commit()
        return True, user, (password or random_password)

    @staticmethod
    def login_user(username, password):
        user = User.query.filter_by(username=username).first()
        if user:
            if user.verify_password(password) and user.is_active:
                return True, user

        return False, None

    @staticmethod
    def verify_user(username):
        return User.query.filter_by(username=username).first()


class Turma(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(20), unique=True, nullable=False)
    alunos = db.relationship('Aluno', backref='turma', cascade="all,delete")
    aulas = db.relationship('Aula', backref='turma', cascade="all,delete")
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Turma %r>' % self.id

    def __str__(self):
        return self.nome

    def update(self, nome, commit=False):
        if nome != self.nome:
            turma_exists = Turma.query.filter_by(nome=nome).first()
            if turma_exists:
                return False
            self.nome = nome

        if commit:
            db.session.commit()

        return True

    @staticmethod
    def get_turma(nome):
        return Turma.query.filter_by(nome=nome).first()

    @staticmethod
    def create(nome):
        turma_exists = Turma.query.filter_by(nome=nome).first()
        if turma_exists:
            return False, turma_exists

        turma = Turma()
        turma.nome = nome

        db.session.add(turma)
        db.session.commit()
        return True, turma

    @staticmethod
    def delete(turma_id):
        turma = Turma.query.get(turma_id)
        if not turma:
            return False

        db.session.delete(turma)
        db.session.commit()
        return True


class Aluno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey("turma.id"), nullable=False)
    presencas = db.relationship('Presenca', backref='aluno', cascade="all,delete")
    dispositivos = db.relationship('Dispositivo', backref='aluno', cascade="all,delete")
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Aluno %r>' % self.id

    def __str__(self):
        return self.id

    def get_last_classes(self, n=5):
        presencas = Presenca.query.filter_by(aluno_id=self.id).join(Aula).join(Unidade).order_by(
            Presenca.created_at.desc()).limit(n).all()
        return [{"unidade": presenca.aula.unidade.nome, "presenca": presenca.created_at}
                for presenca in presencas]

    def get_turma_name(self):
        return Turma.query.get(self.turma_id).nome

    def update_turma(self, turma_id, commit=False):
        turma_exists = Turma.query.get(turma_id)
        if turma_id != self.turma_id and turma_exists:
            self.turma_id = turma_id
        else:
            return False

        if commit:
            db.session.commit()

        return True

    @staticmethod
    def create(aluno_id, turma_id):
        aluno_exists = Aluno.query.get(aluno_id)
        if aluno_exists:
            return False, aluno_exists

        aluno = Aluno()
        aluno.id = aluno_id
        aluno.turma_id = turma_id

        db.session.add(aluno)
        db.session.commit()
        return True, aluno

    @staticmethod
    def delete(aluno_id):
        aluno = Aluno.query.get(aluno_id)
        if aluno:
            db.session.delete(aluno)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_aluno_by_disp(disp_uid):
        return Aluno.query.join(Dispositivo).filter(Dispositivo.uid == disp_uid).first()


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

        uid_exists = Dispositivo.query.filter_by(uid=uid).all()
        if uid_exists:
            return False, uid_exists

        disp = Dispositivo()
        disp.uid = uid
        disp.aluno_id = aluno_id

        db.session.add(disp)
        db.session.commit()
        return True, disp

    @staticmethod
    def delete(aluno_id, uid):
        aluno = Aluno.query.get(aluno_id)
        if not aluno:
            return False

        dispositivo = Dispositivo.query.filter_by(aluno_id=aluno_id, uid=uid).first()
        if not dispositivo:
            return False

        db.session.delete(dispositivo)
        db.session.commit()
        return True


class Sala(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(7), nullable=False, unique=True)
    arduino = db.relationship('Arduino', back_populates='sala', uselist=False, cascade="save-update, none")
    aulas = db.relationship('Aula', backref='sala', cascade="save-update, none")
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Sala %r>' % self.nome

    def __str__(self):
        return self.nome

    @staticmethod
    def get_sala_by_arduino(arduino_uid):
        return Sala.query.join(Arduino).filter(Arduino.uid == arduino_uid).first()

    @staticmethod
    def create(nome, arduino_id, ip_address):
        sala_exists = Sala.query.filter_by(nome=nome).first()
        if sala_exists:
            return False, sala_exists

        sala = Sala()
        sala.nome = nome

        db.session.add(sala)
        db.session.commit()

        arduino = Arduino.create(arduino_id, ip_address, sala.id)
        if not arduino[0]:
            db.session.delete(sala)
            db.session.commit()
            return False, arduino[1]

        return True, sala

    @staticmethod
    def delete(sala_id):
        sala = Sala.query.get(sala_id)
        if not sala:
            return False

        db.session.delete(sala)
        db.session.commit()

        arduino = Arduino.delete(sala.arduino.id)
        if not arduino:
            return False

        return True


class Arduino(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.String(100), nullable=False, unique=True)
    ip_address = db.Column(db.String(100), nullable=False, unique=True)
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False, unique=True)
    sala = db.relationship("Sala", back_populates="arduino", uselist=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Arduino %r>' % self.id

    def __str__(self):
        return '%s (de: %s)' % (self.uid, self.sala)

    @staticmethod
    def create(uid, ip_address, sala_id):
        uid_exists = Arduino.query.filter_by(uid=uid).all()
        if uid_exists:
            return False, uid_exists

        ip_address_exists = Arduino.query.filter_by(ip_address=ip_address).all()
        if ip_address_exists:
            return False, ip_address_exists

        arduino = Arduino()
        arduino.uid = uid
        arduino.ip_address = ip_address
        arduino.sala_id = sala_id

        db.session.add(arduino)
        db.session.commit()
        return True, arduino

    @staticmethod
    def delete(arduino_id):
        arduino = Arduino.query.get(arduino_id)
        if arduino:
            db.session.delete(arduino)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_arduino_by_sala(tipo, sala):
        if tipo == 'nome':
            return Arduino.query.join(Sala).filter(Sala.nome == sala).first()
        elif tipo == 'id':
            return Arduino.query.join(Sala).filter(Sala.id == sala).first()

    @staticmethod
    def get_arduino_by_uid(uid):
        return Arduino.query.filter_by(uid=uid).first()

    @staticmethod
    def get_arduino_by_ip(ip_address):
        return Arduino.query.filter_by(ip_address=ip_address).first()


class Aula(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidade.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=False)
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    presencas = db.relationship('Presenca', backref='aula', cascade="all,delete")
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Aula %r %r>' % (self.id, self.created_at)

    def __str__(self):
        unidade = Unidade.query.get(self.unidade_id)
        data_formatada = self.created_at.strftime('%d/%m/%Y')
        return '%s em %s' % (unidade.nome, data_formatada)

    @staticmethod
    def create(nome_sala, unidade_id, professor_id, turma_id, data_aula):
        sala = Sala.query.filter_by(nome=nome_sala).first()
        aula = Aula()
        aula.sala_id = sala.id
        aula.unidade_id = unidade_id
        aula.professor_id = professor_id
        aula.turma_id = turma_id
        aula.created_at = data_aula

        db.session.add(aula)
        db.session.commit()
        return True, aula

    @staticmethod
    def export(aula_id):
        aula = Aula.query.get(aula_id)
        data = [[presenca.aluno_id, presenca.created_at.strftime('%d/%m/%Y às %H:%M')]
                for presenca in aula.presencas] or []
        return data, aula.created_at.strftime('%d/%m/%Y às %H:%M')


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
    def create(aula, alunos):
        presencas = []
        for aluno in alunos:
            aluno_selecionado = Aluno.create(aluno["numero"], aula.turma_id)

            nova_presenca = Presenca()
            nova_presenca.aula_id = aula.id
            nova_presenca.aluno_id = aluno_selecionado[1].id
            nova_presenca.created_at = aluno["timestamp"]
            presencas.append(nova_presenca)

        db.session.add_all(presencas)
        db.session.commit()
        return True, presencas
