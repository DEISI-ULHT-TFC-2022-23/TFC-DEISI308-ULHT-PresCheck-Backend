from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean(), nullable=False, default=False)
    professor_id = db.Column(db.Integer, db.ForeignKey("professor.id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<User %r>' % self.username

    def is_admin(self):
        return self.is_admin

    def is_active(self):
        return self.is_active()


class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.relationship('User', backref='professor')
    unidades = db.relationship('UnidadeCurricular', backref='professor')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Professor %r %r>' % (self.first_name, self.last_name)

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)


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


class UnidadeCurricular(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Integer, unique=True)
    name = db.Column(db.String, nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=True)
    aulas = db.relationship('Aula', backref='unidadecurricular')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<UnidadeCurricular %r>' % self.id

    def __str__(self):
        return self.name


class Sala(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(7), nullable=False)
    arduino_id = db.Column(db.String, nullable=False)
    aulas = db.relationship('Aula', backref='sala')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Sala %r>' % self.name

    def __str__(self):
        return self.name


class Aula(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidadecurricular.id'), nullable=True)
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=True)
    presencas = db.relationship('Presenca', backref='aula')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Aula %r %r>' % (self.id, self.date)

    def __str__(self):
        unidade = UnidadeCurricular.query.get(self.unidade_id)
        date_formatted = self.date.strftime('%d/%m/%Y às %H:%M')
        return '%s em %s' % (unidade.name, date_formatted)


class Presenca(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    aula_id = db.Column(db.Integer, db.ForeignKey('aula.id'))
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'))
    created_at = db.Column(db.DateTime, server_default=func.now())

    def __repr__(self):
        return '<Presença %r>' % self.id

    def __str__(self):
        date_formatted = self.created_at.strftime('%d/%m/%Y às %H:%M')
        return '%s em %s' % (self.aluno_id, date_formatted)
