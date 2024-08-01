from flask import Flask, render_template, request, redirect, url_for, flash
# Assuming that the db directory has an __init__.py file
import sys
import os

# Obtenir le chemin du dossier racine
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Ajouter le dossier racine au chemin de recherche des modules
sys.path.append(project_root)

# Maintenant, vous pouvez importer le module `coucou`
from db import adduser
from tique import create_tiqué 


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flash messages to work

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        input_value = request.form['input_value']
        result = input_value
    return render_template('index.html', result=result)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user_route():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        tel = request.form['tel']
        email = request.form['email']
        password = request.form['password']
        try:
            ID = adduser(name, age, tel, email, password)
            flash("Utilisateur ajouté avec succès!", "success")
            response = app.make_response(redirect(url_for('add_ticket_route')))
            response.set_cookie('ID', ID)  # Set the new cookie
            return response
        except ValueError as e:
            flash(str(e), "error")
    return render_template('creation_conte.html')

@app.route('/new-ticket')
def add_ticket_route():
    if request.method == 'POST':
        ID = request.cookies.get('ID')
        titre = request.form['titre']
        description = request.form['description']
        gravité = request.form['gravité']
        tags = request.form['tags']
        try:
            create_tiqué(ID,titre,description,gravité,tags)
            flash("le ticket a été ajouté avec succès!", "success")
            response = app.make_response(redirect(url_for('add_ticket_route')))
            return response
        except ValueError as e:
            flash(str(e), "error")
    if request.method == 'GET':
        if request.cookies.get('ID'):
            return render_template('creation_ticket.html')
        else :
            flash("vous devé vous créer un conte dabor", "warning")
            return render_template('creation_ticket.html')

if __name__ == '__main__':
    app.run(debug=True)
