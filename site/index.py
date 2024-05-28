from flask import Flask, render_template
from db import adduser

app = Flask(__name__)

@app.route('/')
def home():
    data = adduser()
    return render_template('home.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)