
import datetime
import csv
import pandas
import os

from currency_converter import CurrencyConverter

import gesamtRendite
import titelRendite
import config
import scrapeSwissquoteOverview
import initDb
import sqlite3

transaktionen = {}


config.currencyConverter = CurrencyConverter('http://www.ecb.int/stats/eurofxref/eurofxref-hist.zip', fallback_on_missing_rate=True, fallback_on_wrong_date=True)

def toYMD(stringDate):
    day = stringDate[0:2]
    month = stringDate[3:5]
    year = stringDate[6:10]
    return datetime.date(int(year),int(month),int(day))


def gewinn(verkauf, kaeufe):
    totalAnzahlVerkauft = verkauf.anzahl
    totalGewinn = 0
    for kauf in kaeufe:
        if totalAnzahlVerkauft > kauf.anzahl:
            anzahlVerkauft = kauf.stueckzahl
            totalAnzahlVerkauft -= kauf.stueckzahl
            totalGewinn += anzahlVerkauft * (verkauf.stueckpreis - kauf.stueckpreis)
    return totalGewinn


def kosten(transaktionsKosten):
    totalKosten = 0
    for kost in transaktionsKosten:
        totalKosten += kost
    return totalKosten

def strToFloat(inStr:str) -> float:
    if "%" in inStr:
        return float(inStr.replace("%", "").replace("'","")) * 100
    else:
        return float(inStr.replace("'",""))

def korrName(name):
    out = name
    if name == '':
        out = 'Carmignac Investissement A EUR acc'
    if name == 'CSF (Lux) Commodity Index Plus (Sfr) B':
        out='CSF Lux Commodity Index Plus Sfr B'
    if name == 'rA Global Microfinance B':
        out = 'RESPONSABILITY GLOBAL MICROFINANCE FUND B'

    return out


def konvertiereTransaktionsDatum(stagingDb):
    cmd = "UPDATE raw SET Datum = substr(Datum,7,4)||'-'||substr(Datum,4,2)||'-'||substr(Datum,0,3)"
    stagingDb.execute(cmd)
    stagingDb.commit()

def spezielleISIN(stagingDb):

    # lösche einige ISIN
    cmd = "DELETE FROM raw WHERE ISIN IN ('GB00BMF7GD44','CH0465781083')"
    stagingDb.execute(cmd)

    # Spezialfall ZGLD
    cmd = "UPDATE raw SET ISIN='CH0139101593' WHERE ISIN='CH0024391002' AND Transaktionen = 'Kauf'"
    stagingDb.execute(cmd)

    # Spezialfall ZUEBLIN
    # if transaktionen[i]['ISIN'] == 'CH0021831182':
    #    transaktionen[i]['ISIN'] = 'CH0312309682'
    #    transaktionen[i]['Name'] = 'ZUEBLIN IMM N'
    cmd = "UPDATE raw SET ISIN='CH0312309682', Name = 'ZUEBLIN IMM N' WHERE ISIN='CH0021831182'"
    stagingDb.execute(cmd)

    # if transaktionen[i]['ISIN'] == 'CH0312309682' and transaktionen[i]['Transaktionen'] == "Verkauf":
    #    transaktionen[i]['Anzahl'] = '2500'
    #    transaktionen[i]['Stückpreis'] = '0.01'
    cmd = "UPDATE raw SET Anzahl=2500, Stückpreis = 0.01 WHERE ISIN='CH0312309682' AND Transaktionen = 'Verkauf'"
    stagingDb.execute(cmd)

    # Spezialfall SYNN -> SYNNE
    # if transaktionen[i]['ISIN'] == 'CH0011037469':
    #    transaktionen[i]['ISIN'] = 'CH0316124541'
    #    transaktionen[i]['Name'] = 'SYNGENTA N  2. Linie'
    #    transaktionen[i]['Symbol'] = 'SYNNE'
    cmd = "UPDATE raw SET " \
          "ISIN = 'CH0316124541', " \
          "Name = 'SYNGENTA N  2. Linie', " \
          "Symbol = 'SYNNE' " \
          "WHERE ISIN = 'CH0011037469'"
    stagingDb.execute(cmd)

    cmd = "UPDATE raw SET " \
            "Anzahl = 12, " \
            "Transaktionen = 'Verkauf' " \
          "WHERE ISIN = 'CH0011037469' " \
            "AND Transaktionen = 'Rückzahlung' " \
            "AND Anzahl = -12 "
    stagingDb.execute(cmd)
    stagingDb.commit()

