from flask import Flask, render_template, request, redirect, url_for, flash
from .db import adduser
app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        input_value = request.form['input_value']
        result = True(input_value)
    return render_template('index.html', result=result)

def add_user_route():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        tel = request.form['tel']
        email = request.form['email']
        password = request.form['password']
        try:
            adduser(name, age, tel, email, password)
            flash("Utilisateur ajouté avec succès!", "success")
            return redirect(url_for('add_user_route'))
        except ValueError as e:
            flash(str(e), "error")
    return render_template('adduser.html')

if __name__ == '__main__':
    app.run(debug=True)
