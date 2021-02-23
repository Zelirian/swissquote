

DROP TABLE IF EXISTS raw;

CREATE TABLE IF NOT EXISTS exchangeRateHistory (
    datum TEXT,
    waehrung TEXT NOT NULL,
    rateToChf REAL
);

DROP TABLE IF EXISTS assets;
CREATE TABLE assets (
    assetId INTEGER PRIMARY KEY,
    assetName TEXT NOT NULL
);

DROP TABLE IF EXISTS transactions;
CREATE TABLE transactions (
    transId INTEGER PRIMARY KEY,
    assetId INTEGER,
    transaktionDatum TEXT,
    transaktionArt TEXT,
    anzahl INTEGER,
    kaufKurs FLOAT,
    kaufKosten FLOAT,
    kaufWaehrung TEXT,
    waehrungKurs FLOAT,
    chf INTEGER,
    FOREIGN KEY (assetId) REFERENCES assets(assetId)
);



