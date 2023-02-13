from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class UnidadeCurricular(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    professores = db.relationship('Professor',
                                  secondary='UnidadeCurricular_Professor',
                                  back_populates='professores')
    aulas = db.relationship('Aula', backref='unidade')

    def __init__(self, unidade_id, name):
        self.id = unidade_id
        self.name = name

    def __repr__(self):
        return '<UnidadeCurricular %r>' % self.id

    def __str__(self):
        return self.name


class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    password = db.Column(db.String, nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    unidades_curriculares = db.relationship('UnidadeCurricular',
                                            secondary='UnidadeCurricular_Professor',
                                            back_populates='unidades')
    aulas = db.relationship('Aula', backref='professor')

    def __init__(self, professor_id, first_name, last_name, is_active=False, is_admin=False):
        self.id = professor_id
        self.first_name = first_name
        self.last_name = last_name
        self.is_active = is_active
        self.is_admin = is_admin

    def __repr__(self):
        return '<Professor %r %r>' % (self.first_name, self.last_name)

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)


class UnidadeCurricular_Professor(db.Model):
    professor_id = db.Column(db.Integer, db.ForeignKey('Professor.id'), primary_key=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('UnidadeCurricular.id'), primary_key=True)

    def __init__(self, prof_id, unid_id):
        self.professor_id = prof_id
        self.unidade_id = unid_id

    def __repr__(self):
        return '<UnidadeCurricular_Professor %s %s>' % (self.unidade_id, self.professor_id)

    def __str__(self):
        return '%s - %s' % (self.unidade_id, self.professor_id)


class Aula(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime)
    duration = db.Column(db.Interval, nullable=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('UnidadeCurricular.id'))
    professor_id = db.Column(db.Integer, db.ForeignKey('Professor.id'))
    presencas = db.relationship('Presenca', backref='aula')

    def __init__(self, date, unidade_id, professor_id, duration=None):
        self.date = date
        self.unidade_id = unidade_id
        self.professor_id = professor_id
        self.duration = duration

    def __repr__(self):
        return '<Aula %r %r>' % (self.id, self.date)

    def __str__(self):
        unidade = UnidadeCurricular.query.get(self.unidade_id)
        date_formatted = self.date.strftime('%d/%m/%Y às %H:%M')
        return '%s em %s' % (unidade.name, date_formatted)


class Presenca(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time = db.Column(db.DateTime)
    aula_id = db.Column(db.Integer, db.ForeignKey('Aula.id'))
    aluno_id = db.Column(db.Integer, db.ForeignKey('Aluno.id'))

    def __init__(self, aula_id, aluno_id, time):
        self.aula_id = aula_id
        self.aluno_id = aluno_id
        self.time = time

    def __repr__(self):
        return '<Presença %r>' % self.id

    def __str__(self):
        date_formatted = self.date.strftime('%d/%m/%Y às %H:%M')
        return '%s em %s' % (self.aluno_id, date_formatted)


class Aluno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    presencas = db.relationship('Presenca', backref='aluno')
    dispositivos = db.relationship('Dispositivo', backref='aluno')

    def __init__(self, aluno_id, first_name=None, last_name=None):
        self.id = aluno_id
        self.first_name = first_name
        self.last_name = last_name

    def __repr__(self):
        return '<Aluno %r>' % self.id

    def __str__(self):
        return self.id


class Dispositivo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.String)
    aluno_id = db.Column(db.Integer, db.ForeignKey('Aluno.id'))

    def __init__(self, uid, aluno_id):
        self.uid = uid
        self.aluno_id = aluno_id

    def __repr__(self):
        return '<Dispositivo %r>' % self.id

    def __str__(self):
        return '%s (de: %s)' % (self.uid, self.aluno_id)


def check_password(username, password):
    professor = Professor.query.filter_by(id=username).first()
    if professor is None:
        return False
    return professor.password == password
