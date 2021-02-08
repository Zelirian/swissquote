
import datetime
from collections import namedtuple
import pandas as pd

import config

splitFaktoren = {"ZKB GOLD ETF": {'datum': datetime.date(2011,10,26), 'anzahlFaktor': 10},
                 "Carmignac Investissement A EUR acc": {'datum': datetime.date(2011,11,14), 'anzahlFaktor': 10}}

nameExcludeList = ['CS GROUP ANRECHT ZU AKTIENDIVIDEND 2013-13.5.13',
                   'CS GROUP N ANR',
                   'INA INVEST HLDG SUB RIGHTS FOR SHS 2020-10.06.20',
                   'ITM POWER SUB.SHS',
                   'LAFARGEHOLCIM-ELECTION RIGHT 2019-3 1.05.19',
                   'MAGLTQ LEONGUE C 08/21',
                   'MEYER BURGER ANR',
                   'ORASCOM DEVL - ANRECHT  2015-14.12. 15',
                   'PRECIOUS WOODS HLDG - REG.SHS',
                   'PRECIOUS WOODS N',
                   'PRECIOUS WOODS HLDG ANR. 2013-11.3. 13',
                   'PRECIOUS WOODS HOLDING ANRECHT 20 1 6-28.6.16',
                   'ST.GALLER KB - SUBSCRIPTION RIGHTS 2019-23.05.19',
                   'VON ROLL HLDG - ANRECHT  2016-6.4.1 6',
                   'VON ROLL HLDG - ANRECHT FUER WAND. 2014-11.06.2014',
                   'ZUEBLIN IMM ANR',
                   ]


def normalisiereAnzahlStueckpreis(trans):
    if trans['Transaktionen'] == "Kauf":
        if trans['Name'] in splitFaktoren:
            split = splitFaktoren[trans['Name']]
            if trans['datum'] <= split['datum']:
                trans['Anzahl'] = trans['Anzahl'] * split['anzahlFaktor']
                trans['Stückpreis'] = trans['Stückpreis'] / split['anzahlFaktor']

def akkumuliereGleichesDatumTransaktionen(trans):
    if len(trans) == 0:
    #    print("no transactions")
        return trans
    toRemove = []
    first = 0
    for i, t in enumerate(trans):
        if i == 0: continue
        if t['datum'] == trans[first]['datum']:
            trans[first]['Anzahl'] += t['Anzahl']
            trans[first]['Kosten'] += t['Kosten']
            toRemove.append(i)
        else:
            first = i

    for p in reversed(toRemove):
        trans.pop(p)

    return trans


def erstelleVKZeile(transaktionen, v,k):
    # todo Kosten + Zusatzertrag
    kKosten = k['Anzahl'] * k['stueckkosten']
    vKosten = v['Anzahl'] * v['stueckkosten']
    kauf = k['Stückpreis'] * k['Anzahl']
    verkauf = v['Stückpreis'] * v['Anzahl']

    transDividenden = [d for d in transaktionen if d['Transaktionen'] in ['Dividende','Capital Gain']
                  and d['datum'] >= k['datum']
                  and d['datum'] <= v['datum']]
    if len(transDividenden) > 0:
        ertrag = sum([x['Stückpreis']*x['rate']/k['Anzahl']*v['Anzahl'] for x in transDividenden])
    else:
        ertrag = 0

    kchf = (kauf + kKosten) * k['rate']
    vchf = (verkauf - vKosten) * v['rate']

    tage = (v['datum'] - k['datum']).days
    if tage == 0:
        print("FEHLER: keine Tage")
    gewinn = vchf - kchf + ertrag
    renditePa = gewinn/kchf * 365/tage * 100
    kaufDatum = k['datum'].strftime("%Y/%m/%d")
    verkaufDatum = v['datum'].strftime("%Y/%m/%d")
    print(f"{   kaufDatum}, anz:{k['Anzahl']:8.1f}, p:{k['Stückpreis']:10,.2f},    kauf:{kauf:10,.0f}, kosten:{kKosten:7.2f}, kurs({k['WährungNettobetrag']}) {k['rate']:5.3f}, chf:{kchf:10,.0f}")
    print(f"{verkaufDatum}, anz:{v['Anzahl']:8.1f}, p:{v['Stückpreis']:10,.2f}, verkauf:{verkauf:10,.0f}, kosten:{vKosten:7.2f}, kurs({k['WährungNettobetrag']}) {v['rate']:5.3f}, chf:{vchf:10,.0f}, diff:{vchf-kchf:10,.0f}")
    print(f"{ertrag=:6.0f}, {gewinn=:6,.0f},  {tage=:4.0f}, {renditePa=:6.2f}")

    return gewinn


