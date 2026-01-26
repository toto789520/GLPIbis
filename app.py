from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.dialects.mysql import LONGTEXT
from functools import wraps
import os
import uuid
from datetime import datetime

load_dotenv()

app = Flask(__name__)
csrf = CSRFProtect(app)

# Configuration de la base de données
db_url = os.getenv('db_url') or os.getenv('DATABASE_URL')
if not db_url:
    raise RuntimeError(
        "DATABASE_URL or db_url environment variable is not set. "
        "Please configure your database connection string."
    )
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set. Please configure a strong, random secret key.")
app.config['SECRET_KEY'] = secret_key

# Configuration pour l'upload de fichiers
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'bills')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Créer le dossier uploads s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirige vers login si non authentifié
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

# class Group
class Group(db.Model):
    __tablename__ = 'group'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text)
    permission_level = db.Column(db.Integer, comment='niveaux de permission')
    #0 : utilisateur ban
    #1 : utilisateur vision pas le drois de modifire
    #2 : utilisateur modificateur ticket
    #4 : utilisateur modificateur Hardware + Bill + Brand
    #8 : utilisateur admin peux de ban / modif les perm 
    #les permision asdison exsanple 1 + 4 = 5 sais la permision la plus grande qui ranprtre dans exsanple il a droit de modif le Hardware mais pas les ticket

    # Relation avec User
    users = db.relationship('User', back_populates='group')

# class Brand
class Brand(db.Model):
    __tablename__ = 'brand'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text)
    tel = db.Column(db.Integer)
    nb_customer = db.Column(db.Integer)
    
    # Relation avec Hardware
    hardwares = db.relationship('Hardware', back_populates='brand')

# class UploadedFile (DÉPLACÉ AVANT Bill)
class UploadedFile(db.Model):
    __tablename__ = 'uploaded_file'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    original_filename = db.Column(db.String(255), nullable=False, comment='nom original du fichier')
    stored_filename = db.Column(db.String(255), nullable=False, unique=True, comment='nom du fichier sur le serveur')
    file_size = db.Column(db.Integer, comment='taille du fichier en octets')
    mime_type = db.Column(db.String(100), comment='type MIME du fichier')
    uploaded_at = db.Column(db.DateTime, default=db.func.now(), comment='date d\'upload')
    id_bill = db.Column(db.Integer, db.ForeignKey('bill.id', ondelete='CASCADE'), nullable=False, comment='facture associée')
    
    # Relation avec Bill
    bill = db.relationship('Bill', back_populates='files')

# class Bill
class Bill(db.Model):
    __tablename__ = 'bill'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text)
    id_brand = db.Column(db.Integer, db.ForeignKey('brand.id', ondelete='NO ACTION', onupdate='NO ACTION'), unique=True)
    
    # Relation avec Hardware et UploadedFile
    hardwares = db.relationship('Hardware', back_populates='bill')
    files = db.relationship('UploadedFile', back_populates='bill', cascade='all, delete-orphan')
    brand = db.relationship('Brand', backref='bill', uselist=False)  # <-- Ajouté

# class Hardware
class Hardware(db.Model):
    __tablename__ = 'hardware'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text)
    def_ = db.Column(LONGTEXT, name='def')
    id_brand = db.Column(db.Integer, db.ForeignKey('brand.id', ondelete='NO ACTION', onupdate='NO ACTION'))
    id_bill = db.Column(db.Integer, db.ForeignKey('bill.id', ondelete='NO ACTION', onupdate='NO ACTION'), comment='facture')
    
    # Relations
    brand = db.relationship('Brand', back_populates='hardwares')
    bill = db.relationship('Bill', back_populates='hardwares')
    tickets = db.relationship('Ticket', back_populates='hardware')

