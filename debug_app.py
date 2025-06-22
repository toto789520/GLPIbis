from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# Configuration de débogage
app.config['DEBUG'] = True

# Vérification des chemins
print(f"Dossier de l'application: {app.root_path}")
print(f"Dossier templates: {app.template_folder}")
print(f"Dossier static: {app.static_folder}")

# Vérifier si les dossiers existent
templates_path = os.path.join(app.root_path, 'templates')
static_path = os.path.join(app.root_path, 'static')

print(f"Templates existe: {os.path.exists(templates_path)}")
print(f"Static existe: {os.path.exists(static_path)}")

if os.path.exists(templates_path):
    print(f"Fichiers dans templates: {os.listdir(templates_path)}")

@app.route('/')
def index():
    return "<h1>Test Flask - Fonctionnel</h1>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    print("=== DEBUT ROUTE LOGIN ===")
    try:
        if request.method == 'POST':
            print("Méthode POST détectée")
            username = request.form.get('username')
            password = request.form.get('password')
            print(f"Username: {username}, Password: {'*' * len(password) if password else 'None'}")
            
            # Rediriger vers le dashboard
            return redirect(url_for('dashboard'))
        
        print("Tentative de rendu du template...")
        result = render_template('login.html')
        print("Template rendu avec succès")
        return result
    except Exception as e:
        print(f"ERREUR lors du rendu: {e}")
        return f"<h1>Erreur Template</h1><p>{str(e)}</p>"

@app.route('/dashboard')
def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Dashboard</title></head>
    <body>
        <h1>Dashboard de test</h1>
        <p>Connexion réussie !</p>
        <a href="/login">Retour au login</a>
    </body>
    </html>
    """

@app.route('/test')
def test():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Direct</title></head>
    <body>
        <h1>Page de test direct</h1>
        <p>Si vous voyez ceci, Flask fonctionne.</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True, port=5000)