def einheitlicheNamen(stagingDb):
    cmd = "UPDATE raw SET Name='Carmignac Investissement A EUR acc' WHERE Name='Carmignac Investissement A'"
    stagingDb.execute(cmd)

    cmd = "UPDATE raw SET Name='CSF Lux Commodity Index Plus Sfr B' WHERE Name='CSF (Lux) Commodity Index Plus (Sfr) B'"
    stagingDb.execute(cmd)

    cmd = "UPDATE raw SET Name='RESPONSABILITY GLOBAL MICROFINANCE FUND B' WHERE Name='rA Global Microfinance B'"
    stagingDb.execute(cmd)
    stagingDb.commit()

def berechneRelativeTage(stagingDb, basisDatum):
    basisDatumStr = str(basisDatum)
    stagingDb.commit()
    cmd = "UPDATE raw SET tage = julianday(Datum) - julianday('"+basisDatumStr+"')"
    stagingDb.execute(cmd)
    stagingDb.commit()


def setzeBetragUmrechnungNachChf(stagingDb):
    '''
    benutze wenn vorhanden die eigene historische tabelle
    ist kein eintrag vorhanden, frage den historischen kurs ab und ergänze ihn in die eigene historische tabelle
    :param stagingDb:
    :return:
    '''
    # transaktionen in CHF bekommen eine 1
    x = 1
    rate1 = "UPDATE raw " \
          "SET rateToChf = 1 " \
          "WHERE Währung = 'CHF' or Währung IS NULL"
    stagingDb.execute(rate1)
    stagingDb.commit()

    # bekannte umrechnungsfaktoren
    updRate = "UPDATE raw " \
          "SET rateToChf = " \
          " (SELECT rateToChf " \
          "  from exchangeRateHistory h " \
          "  WHERE Währung = h.waehrung " \
          "  AND " \
          "  Währung != 'CHF'" \
          "  AND " \
          "  DATE(Datum) = DATE(h.Datum))" \
          "  WHERE rateToChf IS NULL"
    stagingDb.execute(updRate)
    stagingDb.commit()

    # für alle nicht getroffenen transaktionen:
    # frage den historischen Kurs ab
    # ergänze den eintrag in die historische Kurs-Tabelle
    # führe die Transaktion nach
    cursor = stagingDb.cursor()
    unsetRate = "SELECT * FROM raw WHERE rateToChf IS NULL"
    cursor.execute(unsetRate)

    rows = cursor.fetchall()

    for row in rows:
        datum = datetime.datetime.strptime(row[0],"%Y-%m-%d")
        print(f"{row[14]=}")
        rateToChf = config.currencyConverter.convert(1, row[14], 'CHF', date=datum)
        data = (row[0], row[14], rateToChf)
        cmd = f"INSERT INTO exchangeRateHistory (datum, waehrung, rateToChf) VALUES(?,?,?)"
        stagingDb.execute(cmd, data)
    stagingDb.commit()

    # update raw data table with evaluated exchange rate again
    stagingDb.execute(updRate)
    stagingDb.commit()


def korrigiereNettobetrag(stagingDb):
    cmd = "UPDATE raw SET Nettobetrag=0 WHERE Nettobetrag='-'"
    stagingDb.execute(cmd)
    stagingDb.commit()


def setzeStueckkosten(stagingDb):
    cmd = "UPDATE raw SET stueckkosten=Kosten/Anzahl"
    stagingDb.execute(cmd)
    stagingDb.commit()


if __name__ == '__main__':

    config.berechnungsDatum = datetime.date(2020,12,31)
    transaktionen = {}


    initDb.dropCreateTables()

    #stagingDb = sqlite3.connect(':memory:')
    stagingDb = sqlite3.connect('staging.db')
    csvFile = 'transactions-2000-to-01012021.csv'
    #df = pandas.read_csv(csvFile, encoding='cp1252')
    csv.register_dialect('swissquote', delimiter=";")
    df = pandas.read_csv(csvFile, encoding='cp1252', thousands="'", dialect='swissquote')
    df.to_sql('raw', stagingDb, if_exists='append', index=False)

    additionalColumns = [['tage', 'INTEGER'], ['rateToChf', 'REAL'], ['kurs', 'REAL'], ['stueckkosten', 'REAL']]
    for col in additionalColumns:
        alterTable = f"ALTER TABLE raw ADD COLUMN {col[0]} {col[1]}"
        stagingDb.execute(alterTable)

    konvertiereTransaktionsDatum(stagingDb)
    spezielleISIN(stagingDb)
    einheitlicheNamen(stagingDb)
    berechneRelativeTage(stagingDb, config.basisDatum)
    setzeBetragUmrechnungNachChf(stagingDb)
    korrigiereNettobetrag(stagingDb)
    setzeStueckkosten(stagingDb)

    scrapeSwissquoteOverview.scrapeSwissquoteTradingPageWithPandas(transaktionen)

    gesamtRendite.gesamtRendite(transaktionen)

    titelRendite.titelRenditen(transaktionen)


    #renditenIsin()