def kalkuliereTitelRendite(name, transaktionen):


    totalGewinn = 0
    totalVerlust = 0

    if len(transaktionen) == 0:
        print(f"FEHLER: keine transaktionen zu {name}")
        return 0, 0

    #print(f"titel: {transaktionen[0]['Name']=}")

    kaeufe = []
    verkaeufe = []
    kosten = []
    ertrag = 0

    basisDatum = datetime.date(2000,1,1)
    gesamtTage = (config.berechnungsDatum - basisDatum).days

    passiveZinstage = 0
    anzahlGekauft = 0
    anzahlVerkauft = 0

    kauf = namedtuple('kauf', 'datum nettobetrag kosten passivTage')
    verkauf = namedtuple('kauf', 'datum nettobetrag kosten passivTage')

    for trans in transaktionen:
        normalisiereAnzahlStueckpreis(trans)

    # für jeden Verkauf in aufsteigendem datum
    transVerkauf = [d for d in transaktionen if d['Transaktionen'] in ['Verkauf', 'Titelausgang']]
    orderedVerkauf = sorted(transVerkauf, key=lambda k: k['datum'])

    transKauf = [d for d in transaktionen if d['Transaktionen'] in ['Kauf', 'Kapitalerhöhung', 'Spin off']]
    orderedKauf = sorted(transKauf, key=lambda k: k['datum'])

    orderedKauf1 = akkumuliereGleichesDatumTransaktionen(orderedKauf)
    # stückkosten
    for k in orderedKauf1:
        k['stueckkosten'] = k['Kosten'] / k['Anzahl']
    orderedVerkauf1 = akkumuliereGleichesDatumTransaktionen(orderedVerkauf)
    for v in orderedVerkauf1:
        v['stueckkosten'] = v['Kosten'] / v['Anzahl']

    # finde kauf zu verkauf
    if len(orderedVerkauf1) > 0:
        for v in orderedVerkauf1:
            for k in orderedKauf1:
                if k['Anzahl'] == 0:
                    continue
                if v['Anzahl'] == 0:
                    break
                if k['Anzahl'] <= v['Anzahl']:
                    restV = v['Anzahl'] - k['Anzahl']
                    v['Anzahl'] = k['Anzahl']
                    gewinn = erstelleVKZeile(transaktionen, v, k)
                    if gewinn > 0:
                        totalGewinn += gewinn
                    else:
                        totalVerlust += gewinn

                    v['Anzahl'] = restV
                    k['Anzahl'] = 0
                    continue
                else:
                    restK = k['Anzahl'] - v['Anzahl']
                    k['Anzahl'] = v['Anzahl']
                    gewinn = erstelleVKZeile(transaktionen, v, k)
                    if gewinn > 0:
                        totalGewinn += gewinn
                    else:
                        totalVerlust += gewinn

                    k['Anzahl'] = restK
                    v['Anzahl'] = 0
                    break

    # verkaufe offene käufe zum bewertungstag
    if len(orderedKauf1) == 0:
        print(f"FEHLER: kein Kauf vorhanden")
        return 0, 0

    v = orderedKauf1[0].copy()
    for k in orderedKauf1:
        if k['Anzahl'] > 0:
            v['Anzahl'] = k['Anzahl']
            v['stueckkosten'] = k['stueckkosten']   # annahme verkaufskosten gleich kaufkosten
            v['datum'] = config.berechnungsDatum
            waehrung = k['WährungNettobetrag']
            rateToChf = 1
            if waehrung != 'CHF':
                rateToChf = config.currencyConverter.convert(1, waehrung, 'CHF', date=config.berechnungsDatum)
            v['rate'] = rateToChf
            try:
                v['Stückpreis'] = config.letzterPreis[k['ISIN']]
                gewinn = erstelleVKZeile(transaktionen, v, k)
                if gewinn > 0:
                    totalGewinn += gewinn
                else:
                    totalVerlust += gewinn


            except Exception as e:
                v['Stückpreis'] = 0
                print(f"FEHLER: kein aktueller Wert zu ISIN {k['ISIN']=}")

    return totalGewinn, totalVerlust

def titelRenditen(transaktionen):

    gesamtGewinn = 0
    gesamtVerlust = 0

    nameListe = set([transaktionen[x]['Name'] for x in transaktionen \
                     if len(transaktionen[x]['Name']) > 0 ])
                     #if transaktionen[x]['Name'] == 'EMS-CHEMIE N'])

    orderedNameListe = sorted(nameListe)
    for name in orderedNameListe:

        if name in nameExcludeList: continue

        print("-------")
        print(name)

        # test einzelne WS
        #if name != "ZUEBLIN IMM N":
        #    continue
        #if "PRECIOUS" in symbol: continue       # es gibt keinen kauf in den transaktionen???
        #if symbol == "CS GROUP ANR": continue

        #titelTrans = [transaktionen[x] for x in transaktionen if transaktionen[x]['Name'].replace("(","").replace(")","")  == name]
        titelTrans = [transaktionen[x] for x in transaktionen if transaktionen[x]['Name'] == name]
        orderedTitelTrans = sorted(titelTrans, key=lambda k: k['tage'])

        totalGewinn, totalVerlust = kalkuliereTitelRendite(name, orderedTitelTrans)

        print(f"{totalGewinn=:10,.0f}, {totalVerlust=:10,.0f}")
        gesamtGewinn += totalGewinn
        gesamtVerlust += totalVerlust

    print("===================================================")
    print(f"{gesamtGewinn=:10,.0f}, {gesamtVerlust=:10,.0f}")