

import pandas as pd
import numpy as np

import config

def korrSymbol(symbol):
    out = symbol
    if symbol.lower() == "car-investissem":
        out = 'CAR-INVESAEURAC'

    if symbol.lower() == "Res-GlobaMicrAD":
        out = 'RES - MICROANDSME'

    if symbol.lower() == "CS-responsAbili":
        out = 'RES - MICROANDSME'

    return out


def scrapeSwissquoteTradingPageWithPandas(transaktionen):

    barBestand = 3
    assetTabelle = 4
    symbolCol = 3
    isinCol = 4
    wertCol = 6
    letzterPreisCol = 8
    currencyCol = 9

    with open('D:/Privat/Geld/Swissquote/Performance/portfolio_2020_12_31_files/AccountCtrl.html', 'r') as html:

        contents = html.read()
        df_list = pd.read_html(contents)

        # tabelle der barbestände
        totalBar = 0
        numRows = df_list[barBestand].shape[0]
        for i in range(numRows):
            w = df_list[barBestand]['Währung'][i]
            b = df_list[barBestand]['Barsaldo'][i]
            k = df_list[barBestand]['Kurse'][i]

            if w == "Total CHF":
                config.totalBar = df_list[barBestand]['Barsaldo'][i]

        # kurse müssen für die bewertung der nicht verkauften assets bekannt sein

        # tabelle der offenen assets
        numRows = df_list[assetTabelle].shape[0]
        for row in range(numRows):
            asset = df_list[assetTabelle].T[row]
            #print(asset[3])
            if isinstance(asset[symbolCol],str):
                if "Symbol" in asset[symbolCol]: continue
                if "Subtotal" in asset[symbolCol]: continue
                if "Seitentotal" in asset[symbolCol]:
                    totalWert = float(asset[wertCol].replace("'", ""))
                    config.letzterPreis['Total'] = totalWert
                    continue
            else:
                if np.isnan(asset[symbolCol]): continue

            symbol = korrSymbol(asset[symbolCol])
            # finde die isin des symbols aus den transaktionen weil eine isin über die zeit verschiedene symbole habe kann
            isinListe = [transaktionen[x]['ISIN'] for x in transaktionen if korrSymbol(transaktionen[x]['Symbol']) == symbol]
            if len(isinListe) > 0:
                isin = isinListe[0]
                if isin=='CH0011037469': isin = 'CH0316124541'      # SYNN zu SYNNE
                letzterPreis = float(asset[letzterPreisCol].replace("'", ""))
                config.letzterPreis[isin] = letzterPreis
            else:
                print(f"keine isin zu {symbol=}")




