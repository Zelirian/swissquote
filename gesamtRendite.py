
'''
hier werden nur die einzahlungen, wertpapier-zugänge, auszahlungen und aktueller portfolio-wert ausgewertet
'''

import datetime

Stichtag = {'datum': datetime.datetime(2020, 12, 31), 'wert': 255576.41}

def gesamtRendite(transaktionen):

    Einzahlungen = [transaktionen[x] for x in transaktionen if transaktionen[x]['Transaktionen'] in ('Einzahlung','Vergütung')]
    Auszahlungen = [transaktionen[x] for x in transaktionen if transaktionen[x]['Transaktionen'] in ('Auszahlung')]

    zinstage = 0
    totalEinzahlungen = 0
    totalAuszahlungen = 0

    for trans in Einzahlungen:
        dateFromString = datetime.datetime.strptime(trans['Datum'], '%d-%m-%Y %H:%M:%S')
        transDatum = datetime.date(dateFromString.year, dateFromString.month, dateFromString.day)
        tage = (Stichtag['datum'].date() - transDatum).days
        #betragCHF = trans['Anzahl'] * trans['Stückpreis'] * trans['rate']
        betragCHF = trans['Nettobetrag'] * trans['rate']
        totalEinzahlungen += betragCHF
        zinstage += tage * betragCHF

    for trans in Auszahlungen:
        dateFromString = datetime.datetime.strptime(trans['Datum'], '%d-%m-%Y %H:%M:%S')
        transDatum = datetime.date(dateFromString.year, dateFromString.month, dateFromString.day)
        tage = (Stichtag['datum'].date() - transDatum).days
        #betragCHF = trans['Anzahl'] * trans['Stückpreis'] * trans['rate']
        betragCHF = trans['Nettobetrag'] * trans['rate']
        totalAuszahlungen -= betragCHF
        zinstage -= tage * betragCHF

    gewinn = Stichtag['wert'] - totalEinzahlungen + totalAuszahlungen

    renditePa = gewinn / zinstage * 36500

    print(f"{Stichtag['datum']=}")
    print(f"{totalEinzahlungen=}")
    print(f"{totalAuszahlungen=}")
    print(f"{Stichtag['wert']=}")
    print(f"{gewinn=:.0f}")
    print(f"{renditePa=:.2f}%")
