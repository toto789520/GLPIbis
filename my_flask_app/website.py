from flask import Flask, render_template, request, redirect, url_for, flash
# Assuming that the db directory has an __init__.py file
import sys
import os

# Obtenir le chemin du dossier racine
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Ajouter le dossier racine au chemin de recherche des modules
sys.path.append(project_root)

# Maintenant, vous pouvez importer le module `coucou`
from db import adduser, who, verify_password
from tique import create_tiqué, list_tiqué, get_info_tiqué, get_info_tiqué_comment, now_comment, close_tiqué


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flash messages to work

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        input_value = request.form['input_value']
        result = list_tiqué(input_value)  # Assuming list_tiqué can take a filter parameter
    else:
        results = []
        result = list_tiqué()  # Assuming this function returns a list of tuples

        for i in result:
            # Convert the tuple to a list to modify it
            a = list(i)
            
            # Modify the element
            a[1] = str(who(i[1]))
            
            # If you need to maintain it as a tuple, convert it back
            a = tuple(a)
            
            # Append to the results
            results.append(a)

        # Render the template with the modified results
        return render_template('index.html', result=results)
@app.route('/connet_user', methods=['GET', 'POST'])
def connet_user_route():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            ID = verify_password(password, email)
            flash("Utilisateur connet avec succès!", "success")
            response = app.make_response(redirect(url_for('connet_user_route')))
            response.set_cookie('ID', ID)  # Set the new cookie
            return response
        except ValueError as e:
            flash(str(e), "error")
    return render_template('connet_conte.html')

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

@app.route('/new-ticket', methods=['GET', 'POST'])
def add_ticket_route():
    if request.method == 'POST':
        IDs = request.cookies.get('ID')
        titre = request.form['titre']
        description = request.form['description']
        gravité = request.form['gravité']
        tags = request.form['tags']
        try:
            create_tiqué(IDs,titre,description,gravité,tags)
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
    response = app.make_response(redirect(url_for('add_ticket_route')))
    return response
@app.route('/ticket', methods=['POST'])
def web_ticket_route():
    if request.method == 'POST':
        id_tiqué =  request.form['ticket_id']
        id_user = request.cookies.get('ID')
        print(id_tiqué)
        tickete = get_info_tiqué(id_tiqué)
        results_tickete = []
        results_comm = []
        if request.form['action'] == 'dilet':
            try:
                close_tiqué(id_tiqué, id_user)
            except LookupError:
                flash("Devez d'abord interagir avec le ticket avant de le fermer (Mettre un commentaire)", "warning")
            except ValueError:
                flash("Le ticket doit être fermé par le Créateur Vous devez le contacter pour fermer le ticket", "info")
        for i in tickete:
            # Convert the tuple to a list to modify it
            a = list(i)
            
            # Modify the element
            a[1] = str(who(i[1]))
            
            # If you need to maintain it as a tuple, convert it back
            a = tuple(a)
            
            # Append to the results
            results_tickete.append(a)


        if request.cookies.get('ID') != None:
            try:
                commter = request.form['commer']
                print(commter)
                now_comment(id_tiqué,id_user,commter)
            except:
                print("no-comm")
        else:
            flash("Aucun compte connecté", "warning")
            print("no-id")
            print(request.cookies.get('ID'))

        comm=get_info_tiqué_comment(id_tiqué)
        for i in comm:
            # Convert the tuple to a list to modify it
            a = list(i)
            
            # Modify the element
            a[0] = str(who(i[0]))
            
            # If you need to maintain it as a tuple, convert it back
            a = tuple(a)
            
            # Append to the results
            results_comm.append(a)

    return render_template('ticket.html', result=results_tickete, comm=results_comm)


if __name__ == '__main__':
    app.run(debug=True)
