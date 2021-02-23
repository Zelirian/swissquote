
import sqlite3

def dropCreateTables():

    db = sqlite3.connect('staging.db')

    with open('schema.sql') as f:
        db.executescript(f.read())

    db.commit()
    db.close()
