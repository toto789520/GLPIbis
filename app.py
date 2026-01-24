from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from sqlalchemy import text
import os

load_dotenv()

app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('db_url')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set. Please configure a strong, random secret key.")
app.config['SECRET_KEY'] = secret_key  # Important pour les sessions

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirige vers login si non authentifié
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

def test_connect_to_database():
    try:
        with app.app_context():
            with db.engine.connect() as connection:
                version = connection.execute(text("SELECT VERSION()")).fetchone()[0]
                print(f"Connexion OK ! Version MySQL : {version}")
        return True
    except Exception as e:
        print(f"Erreur DB : {e}")
        return False
    

# class User
class User(UserMixin, db.Model):
    __tablename__ = 'app_user'
    
    id = db.Column(db.Integer, primary_key=True)
    id_group = db.Column(db.Integer)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mdp_encrypted = db.Column(db.String(255), nullable=False)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.mdp_encrypted = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.mdp_encrypted, password)
    
# class Ticket
class Ticket(db.Model):
    __tablename__ = 'ticket'
    __table_args__ = {'comment': 'table pour les ticket'}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='id du ticket')
    id_user_creator = db.Column(db.Integer, db.ForeignKey('app_user.id', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=False, comment='creator ID')
    id_hardware = db.Column(db.Integer, comment='id du matériel concerné')
    name_ticket = db.Column(db.Text, nullable=False, comment='nom')
    def_ticket = db.Column(db.Text, comment='description du ticket')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), comment='date de création')
    status = db.Column(db.Integer, comment='statut du ticket')
    updated_at = db.Column(db.Date, comment='date de mise à jour')
    
    # Relation avec User
    user_creator = db.relationship('User', backref='tickets')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template('home.html')

#user :
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Validations
        if not name or not email or not password:
            flash('Tous les champs sont obligatoires.', 'danger')
            return render_template('register.html')
        
        if password != password_confirm:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'danger')
            return render_template('register.html')
        
        # Créer le nouvel utilisateur
        new_user = User(
            name=name,
            email=email,
            id_group=1  # Valeur par défaut, à adapter selon vos besoins
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            
            # Mettre à jour last_login
            from datetime import datetime
            user.last_login = datetime.now()
            db.session.commit()
            
            flash(f'Bienvenue {user.name} !', 'success')
            
            # Rediriger vers la page demandée ou profile
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('profile'))
        else:
            flash('Email ou mot de passe incorrect.', 'danger')
    
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('home'))

@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html', user=current_user)

#ticket 
@app.route("/tickets")
@login_required
def tickets():
    tickets = Ticket.query.all()
    return render_template('tickets-list.html', tickets=tickets)

@app.route("/tickets/create", methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        name_ticket = request.form.get('name_ticket')
        def_ticket = request.form.get('def_ticket')
        
        if not name_ticket:
            flash('Le nom du ticket est obligatoire.', 'danger')
            return render_template('create_ticket.html')
        
        new_ticket = Ticket(
            id_user_creator=current_user.id,
            name_ticket=name_ticket,
            def_ticket=def_ticket,
            status=0  # Statut par défaut, à adapter selon vos besoins
        )
        
        db.session.add(new_ticket)
        db.session.commit()
        
        flash('Ticket créé avec succès !', 'success')
        return redirect(url_for('tickets'))
    
    return render_template('create_ticket.html')

@app.route("/tickets/<int:id_tickets>")
@login_required
def view_ticket(id_tickets):
    ticket = Ticket.query.filter_by(id=id_tickets).first()
    if ticket:
        return render_template('tickets.html', ticket=ticket)
    else:
        return render_template('erreur.html', erreur='Ticket non trouvé'), 404

@app.route("/tickets/<int:id_tickets>/update/status", methods=['POST'])
@login_required
def update_ticket_status(id_tickets):
    ticket = Ticket.query.filter_by(id=id_tickets).first()
    if not ticket:
        return render_template('erreur.html', erreur='Ticket non trouvé'), 404
    
    new_status = request.form.get('status')
    if new_status is not None:
        try:
            ticket.status = int(new_status)
            db.session.commit()
            flash('Statut du ticket mis à jour avec succès !', 'success')
        except ValueError:
            flash('Statut invalide.', 'danger')
    else:
        flash('Aucun statut fourni.', 'danger')
    
    return redirect(url_for('view_ticket', id_tickets=id_tickets))

@app.route("/tickets/<int:id_tickets>/update/edit", methods=['POST', 'GET'])
@login_required
def edit_ticket(id_tickets):
    if request.method == 'GET':
        ticket = Ticket.query.filter_by(id=id_tickets).first()
        if not ticket:
            return render_template('erreur.html', erreur='Ticket non trouvé'), 404
        return render_template('edit_ticket.html', ticket=ticket)
    else:
        ticket = Ticket.query.filter_by(id=id_tickets).first()
        if not ticket:
            return render_template('erreur.html', erreur='Ticket non trouvé'), 404
        
        name_ticket = request.form.get('name_ticket')
        def_ticket = request.form.get('def_ticket')

        if not name_ticket:
            flash('Le nom du ticket est obligatoire.', 'danger')
            return redirect(url_for('view_ticket', id_tickets=id_tickets))
        
        ticket.name_ticket = name_ticket
        ticket.def_ticket = def_ticket
        db.session.commit()
        
        flash('Ticket mis à jour avec succès !', 'success')
        return redirect(url_for('view_ticket', id_tickets=id_tickets))

@app.route("/tickets/<int:id_tickets>/update/delete", methods=['POST'])
@login_required
def delete_ticket(id_tickets):
    ticket = Ticket.query.filter_by(id=id_tickets).first()
    if not ticket:
        return render_template('erreur.html', erreur='Ticket non trouvé'), 404
    
    db.session.delete(ticket)
    db.session.commit()
    
    flash('Ticket supprimé avec succès !', 'success')
    return redirect(url_for('tickets'))

# page d'erreur

@app.errorhandler(404)
def page_not_found(e):
    return render_template('erreur.html', erreur='Page non trouvée'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('erreur.html', erreur='Erreur serveur'), 500

if __name__ == "__main__":
    #with app.app_context():
        #db.create_all()  # Crée les tables si elles n'existent pas
    app.run(debug=True, host="0.0.0.0", port=5000)