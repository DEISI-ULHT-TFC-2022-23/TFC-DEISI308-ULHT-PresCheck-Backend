from flask import Flask, request, abort, redirect, render_template, session
from models import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projeto.db'


@app.route('/')
def hello_world():
    if 'professor_id' in session:
        return redirect('/dashboard')
    return "Hello"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_password(username, password):
            professor = Professor.query.get(id=username)
            session['professor_id'] = professor.id
            return redirect('/dashboard')
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'professor_id' not in session:
        return redirect('/')
    professor = Professor.query.get(session['professor_id'])
    return render_template('dashboard.html', professor=professor)


@app.route('/logout')
def logout():
    session.pop('professor_id', None)
    return redirect('/')


@app.route("/arduinoPresence", methods=["POST"])
def arduino_presence():
    if request.content_type == "application/json" and "Arduino" in request.headers.get("User-Agent"):
        return "Arduino presence confirmed"
    else:
        abort(403)


if __name__ == '__main__':
    #db.create_all()
    app.run(debug=True, port=5000, host='0.0.0.0')
    # flask run --host="0.0.0.0"
