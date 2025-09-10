# baza.py
import os
import pymssql
import pandas as pd

# --- Konfiguracija iz environment varijabli ---
DB_SERVER   = os.getenv("DB_SERVER", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "1433"))
DB_NAME     = os.getenv("DB_NAME", "infoeduka_view")
DB_USER     = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

brojac = 0

def get_conn():
    # azure/sql server; pymssql radi bez dodatnih parametara
    return pymssql.connect(
        server=DB_SERVER,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        login_timeout=10,
        timeout=30,
        charset="utf8"
    )

def fetch_data_from_db(query, params=None):
    """Univerzalna funkcija za dohvaćanje podataka iz baze."""
    global brojac
    try:
        with get_conn() as conn:
            df = pd.read_sql(query, conn, params=params)
        brojac += 1
        return df
    except pymssql.OperationalError as e:
        print(f"❗ DB OperationalError: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❗ Nepoznata greška: {e}")
        return pd.DataFrame()

def akademske_godine():
    query = "SELECT * FROM dbo.analytics_vss_struktura_akad_godine"
    df = fetch_data_from_db(query)

    if df is None or df.empty:
        # fallback vrijednosti
        return pd.DataFrame(), "2023/2024"

    # pokušaj naći aktualnu; inače prva
    try:
        if not df[df["aktualna"] == "1"].empty:
            aktualna = df.loc[df["aktualna"] == "1", "naziv"].iloc[0]
        else:
            aktualna = df["naziv"].iloc[0]
    except Exception:
        aktualna = "2023/2024"

    return df, aktualna

