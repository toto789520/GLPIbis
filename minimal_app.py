from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Identifiants requis")
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
