
import datetime
import sqlite3
import os

letzterPreis = {}
totalBar = 0
berechnungsDatum = None

currencyConverter = None

transId = 0

basisDatum = datetime.date(2000,1,1)