# class User
class User(UserMixin, db.Model):
    __tablename__ = 'app_user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text)
    email = db.Column(db.String(191), unique=True, nullable=False)
    mdp_encrypted = db.Column(db.Text, nullable=False, comment='mot de passe chiffré')
    id_group = db.Column(db.Integer, db.ForeignKey('group.id', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=True, comment='groupe')
    last_login = db.Column(db.DateTime, default=db.func.now(), comment='dernière connexion')
    group = db.relationship('Group', back_populates='users')
    tickets = db.relationship('Ticket', back_populates='user_creator')

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
    name_ticket = db.Column(db.Text, nullable=False, comment='nom')
    def_ticket = db.Column(LONGTEXT, comment='description du ticket')
    id_hardware = db.Column(db.Integer, db.ForeignKey('hardware.id', ondelete='NO ACTION', onupdate='NO ACTION'), comment='id du matérielle conserné')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='date de création')
    status = db.Column(db.Integer)
    updated_at = db.Column(db.Date, comment='date de mise à jour')
    hardware = db.relationship('Hardware', back_populates='tickets')
    user_creator = db.relationship('User', back_populates='tickets', foreign_keys=[id_user_creator])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Système de permissions
def has_permission(permission_bit):
    """
    Vérifie si l'utilisateur a la permission demandée.
    
    permission_bit:
    - 1: Lecture seule (vision)
    - 2: Modification tickets
    - 4: Modification Hardware + Bill + Brand
    - 8: Admin (bannir / modifier permissions)
    """
    if not current_user.is_authenticated:
        return False
    
    if not current_user.group or current_user.group.permission_level == 0:
        return False  # Utilisateur banni ou sans groupe
    
    # Vérifier si l'utilisateur a la permission
    return (current_user.group.permission_level & permission_bit) != 0

