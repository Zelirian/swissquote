
import config
import sqlite3
from flask import Flask, render_template
from werkzeug.exceptions import abort
import config

def get_trans(assetId):
    conn = config.get_db_connection()
    trans = conn.execute('SELECT * FROM asset WHERE id = ?', assetId).fetchone()
    conn.close()
    if trans is None:
        abort(404)
    return trans

app = Flask(__name__)

'''
@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()
    return render_template('index.html', posts=posts)
'''
@app.route('/')
def index():
    conn = config.get_db_connection()
    assets = conn.execute('SELECT * FROM assets').fetchall()
    conn.close()
    return render_template('index.html', assets=assets)

@app.route('/<int:assetId>')
def post(assetId):
    trans = get_trans(assetId)
    return render_template('trans.html', post=trans)