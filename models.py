from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()

professor_unidade = db.Table('professor_unidade',
                             db.Column('unidade_id', db.Integer, db.ForeignKey('unidade.id')),
                             db.Column('professor_id', db.Integer, db.ForeignKey('professor.id'))
                             )


class Unidade(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String, nullable=False)
    aulas = db.relationship('Aula', backref='unidade')
    criado_em = db.Column(db.DateTime, server_default=func.now())
    atualizado_em = db.Column(db.DateTime, onupdate=func.now())

    def __init__(self, codigo, nome):
        self.codigo = codigo
        self.nome = nome

    def __repr__(self):
        return '<Unidade %r>' % self.id

    def __str__(self):
        return self.nome


class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.relationship('User', backref='professor')
    unidades = db.relationship('Unidade', secondary='professor_unidade', backref='professores')
    aulas = db.relationship('Aula', backref='professor')
    criado_em = db.Column(db.DateTime, server_default=func.now())
    atualizado_em = db.Column(db.DateTime, onupdate=func.now())

    def __init__(self, professor_id):
        self.id = professor_id

    def __repr__(self):
        return '<Professor %r %r>' % (self.first_name, self.last_name)

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(8), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    e_admin = db.Column(db.Boolean(), nullable=False)
    esta_ativo = db.Column(db.Boolean(), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey("professor.id"), nullable=True)
    criado_em = db.Column(db.DateTime, server_default=func.now())
    atualizado_em = db.Column(db.DateTime, onupdate=func.now())

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.e_admin = False
        self.esta_ativo = False

    def __repr__(self):
        return '<User %r>' % self.username

    def __str__(self):
        return '%s' % self.username


class Aluno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    presencas = db.relationship('Presenca', backref='aluno')
    dispositivos = db.relationship('Dispositivo', backref='aluno')
    criado_em = db.Column(db.DateTime, server_default=func.now())
    atualizado_em = db.Column(db.DateTime, onupdate=func.now())

    def __init__(self, aluno_id):
        self.id = aluno_id

    def __repr__(self):
        return '<Aluno %r>' % self.id

    def __str__(self):
        return self.id


class Dispositivo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.String(100), unique=True, nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    criado_em = db.Column(db.DateTime, server_default=func.now())
    atualizado_em = db.Column(db.DateTime, onupdate=func.now())

    def __init__(self, uid, aluno_id):
        self.uid = uid
        self.aluno_id = aluno_id

    def __repr__(self):
        return '<Dispositivo %r>' % self.id

    def __str__(self):
        return '%s (de: %s)' % (self.uid, self.aluno_id)


class Sala(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(7), nullable=False, unique=True)
    arduino_id = db.Column(db.String(100), nullable=False, unique=True)
    aulas = db.relationship('Aula', backref='sala')
    criado_em = db.Column(db.DateTime, server_default=func.now())
    atualizado_em = db.Column(db.DateTime, onupdate=func.now())

    def __init__(self, nome, arduino_id):
        self.nome = nome
        self.arduino_id = arduino_id

    def __repr__(self):
        return '<Sala %r>' % self.nome

    def __str__(self):
        return self.nome


class Aula(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data_aula = db.Column(db.Date, nullable=False)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidade.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=False)
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    presencas = db.relationship('Presenca', backref='aula')
    criado_em = db.Column(db.DateTime, server_default=func.now())
    atualizado_em = db.Column(db.DateTime, onupdate=func.now())

    def __init__(self, data_aula, unidade_id, professor_id, sala_id):
        self.data_aula = data_aula
        self.unidade_id = unidade_id
        self.professor_id = professor_id
        self.sala_id = sala_id

    def __repr__(self):
        return '<Aula %r %r>' % (self.id, self.data_aula)

    def __str__(self):
        unidade = Unidade.query.get(self.unidade_id)
        data_formatada = self.data_aula.strftime('%d/%m/%Y')
        return '%s em %s' % (unidade.nome, data_formatada)


class Presenca(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    aula_id = db.Column(db.Integer, db.ForeignKey('aula.id'))
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'))
    criado_em = db.Column(db.DateTime, server_default=func.now())

    def __init__(self, aula_id, aluno_id):
        self.aula_id = aula_id
        self.aluno_id = aluno_id

    def __repr__(self):
        return '<Presença %r>' % self.id

    def __str__(self):
        data_formatada = self.created_at.strftime('%d/%m/%Y às %H:%M')
        return '%s em %s' % (self.aluno_id, data_formatada)
