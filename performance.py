
import datetime
import csv
from currency_converter import CurrencyConverter

import gesamtRendite
import titelRendite
import config
import scrapeSwissquoteOverview

csv.register_dialect('swissquote', delimiter=";")

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
    if name == 'Carmignac Investissement A':
        out = 'Carmignac Investissement A EUR acc'
    if name == 'CSF (Lux) Commodity Index Plus (Sfr) B':
        out='CSF Lux Commodity Index Plus Sfr B'
    if name == 'rA Global Microfinance B':
        out = 'RESPONSABILITY GLOBAL MICROFINANCE FUND B'
    return out


if __name__ == '__main__':

    config.berechnungsDatum = datetime.date(2020,12,31)
    transaktionen = {}

    with open('transactions-2000-to-01012021.csv') as transactionFile:
        reader = csv.reader(transactionFile, dialect='swissquote')
        fields = next(reader)
        fields = [s.replace(" #", "") for s in fields]
        fields = [s.replace(" ", "") for s in fields]

        fields.append("tage")
        fields.append("rate")
        fields.append("kurs")
        fields.append("stueckkosten")

        baseDatum = datetime.date(2000, 1, 1)

        for i, values in enumerate(reader):

            transaktionen[i] = dict(zip(fields, values))

            # ändere die isin nummer zu symbolen, welche unterschiedliche isin haben

            # Spezialfall SYNN -> SYNNE
            if transaktionen[i]['ISIN'] == 'CH0011037469': transaktionen[i]['ISIN'] = 'CH0316124541'  # SYNN zu SYNNE

            # Spezialfall ZGLD
            if transaktionen[i]['ISIN'] == 'CH0024391002' and transaktionen[i]['Transaktionen'] == "Kauf": transaktionen[i]['ISIN'] = 'CH0139101593'

            transaktionen[i]['Name'] = korrName(transaktionen[i]['Name'])

            curr = transaktionen[i]['WährungNettobetrag']
            transaktionen[i]['rate'] = 1
            dateFromString = datetime.datetime.strptime(transaktionen[i]['Datum'], '%d-%m-%Y %H:%M:%S')
            dtDatum = datetime.date(dateFromString.year, dateFromString.month, dateFromString.day)
            transaktionen[i]['datum'] = dtDatum

            transaktionen[i]['tage'] = (dtDatum - baseDatum).days

            # string to float, tausender trennzeichen entfernen
            transaktionen[i]['Anzahl'] = strToFloat(transaktionen[i]['Anzahl'])
            transaktionen[i]['Stückpreis'] = strToFloat(transaktionen[i]['Stückpreis'])
            if transaktionen[i]['Nettobetrag'] == "-":
                transaktionen[i]['Nettobetrag'] = 0
            else:
                transaktionen[i]['Nettobetrag'] = strToFloat(transaktionen[i]['Nettobetrag'])

            #transaktionen[i]['Saldo'] = float(transaktionen[i]['Saldo'].replace("'", ""))
            transaktionen[i]['Kosten'] = strToFloat(transaktionen[i]['Kosten'])
            #transaktionen[i]['stueckkosten'] = transaktionen[i]['Kosten'] / transaktionen[i]['Anzahl']
            if transaktionen[i]['Name'] == 'BABA-SW ORD':
                print('baba')
            if len(curr) > 0:
                rateToChf = config.currencyConverter.convert(1, curr, 'CHF', date=dtDatum)
                transaktionen[i]['rate'] = rateToChf

        scrapeSwissquoteOverview.scrapeSwissquoteTradingPageWithPandas(transaktionen)

        gesamtRendite.gesamtRendite(transaktionen)

        titelRendite.titelRenditen(transaktionen)


        #renditenIsin()

