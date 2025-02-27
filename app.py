from flask import Flask, render_template, request, redirect, url_for, flash
import sys
import os
from alive_progress import alive_bar
import time
from flask_socketio import SocketIO
from db import adduser, who, verify_password, tiqué_type, ader_type
from tique import create_tiqué, list_tiqué, get_info_tiqué, get_info_tiqué_comment, now_comment, close_tiqué

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)

with alive_bar(0) as bar:
    @app.route('/', methods=['GET', 'POST'])
    def index():
        result = None
        if request.method == 'POST':
            input_value = request.form['input_value']
            result = list_tiqué(input_value)
        else:
            results = []
            result = list_tiqué()
            for i in result:
                a = list(i)
                a[1] = str(who(i[1]))
                a = tuple(a)
                results.append(a)
            return render_template('index.html', result=results)

    @app.route('/connexion', methods=['GET', 'POST'])
    def connexion_route():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            try:
                ID = verify_password(password, email)
                response = app.make_response(redirect(url_for('connexion_route')))
                response.set_cookie('ID', str(ID))
                flash("Utilisateur connecté avec succès!", "success")
                return response
            except Exception as e:
                flash(str(e), "error")
        return render_template('connexion.html')

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
                response = app.make_response(redirect(url_for('index')))
                response.set_cookie('ID', ID)
                return response
            except ValueError as e:
                flash(str(e), "error")
        return render_template('creation_conte.html')

    @app.route('/new-ticket', methods=['POST'])
    def add_ticket_route():
        if request.method == 'POST':
            IDs = request.cookies.get('ID')
            titre = request.form['titre']
            description = request.form['description']
            gravité = request.form['gravité']
            tags = request.form['tags']
            try:
                create_tiqué(IDs, titre, description, gravité, tags)
                flash("Le ticket a été ajouté avec succès!", "success")
                response = app.make_response(redirect(url_for('add_ticket_route')))
                return response
            except ValueError as e:
                flash(str(e), "error")
        return response

    @app.route('/ticket', methods=['GET', 'POST'])
    @app.route('/ticket/<id_tique>', methods=['GET', 'POST'])
    def ticket_route(id_tique=None):
        if request.method == 'POST':
            if id_tique:
                ID_user = request.cookies.get('ID')
                commenter = request.form['commenter']
                now_comment(id_tique, ID_user, commenter)
                flash("Commentaire ajouté avec succès!", "success")
            else:
                id_tiqué = request.form.get('ticket_id')
                id_user = request.cookies.get('ID')
                tickete = get_info_tiqué(id_tiqué)
                if not tickete:
                    flash("Ticket non trouvé.", "error")
                    return redirect(url_for('index'))
                if request.form['action'] == 'dilet':
                    try:
                        close_tiqué(id_tiqué, id_user)
                    except LookupError:
                        flash("Devez d'abord interagir avec le ticket avant de le fermer (Mettre un commentaire)", "warning")
                    except ValueError:
                        flash("Le ticket doit être fermé par le Créateur. Vous devez le contacter pour fermer le ticket", "info")

        elif request.method == 'GET' and id_tique:
            id_user = request.cookies.get('ID')
            if id_user is not None:
                tickete = get_info_tiqué(id_tique)
                comm = get_info_tiqué_comment(id_tique)
                results_comm = []
                for i in comm:
                    a = list(i)
                    a[0] = str(who(i[0]))
                    a = tuple(a)
                    results_comm.append(a)
                return render_template('ticket.html', ticket=tickete, comments=results_comm)
            else:
                flash("Aucun compte connecté", "warning")
                return redirect(url_for('index'))

        return redirect(url_for('index'))

    def all_tiqué(tiqué_type_var="all"):
        results = []
        result = list_tiqué(tiqué_type_var)
        for i in result:
            a = list(i)
            a[1] = str(who(i[1]))
            a = tuple(a)
            results.append(a)
        return results

    @app.route('/allticket', methods=['GET', 'POST'])
    def create_allticket_route(tiqué_type_var="all"):
        retone = 0
        if request.method == 'POST':
            IDs = request.cookies.get('ID')
            titre = request.form['titre']
            description = request.form['description']
            gravité = request.form['gravité']
            tags = request.form['tags']
            if request.cookies.get('ID'):
                try:
                    create_tiqué(IDs, titre, description, gravité, tags)
                    flash("Le ticket a été ajouté avec succès!", "success")
                    time.sleep(0.5)
                    page = all_tiqué(tiqué_type_var)
                except ValueError as e:
                    flash(str(e), "error")
                    page = all_tiqué(tiqué_type_var)
            else:
                flash("Avant de commencer, il est nécessaire de créer un compte.", "error")
                page = []
        if request.method == 'GET':
            if request.cookies.get('ID'):
                page = all_tiqué(tiqué_type_var)
            else:
                flash("Avant de commencer, il est nécessaire de créer un compte.", "warning")
                retone = 1
                page = []

        if retone == 1:
            return redirect(url_for('index'))
        else:
            resultsoftcorige = []
            resultardercorige = []
            resultsoft = tiqué_type()

            for i in resultsoft:
                a = list(i)
                a[0] = str(a[0]).replace(" ", "_")
                a = tuple(a)
                resultsoftcorige.append(a[0])

            resultarder = ader_type()
            for i in resultsoft:
                a = list(i)
                a[0] = str(a[0]).replace(" ", "_")
                a = tuple(a)
                resultardercorige.append(a[0])
        return render_template('Softwer.html', soft=resultsoft, ard=resultarder, page=page, ou=tiqué_type_var)

    with app.app_context():
        for i in tiqué_type():
            a = list(i)
            a[0] = str(a[0]).replace(" ", "_")
            a[0] = str(a[0]).lower()
            a = tuple(a)
            route_name = f'/software/{a[0]}'
            endpoint_name = f'software_{a[0]}'
            app.route(route_name, methods=['GET', 'POST'], endpoint=endpoint_name)(lambda tiqué_type_var=a[0]: create_allticket_route(tiqué_type_var))

        for i in ader_type():
            a = list(i)
            a[0] = str(a[0]).replace(" ", "_")
            a[0] = str(a[0]).lower()
            a = tuple(a)
            route_name = f'/hardware/{a[0]}'
            endpoint_name = f'hardware_{a[0]}'
            app.route(route_name, methods=['GET', 'POST'], endpoint=endpoint_name)(lambda tiqué_type_var=a[0]: create_allticket_route(tiqué_type_var))

    def list_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            if "GET" in rule.methods and rule.endpoint != 'static':
                url = url_for(rule.endpoint, **(rule.defaults or {}))
                routes.append((url, rule.endpoint))
        return routes

    @app.route('/site-map')
    def site_map():
        routes = list_routes()
        for route in routes:
            print(route)
        return {'routes': routes}

    @app.route('/materiel', methods=['GET', 'POST'])
    def materil():
        tiqué_types = tiqué_type()
        ader_types = ader_type()
        materiels = tiqué_types + ader_types
        return render_template('materiel.html', materiels=materiels)

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)