def permission_required(permission_bit):
    """
    Décorateur pour vérifier les permissions.
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.group:
                flash('Vous n\'avez pas de groupe assigné. Contactez un administrateur.', 'warning')
                return redirect(url_for('home'))
            
            if current_user.group.permission_level == 0:
                flash('Votre compte est banni.', 'danger')
                logout_user()
                return redirect(url_for('home'))
            
            if not has_permission(permission_bit):
                flash('Vous n\'avez pas la permission d\'accéder à cette page.', 'danger')
                return redirect(url_for('home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Décorateur pour les routes réservées aux administrateurs.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.group or not has_permission(8):
            flash('Cette action est réservée aux administrateurs.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Ajouter has_permission au contexte des templates
@app.context_processor
def utility_processor():
    return dict(has_permission=has_permission)

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
            id_group=None
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
@permission_required(2)
def create_ticket():
    if request.method == 'POST':
        name_ticket = request.form.get('name_ticket')
        def_ticket = request.form.get('def_ticket')
        id_hardware = request.form.get('id_hardware')
        
        if not name_ticket:
            flash('Le nom du ticket est obligatoire.', 'danger')
            hardware_list = Hardware.query.all()
            return render_template('create_ticket.html', hardware_list=hardware_list)
        
        new_ticket = Ticket(
            id_user_creator=current_user.id,
            name_ticket=name_ticket,
            def_ticket=def_ticket,
            id_hardware=id_hardware if id_hardware else None,
            status=0  # Statut par défaut, à adapter selon vos besoins
        )
        
        db.session.add(new_ticket)
        db.session.commit()
        
        flash('Ticket créé avec succès !', 'success')
        return redirect(url_for('tickets'))
    
    hardware_list = Hardware.query.all()
    return render_template('create_ticket.html', hardware_list=hardware_list)

@app.route("/tickets/<int:id_tickets>")
@login_required
def view_ticket(id_tickets):
    ticket = Ticket.query.filter_by(id=id_tickets).first()
    if ticket:
        return render_template('tickets.html', ticket=ticket)
    else:
        return render_template('erreur.html', erreur='Ticket non trouvé'), 404

@app.route("/tickets/<int:id_tickets>/update/status", methods=['POST'])
@permission_required(2)
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
@permission_required(2)
def edit_ticket(id_tickets):
    if request.method == 'GET':
        ticket = Ticket.query.filter_by(id=id_tickets).first()
        if not ticket:
            return render_template('erreur.html', erreur='Ticket non trouvé'), 404
        hardware_list = Hardware.query.all()
        return render_template('edit_ticket.html', ticket=ticket, hardware_list=hardware_list)
    else:
        ticket = Ticket.query.filter_by(id=id_tickets).first()
        if not ticket:
            return render_template('erreur.html', erreur='Ticket non trouvé'), 404
        
        name_ticket = request.form.get('name_ticket')
        def_ticket = request.form.get('def_ticket')
        id_hardware = request.form.get('id_hardware')

        if not name_ticket:
            flash('Le nom du ticket est obligatoire.', 'danger')
            return redirect(url_for('view_ticket', id_tickets=id_tickets))
        
        ticket.name_ticket = name_ticket
        ticket.def_ticket = def_ticket
        ticket.id_hardware = id_hardware if id_hardware else None
        db.session.commit()
        
        flash('Ticket mis à jour avec succès !', 'success')
        return redirect(url_for('view_ticket', id_tickets=id_tickets))

@app.route("/tickets/<int:id_tickets>/update/delete", methods=['POST'])
@permission_required(2)
def delete_ticket(id_tickets):
    ticket = Ticket.query.filter_by(id=id_tickets).first()
    if not ticket:
        return render_template('erreur.html', erreur='Ticket non trouvé'), 404
    
    db.session.delete(ticket)
    db.session.commit()
    
    flash('Ticket supprimé avec succès !', 'success')
    return redirect(url_for('tickets'))


# materiel :

@app.route("/hardware")
@login_required
def hardware():
    hardware_list = Hardware.query.all()
    return render_template('Hardware-list.html', hardware_list=hardware_list)

@app.route("/hardware/create", methods=['GET', 'POST'])
@permission_required(4)
def create_hardware():
    if request.method == 'POST':
        name = request.form.get('name')
        def_ = request.form.get('def_')
        id_brand = request.form.get('id_brand')
        id_bill = request.form.get('id_bill')

        if not name:
            flash('Le nom du matériel est obligatoire.', 'danger')
            return render_template('Hardware.html')

        new_hardware = Hardware(
            name=name,
            def_=def_,
            id_brand=id_brand if id_brand else None,
            id_bill=id_bill if id_bill else None
        )
        db.session.add(new_hardware)
        db.session.commit()
        flash('Matériel créé avec succès !', 'success')
        return redirect(url_for('hardware'))

    brands = Brand.query.all()
    bills = Bill.query.all()
    return render_template('Hardware.html', brands=brands, bills=bills)

@app.route("/hardware/<int:hardware_id>")
@login_required
def view_hardware(hardware_id):
    hardware = Hardware.query.filter_by(id=hardware_id).first()
    if hardware:
        return render_template('Hardware.html', hardware=hardware)
    else:
        return render_template('erreur.html', erreur='Matériel non trouvé'), 404

@app.route("/hardware/<int:hardware_id>/update", methods=['GET', 'POST'])
@permission_required(4)
def edit_hardware(hardware_id):
    hardware = Hardware.query.filter_by(id=hardware_id).first()
    if not hardware:
        return render_template('erreur.html', erreur='Matériel non trouvé'), 404

    if request.method == 'POST':
        name = request.form.get('name')
        def_ = request.form.get('def_')
        id_brand = request.form.get('id_brand')
        id_bill = request.form.get('id_bill')

        if not name:
            flash('Le nom du matériel est obligatoire.', 'danger')
            return redirect(url_for('edit_hardware', hardware_id=hardware_id))

        hardware.name = name
        hardware.def_ = def_
        hardware.id_brand = id_brand if id_brand else None
        hardware.id_bill = id_bill if id_bill else None
        db.session.commit()
        flash('Matériel mis à jour avec succès !', 'success')
        return redirect(url_for('view_hardware', hardware_id=hardware_id))

    brands = Brand.query.all()
    bills = Bill.query.all()
    return render_template('edit_hardware.html', hardware=hardware, brands=brands, bills=bills)

@app.route("/hardware/<int:hardware_id>/delete", methods=['POST'])
@permission_required(4)
def delete_hardware(hardware_id):
    hardware = Hardware.query.filter_by(id=hardware_id).first()
    if not hardware:
        return render_template('erreur.html', erreur='Matériel non trouvé'), 404

    db.session.delete(hardware)
    db.session.commit()
    flash('Matériel supprimé avec succès !', 'success')
    return redirect(url_for('hardware'))


# Brand :

@app.route("/brands")
@login_required
def brands():
    brands_list = Brand.query.all()
    return render_template('brands-list.html', brands=brands_list)

@app.route("/brands/create", methods=['GET', 'POST'])
@permission_required(4)
def create_brand():
    if request.method == 'POST':
        name = request.form.get('name')
        tel = request.form.get('tel')
        nb_customer = request.form.get('nb_customer')

        if not name:
            flash('Le nom de la marque est obligatoire.', 'danger')
            return render_template('create_brand.html')

        new_brand = Brand(
            name=name,
            tel=int(tel) if tel else None,
            nb_customer=int(nb_customer) if nb_customer else None
        )
        db.session.add(new_brand)
        db.session.commit()
        flash('Marque créée avec succès !', 'success')
        return redirect(url_for('brands'))

    return render_template('create_brand.html')

@app.route("/brands/<int:brand_id>")
@login_required
def view_brand(brand_id):
    brand = Brand.query.filter_by(id=brand_id).first()
    if brand:
        return render_template('view_brand.html', brand=brand)
    else:
        return render_template('erreur.html', erreur='Marque non trouvée'), 404

@app.route("/brands/<int:brand_id>/update", methods=['GET', 'POST'])
@permission_required(4)
def edit_brand(brand_id):
    brand = Brand.query.filter_by(id=brand_id).first()
    if not brand:
        return render_template('erreur.html', erreur='Marque non trouvée'), 404

    if request.method == 'POST':
        name = request.form.get('name')
        tel = request.form.get('tel')
        nb_customer = request.form.get('nb_customer')

        if not name:
            flash('Le nom de la marque est obligatoire.', 'danger')
            return redirect(url_for('edit_brand', brand_id=brand_id))

        brand.name = name
        brand.tel = int(tel) if tel else None
        brand.nb_customer = int(nb_customer) if nb_customer else None
        db.session.commit()
        flash('Marque mise à jour avec succès !', 'success')
        return redirect(url_for('view_brand', brand_id=brand_id))

    return render_template('edit_brand.html', brand=brand)

@app.route("/brands/<int:brand_id>/delete", methods=['POST'])
@permission_required(4)
def delete_brand(brand_id):
    brand = Brand.query.filter_by(id=brand_id).first()
    if not brand:
        return render_template('erreur.html', erreur='Marque non trouvée'), 404

    db.session.delete(brand)
    db.session.commit()
    flash('Marque supprimée avec succès !', 'success')
    return redirect(url_for('brands'))


# Bill :

@app.route("/bills")
@login_required
def bills():
    bills_list = Bill.query.all()
    return render_template('bills-list.html', bills=bills_list)

@app.route("/bills/create", methods=['GET', 'POST'])
@permission_required(4)
def create_bill():
    if request.method == 'POST':
        name = request.form.get('name')
        id_brand = request.form.get('id_brand')

        if not name:
            flash('Le nom est obligatoire.', 'danger')
            brands_list = Brand.query.all()
            return render_template('create_bill.html', brands=brands_list)

        new_bill = Bill(
            name=name,
            id_brand=int(id_brand) if id_brand else None
        )
        db.session.add(new_bill)
        db.session.flush()  # Pour obtenir l'ID de la facture

        # Gérer les fichiers uploadés
        files = request.files.getlist('files')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                # Générer un nom unique pour le fichier
                original_filename = secure_filename(file.filename)
                file_extension = original_filename.rsplit('.', 1)[1].lower()
                stored_filename = f"{uuid.uuid4().hex}.{file_extension}"
                
                # Sauvegarder le fichier
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
                file.save(file_path)
                
                # Créer l'entrée dans la base de données
                file_size = os.path.getsize(file_path)
                uploaded_file = UploadedFile(
                    original_filename=original_filename,
                    stored_filename=stored_filename,
                    file_size=file_size,
                    mime_type=file.content_type,
                    id_bill=new_bill.id
                )
                db.session.add(uploaded_file)
            elif file and file.filename:
                flash(f'Le fichier {file.filename} n\'est pas autorisé. Extensions autorisées : {", ".join(ALLOWED_EXTENSIONS)}', 'warning')

        db.session.commit()
        flash('Facture créée avec succès !', 'success')
        return redirect(url_for('bills'))

    brands_list = Brand.query.all()
    return render_template('create_bill.html', brands=brands_list, allowed_extensions=ALLOWED_EXTENSIONS)

@app.route("/bills/<int:bill_id>")
@login_required
def view_bill(bill_id):
    bill = Bill.query.filter_by(id=bill_id).first()
    if bill:
        return render_template('view_bill.html', bill=bill)
    else:
        return render_template('erreur.html', erreur='Facture non trouvée'), 404

@app.route("/bills/<int:bill_id>/update", methods=['GET', 'POST'])
@permission_required(4)
def edit_bill(bill_id):
    bill = Bill.query.filter_by(id=bill_id).first()
    if not bill:
        return render_template('erreur.html', erreur='Facture non trouvée'), 404

    if request.method == 'POST':
        name = request.form.get('name')
        id_brand = request.form.get('id_brand')

        if not name:
            flash('Le nom est obligatoire.', 'danger')
            return redirect(url_for('edit_bill', bill_id=bill_id))

        bill.name = name
        bill.id_brand = int(id_brand) if id_brand else None
        
        # Gérer les nouveaux fichiers uploadés
        files = request.files.getlist('files')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                file_extension = original_filename.rsplit('.', 1)[1].lower()
                stored_filename = f"{uuid.uuid4().hex}.{file_extension}"
                
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
                file.save(file_path)
                
                file_size = os.path.getsize(file_path)
                uploaded_file = UploadedFile(
                    original_filename=original_filename,
                    stored_filename=stored_filename,
                    file_size=file_size,
                    mime_type=file.content_type,
                    id_bill=bill.id
                )
                db.session.add(uploaded_file)
            elif file and file.filename:
                flash(f'Le fichier {file.filename} n\'est pas autorisé.', 'warning')
        
        db.session.commit()
        flash('Facture mise à jour avec succès !', 'success')
        return redirect(url_for('view_bill', bill_id=bill_id))

    brands_list = Brand.query.all()
    return render_template('edit_bill.html', bill=bill, brands=brands_list, allowed_extensions=ALLOWED_EXTENSIONS)

@app.route("/bills/<int:bill_id>/delete", methods=['POST'])
@permission_required(4)
def delete_bill(bill_id):
    bill = Bill.query.filter_by(id=bill_id).first()
    if not bill:
        return render_template('erreur.html', erreur='Facture non trouvée'), 404

    # Supprimer les fichiers physiques
    for uploaded_file in bill.files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.stored_filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(bill)
    db.session.commit()
    flash('Facture supprimée avec succès !', 'success')
    return redirect(url_for('bills'))

@app.route("/bills/files/<int:file_id>/download")
@login_required
def download_bill_file(file_id):
    uploaded_file = UploadedFile.query.filter_by(id=file_id).first()
    if not uploaded_file:
        abort(404)
    
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        uploaded_file.stored_filename,
        as_attachment=True,
        download_name=uploaded_file.original_filename
    )

@app.route("/bills/files/<int:file_id>/delete", methods=['POST'])
@permission_required(4)
def delete_bill_file(file_id):
    uploaded_file = UploadedFile.query.filter_by(id=file_id).first()
    if not uploaded_file:
        abort(404)
    
    bill_id = uploaded_file.id_bill
    
    # Supprimer le fichier physique
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.stored_filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.session.delete(uploaded_file)
    db.session.commit()
    
    flash('Fichier supprimé avec succès !', 'success')
    return redirect(url_for('view_bill', bill_id=bill_id))


# Group :

@app.route("/groups")
@login_required
def groups():
    groups_list = Group.query.all()
    return render_template('groups-list.html', groups=groups_list)

@app.route("/groups/create", methods=['GET', 'POST'])
@admin_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('name')
        permission_level = request.form.get('permission_level')

        if not name:
            flash('Le nom du groupe est obligatoire.', 'danger')
            return render_template('create_group.html')

        new_group = Group(
            name=name,
            permission_level=int(permission_level) if permission_level else 1
        )
        db.session.add(new_group)
        db.session.commit()
        flash('Groupe créé avec succès !', 'success')
        return redirect(url_for('groups'))

    return render_template('create_group.html')

@app.route("/groups/<int:group_id>")
@login_required
def view_group(group_id):
    group = Group.query.filter_by(id=group_id).first()
    if group:
        return render_template('view_group.html', group=group)
    else:
        return render_template('erreur.html', erreur='Groupe non trouvé'), 404

@app.route("/groups/<int:group_id>/update", methods=['GET', 'POST'])
@admin_required
def edit_group(group_id):
    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return render_template('erreur.html', erreur='Groupe non trouvé'), 404

    if request.method == 'POST':
        name = request.form.get('name')
        permission_level = request.form.get('permission_level')

        if not name:
            flash('Le nom du groupe est obligatoire.', 'danger')
            return redirect(url_for('edit_group', group_id=group_id))

        group.name = name
        group.permission_level = int(permission_level) if permission_level else 1
        db.session.commit()
        flash('Groupe mis à jour avec succès !', 'success')
        return redirect(url_for('view_group', group_id=group_id))

    return render_template('edit_group.html', group=group)

@app.route("/groups/<int:group_id>/delete", methods=['POST'])
@admin_required
def delete_group(group_id):
    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return render_template('erreur.html', erreur='Groupe non trouvé'), 404

    db.session.delete(group)
    db.session.commit()
    flash('Groupe supprimé avec succès !', 'success')
    return redirect(url_for('groups'))


# Gestion des utilisateurs (Admin)

@app.route("/users")
@admin_required
def users():
    users_list = User.query.all()
    return render_template('users-list.html', users=users_list)

@app.route("/users/<int:user_id>")
@admin_required
def view_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user:
        return render_template('view_user.html', user=user)
    else:
        return render_template('erreur.html', erreur='Utilisateur non trouvé'), 404

@app.route("/users/<int:user_id>/update", methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return render_template('erreur.html', erreur='Utilisateur non trouvé'), 404

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        id_group = request.form.get('id_group')

        if not name or not email:
            flash('Le nom et l\'email sont obligatoires.', 'danger')
            return redirect(url_for('edit_user', user_id=user_id))

        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user_id:
            flash('Cet email est déjà utilisé.', 'danger')
            return redirect(url_for('edit_user', user_id=user_id))

        user.name = name
        user.email = email
        user.id_group = int(id_group) if id_group else None
        db.session.commit()
        flash('Utilisateur mis à jour avec succès !', 'success')
        return redirect(url_for('view_user', user_id=user_id))

    groups_list = Group.query.all()
    return render_template('edit_user.html', user=user, groups=groups_list)

@app.route("/users/<int:user_id>/delete", methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return render_template('erreur.html', erreur='Utilisateur non trouvé'), 404

    # Empêcher la suppression de son propre compte
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('users'))

    db.session.delete(user)
    db.session.commit()
    flash('Utilisateur supprimé avec succès !', 'success')
    return redirect(url_for('users'))


# page d'erreur

@app.errorhandler(404)
def page_not_found(e):
    return render_template('erreur.html', erreur='Page non trouvée'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('erreur.html', erreur='Erreur serveur'), 500

def create_default_groups():
    """
    Crée les groupes par défaut dans la base de données si aucun groupe n'existe.
    """
    if not Group.query.first():
        default_groups = [
            {"name": "Administrateurs", "permission_level": 15},
            {"name": "Utilisateurs Standard", "permission_level": 7},
            {"name": "Lecture Seule", "permission_level": 1},
            {"name": "Support", "permission_level": 3},
            {"name": "Techniciens", "permission_level": 5},
        ]
        for group in default_groups:
            new_group = Group(name=group["name"], permission_level=group["permission_level"])
            db.session.add(new_group)
        db.session.commit()
        print("Groupes par défaut créés avec succès.")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Crée les tables si elles n'existent pas
        create_default_groups()  # Crée les groupes par défaut
    app.run(debug=True, host="0.0.0.0", port=5000)