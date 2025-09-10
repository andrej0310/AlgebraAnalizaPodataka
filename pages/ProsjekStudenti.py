import dash
from dash import dcc, html, dash_table, Input, Output, State
import pandas as pd
import pymssql
from dash.dash_table.Format import Format, Scheme
from sqlalchemy import create_engine
import warnings
from baza import fetch_data_from_db
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import io


dash.register_page(__name__, path="/ProsjekStudenti")  # ✅ Ispravno

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy*")


# 🔹 Povezivanje sa SQL Serverom
def get_student_data():
    
    query = """
    SELECT * FROM dbo.analytics_final_statusi_studenata
    WHERE godina = '1. godina' AND status_semestra = 'U'
    """
    df = fetch_data_from_db(query)
    
    return df

# 🔹 Dohvati podatke i kreiraj DataFrame sa studentima (jedinstveni OIB)
df_students = get_student_data()
df_students_unique = df_students.drop_duplicates(subset=['oib'])


# 🔹 Dohvati jedinstvene akademske godine i sortiraj ih opadajuće (najnovija prva)
akademske_godine = sorted(df_students_unique["ak_god_naziv"].unique(), reverse=True)


# Kreiranje Dash aplikacije
app = dash.get_app()

layout = html.Div(style={'background-color': '#F4F4F4', 'padding': '20px'}, children=[
    
     dcc.Store(id="processed-data"),

    # Header naslovom
    html.Div([
        html.H1("Studenti - Analiza po gneraciji")
    ]),
    
    # Dropdown filteri

    html.Div([
            html.Label("Generacija:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
            dcc.Dropdown(
            id="filter_akademska_godina",
            options=[{"label": godina, "value": godina} for godina in akademske_godine],
            placeholder="Odaberi akademsku godinu",
            multi=False,
            style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
            className="my-dropdown"
    ),
            html.Label("Studij:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
            dcc.Dropdown(
            id="filter_studij",
            placeholder="Odaberi studij",
            multi=False,
            style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
            className="my-dropdown"
    ),
            html.Label("Smjer:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
            dcc.Dropdown(
            id="filter_smjer",
            placeholder="Odaberi smjer",
            multi=False,
            style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
            className="my-dropdown"
    )
    ],style={'display': 'flex', 'justify-content': 'center',  "align-items": "center", "width": "100%"}),

    html.Div([    
        html.Hr(className="custom-line"),
        html.Label("Broj studenata (po generaciji)")
    ],className="graph-naslov"),

    dcc.Loading(
        id="loading-container-1",
        type="circle",  # Može biti "default", "circle" ili "dot"
        children=[
            html.Div([
                html.Div([
                    dbc.Card([
                        dbc.CardHeader("UKUPAN BROJ STUDENATA",className="card-header"),
                        dbc.CardBody([
                            html.H5(id="broj-U", className="card-broj")
                        ])
                    ], className="status-card")
                ], id="kartica1"),
                 
                html.Div([
                    dcc.Graph(id='spol-nacin-graph')  # Grafikon
                 ],id="kartica2"),
                 
                html.Div([
                    dbc.Card([
                        dbc.CardHeader("DIPLOMIRALI",className="card-header"),
                        dbc.CardBody([
                            html.H5(id="broj-D", className="card-title"),
                            html.H2(id="posto-D", className="card-text"),
                            html.H2(id="vrijeme-D", className="card-text"),
                        ])
                    ], className="status-card")
                ],id="kartica3"),
                
                html.Div([
                    dbc.Card([
                    dbc.CardHeader("ISPISANI"),
                    dbc.CardBody([
                        html.H5(id="broj-I", className="card-title"),
                        html.H2(id="posto-I", className="card-text"),
                        html.H2(id="vrijeme-I", className="card-text"),
                        ])
                    ], className="status-card")     
                ], id="kartica4"),
                
                html.Div([
                     dcc.Graph(id='status-studija-pie', style={'width': '100%', 'height': '95%'})  # Grafikon
                ], id="kartica5"),

            ],id="kartice-grupno"),

             html.Div([    
                html.Hr(className="custom-line"),
                html.Label("Prosjčene ocjene i težinski prosijek")
            ],className="graph-naslov"),

        ]
    ),
    dcc.Loading(
        id="loading-container-2",
        type="circle",  # Može biti "default", "circle" ili "dot"
        children=[
            # 🔹 CheckList filter za "način studiranja"
            html.Div([
                html.Div([
                    html.Label("Filtriraj po načinu studiranja:"),
                    dcc.Checklist(
                        id="filter_nacin",
                        options=[],  # Automatski generirano
                        inline=True,
                        className="dash-checklist"
                    )
                ], className="checklist-container"),
                
                html.Div([
                    html.Label("Filtriraj po trenutnoj godini:"),
                        dcc.Checklist(
                            id="filter_trenutna",
                            options=[],  # Automatski generirano
                            inline=True,
                            className="dash-checklist"
                        )
                ], className="checklist-container"),

                html.Div([
                    html.Label("Filtriraj po statusu studija:"),
                        dcc.Checklist(
                            id="filter_statusStudij",
                            options=[],  # Automatski generirano
                            inline=True,
                            className="dash-checklist"
                        )
                ], className="checklist-container"),  
            ],style={'display': 'flex', 'justify-content': 'center',  "align-items": "center", "width": "100%", "gap":'40px'}),
            
        
            # Tabela sa podacima
            html.Div([  
                dash_table.DataTable(
                    id="student_table",
                    columns=[
                        {"name": "#", "id": "redni_broj", "type": "numeric"},
                        {"name": "Student", "id": "ime_prezime"},
                        {"name": "JMBAG", "id": "jmbag"},
                        {"name": "R/I", "id": "nacin"},
                        {"name": "Pros. ocj.", "id": "prosjek_ocjena",
                        "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed),}, #Klasičan prosjek
                        {"name": "Tež. pros.", "id": "tezinski_prosjek",
                        "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)},  # Težinski prosjek
                        {"name": "Godina", "id": "trenutna_godina"}, #Trenutna godina
                        {"name": "Status", "id": "status_studija"},
                        {"name": "Vrijeme stud.", "id": "vrijeme_studiranja"},
                    ],
                    # ✅ Stilizacija zaglavlja tablice
                    data=[],
                    sort_action="native",
                    filter_action="native",
                    page_action="none",
                    style_header={
                        'backgroundColor': '#be1e67',  # Roza zaglavlje
                        'color': 'white',
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                        'border': '1px solid #ddd'
                    },
                    # ✅ Povezivanje CSS-a
                    css=[
                        
                        {"selector": ".dash-spreadsheet", "rule": "border-collapse: collapse !important;"}
                    ]   
                )
            ])
        ]
    )
])

#ažuriranje studija na temelju akademske
@app.callback(
    Output("filter_studij", "options"),
    Input("filter_akademska_godina", "value")
)
def update_studij_options(selected_godina):
    if not selected_godina:
        return []
    filtered_df = df_students_unique[df_students_unique["ak_god_naziv"] == selected_godina]
    studiji_options = [{"label": s, "value": s} for s in filtered_df["studij_naziv"].unique()]
    return studiji_options

#ažuriranje smjera na temelju studija
@app.callback(
    Output("filter_smjer", "options"),
    [Input("filter_akademska_godina", "value"),
     Input("filter_studij", "value")]
)
def update_smjer_options(selected_godina, selected_studij):
    if not selected_godina or not selected_studij:
        return []
    filtered_df = df_students_unique[
        (df_students_unique["ak_god_naziv"] == selected_godina) &
        (df_students_unique["studij_naziv"] == selected_studij)
    ]
    smjer_options = [{"label": smjer, "value": smjer} for smjer in filtered_df["smjer_naziv"].unique()]
    return smjer_options

#dohvaćanje prosječnih ocjena iz baze
def get_student_grades(jmbags):
    if not jmbags:
        return pd.DataFrame(columns=["jmbag", "kolegij_sifra", "ocjena"])

    query = """
    SELECT jmbag, kolegij_sifra, ocjena
    FROM dbo.analytics_final_studentipredmeti
    WHERE ocjena > 1 
    AND kolegij_naziv != 'Praksa' 
    AND jmbag IN %s
    """
    if len(jmbags) == 1:
        jmbags = (jmbags[0],)  # Oblik za jedan element
    else:
        jmbags = tuple(jmbags)  # Oblik za više elemenata

    df_grades = fetch_data_from_db(query, params=(jmbags,))
    
    return df_grades

#dohvaćanje ects-a
def get_ects_data():
    """ Dohvaća ECTS bodove za kolegije. """
    
    query = "select sifra, ects from dbo.analytics_vss_predmeti"
    df_ects = fetch_data_from_db(query)
    
    return df_ects

#dohvaćanje trenutne godine studenta
def get_student_godina(jmbags):
    if not jmbags:
        return pd.DataFrame(columns=["jmbag", "trenutna_godina"])  # 🔹 DODANO: Definiran novi stupac

    if len(jmbags) == 1:
        jmbags = (jmbags[0],)  # Oblik za jedan element
    else:
        jmbags = tuple(jmbags)  # Oblik za više elemenata

    query = """
        SELECT jmbag,MAX(godina) AS trenutna_godina
        FROM dbo.analytics_final_statusi_studenata
        WHERE jmbag IN %s
        GROUP BY jmbag;
    """
    
    df_godina = fetch_data_from_db(query, params=(jmbags,))
    
    return df_godina

# 🔹 Funkcija za izračun `vrijeme_studiranja`
def format_vrijeme_studiranja(datum_statusa, status_studija, datum_pocetka):
    if pd.isna(datum_statusa) and status_studija != "Upis":
        return "N/A"

    # ✅ Ako je status "Upis", koristimo današnji datum
    if status_studija == "upis":
        datum_statusa = datetime.today()

    # ✅ Izračun razlike u danima
    delta = datum_statusa - datum_pocetka

    # ✅ Preračunavanje u godine i mjesece
    total_months = delta.days // 30  # Pretpostavljamo da mjesec ima ~30 dana
    godine = total_months // 12
    mjeseci = total_months % 12

    return f"{godine} g {mjeseci} m", total_months


@app.callback(
    Output("processed-data", "data"),
    [
     Input("filter_akademska_godina", "value"),
     Input("filter_studij", "value"),
     Input("filter_smjer", "value"),
    ],
)
def update_dataframe(selected_godina, selected_studij, selected_smjer):
    if not selected_godina or not selected_studij or not selected_smjer:
        return None

    # 🔹 Filtriranje studenata
    filtered_students = df_students_unique[
        (df_students_unique["ak_god_naziv"] == selected_godina) &
        (df_students_unique["studij_naziv"] == selected_studij) &
        (df_students_unique["smjer_naziv"] == selected_smjer)
    ]

    if filtered_students.empty:
        return None

    # 🔹 Dohvati ocjene studenata
    jmbags = filtered_students["jmbag"].astype(str).tolist()
    df_grades = get_student_grades(jmbags)

    # 🔹 Dohvati ECTS podatke za kolegije
    df_ects = get_ects_data()

    #print(df_ects.head(10))
    #print(df_ects.loc[df_ects["sifra"] == "22-06-500"])

    # 🔹 Spajanje ocjena s ECTS bodovima (preko "kolegij_sifra" u jednoj i "sifra" u drugoj tablici)
    df_grades = df_grades.merge(df_ects, left_on="kolegij_sifra", right_on="sifra", how="left")

    #print(df_grades.loc[df_grades["jmbag"] == "0321021511"])

    # 🔹 Izračun težinskog prosjeka
    df_weighted = df_grades.groupby("jmbag").apply(
        lambda x: (x["ocjena"] * x["ects"]).sum() / x["ects"].sum() if x["ects"].sum() > 0 else 0
    ).reset_index(name="tezinski_prosjek")

    # 🔹 Izračun klasičnog prosjeka ocjena
    df_avg = df_grades.groupby("jmbag")["ocjena"].mean().reset_index(name="prosjek_ocjena")

    # 🔹 Dohvati najveću godinu studenta i dodaj kao novi stupac
    df_godina = get_student_godina(jmbags)  # 🔹 DODANO: Dohvat najveće godine

    # 🔹 Spajanje sa studentima
    df_final = filtered_students.merge(df_avg, on="jmbag", how="left").fillna(0)
    df_final = df_final.merge(df_weighted, on="jmbag", how="left").fillna(0)
    df_final = df_final.merge(df_godina, on="jmbag", how="left").fillna(0)

    # 🔹 Zaokruživanje na 2 decimale
    df_final["prosjek_ocjena"] = df_final["prosjek_ocjena"].astype(float).round(2)
    df_final["tezinski_prosjek"] = df_final["tezinski_prosjek"].astype(float).round(2)


    # Vrijeme studiranja
    # 🔹 Izvlačenje prve godine iz select_godina
    pocetna_godina = int(selected_godina.split("/")[0])

    # 🔹 Definiranje datum_pocetka kao 1. listopada te godine
    datum_pocetka = datetime(pocetna_godina, 10, 1)

    df_final["datum_statusa"] = pd.to_datetime(df_final["datum_statusa"])
    df_final[["vrijeme_studiranja", "total_months"]] = df_final.apply(
    lambda row: pd.Series(format_vrijeme_studiranja(row["datum_statusa"], row["status_studija"], datum_pocetka)),axis=1)


    # 🔹 Sortiranje od najveće prema najmanjoj ocjeni
    df_final = df_final.sort_values(by="prosjek_ocjena", ascending=False)

    # 🔹 Spajamo ime i prezime u jedan stupac
    df_final["ime_prezime"] = df_final["prezime"] + " " + df_final["ime"]

    return df_final.to_json(date_format="iso", orient="split")


#ažuriranje tablice sa studentima i prosjecima
@app.callback(
    Output("student_table", "data"),
    [
    Input("filter_nacin", "value"),
    Input("filter_trenutna", "value"),
    Input("filter_statusStudij", "value"),
    Input("processed-data", "data")
    ],
)
def update_student_table(selected_nacin, selected_trenutna, selected_statusStudij, data_json):

    if not data_json:
        return []

    df_final_t= df = pd.read_json(io.StringIO(data_json), orient="split")

    # 🔹 Ako su odabrane opcije u `CheckList - nacin studiranja`, filtriraj tablicu
    if selected_nacin:
        df_final_t = df_final_t[df_final_t["nacin"].isin(selected_nacin)]

      # 🔹 Ako su odabrane opcije u `CheckList - trenutna godina`, filtriraj tablicu
    if selected_trenutna:
        df_final_t = df_final_t[df_final_t["trenutna_godina"].isin(selected_trenutna)]

      # 🔹 Ako su odabrane opcije u `CheckList - status studija`, filtriraj tablicu
    if selected_statusStudij:
        df_final_t = df_final_t[df_final_t["status_studija"].isin(selected_statusStudij)]

     # 🔹 Dodavanje rednog broja
    df_final_t = df_final_t.reset_index(drop=True)
    df_final_t["redni_broj"] = df_final_t.index + 1

    # 🔹 Vraćanje podataka u Dash tablicu
    return df_final_t[["redni_broj", "ime_prezime", "jmbag", "prosjek_ocjena", "tezinski_prosjek", "nacin", "trenutna_godina","status_studija","vrijeme_studiranja"]].to_dict("records")
  

@app.callback(
    Output("broj-D", "children"),
    Output("posto-D", "children"),
    Output("vrijeme-D", "children"),
    Output("broj-I", "children"),
    Output("posto-I", "children"),
    Output("vrijeme-I", "children"),
    Output("broj-U", "children"),
    Output('spol-nacin-graph', 'figure'),
    Output('status-studija-pie', 'figure'),
    [
     #Input("filter_akademska_godina", "value"),
     #Input("filter_studij", "value"),
     #Input("filter_smjer", "value"),
     Input("processed-data", "data")
    ],
)
def update_student_kartice(data_json):
    #selected_godina, selected_studij, selected_smjer
    #not selected_godina or not selected_studij or not selected_smjer:

    if not data_json:
        fig = go.Figure()
        fig.update_layout(title="Nema dostupnih podataka", height=230)
        fig_status = go.Figure()
        fig_status.update_layout(title="Nema dostupnih podataka", height=500)
        return 0, "0%", "N/A", 0, "0%", "N/A", 0, fig, fig_status
    
     # Dekodiranje JSON-a natrag u DataFrame
    df_final2 = df = pd.read_json(io.StringIO(data_json), orient="split")

    #print(df_final.columns.tolist())

    ### DIPLOMIRALI"
    # Filtriranje samo diplomiranih
    diplomirani_df = df_final2[df_final2["status_studija"].str.lower() == "diplomirala/o"]

    # Broj diplomiranih
    broj_diplomiranih = len(diplomirani_df)

    # Ukupan broj studenata
    ukupno_studenata = len(df_final2)

    # Izračun postotka
    postotak_diplomiranih = (broj_diplomiranih / ukupno_studenata) * 100 if ukupno_studenata > 0 else 0

    # 🔹 Izračun prosječnog trajanja studiranja u minutama
    prosjek_mjeseci_D = diplomirani_df["total_months"].mean()

    # 🔹 Konverzija u godine i mjesece
    if pd.notna(prosjek_mjeseci_D):  # Provjera da nije NaN
        prosjecne_godine_D = int(prosjek_mjeseci_D // 12)
        prosjecni_mjeseci_D = int(prosjek_mjeseci_D % 12)
        prosjecno_trajanje_D = f"{prosjecne_godine_D} g. {prosjecni_mjeseci_D} mj."
    else:
        prosjecno_trajanje_D = "N/A"

    ######
    #### ISPISANI ####
        # Filtriranje samo ispisanih
    ispisani_df = df_final2[df_final2["status_studija"].str.lower() == "ispis"]

    # Broj diplomiranih
    broj_ispisanih = len(ispisani_df)

    # Ukupan broj studenata
    ukupno_studenata = len(df_final2)

    # Izračun postotka
    postotak_ispisanih = (broj_ispisanih / ukupno_studenata) * 100 if ukupno_studenata > 0 else 0

    # 🔹 Izračun prosječnog trajanja studiranja u minutama
    prosjek_mjeseci_I = ispisani_df["total_months"].mean()

    # 🔹 Konverzija u godine i mjesece
    if pd.notna(prosjek_mjeseci_I):  # Provjera da nije NaN
        prosjecne_godine_I = int(prosjek_mjeseci_I // 12)
        prosjecni_mjeseci_I = int(prosjek_mjeseci_I % 12)
        prosjecno_trajanje_I = f"{prosjecne_godine_I} g. {prosjecni_mjeseci_I} mj."
    else:
        prosjecno_trajanje_I = "N/A"

    ######
    ## GRAF Redovni/Izvanredni + Muško/Žensko
    # Ukupan broj studenata
    total_students = len(df_final2)

    # Izračun postotaka za spol
    df_spol = df_final2['spol'].value_counts(normalize=True).mul(100).reset_index()
    df_spol.columns = ['kategorija', 'postotak']
    df_spol['tip'] = 'Spol'

    # Izračun postotaka za način studiranja
    df_nacin = df_final2['nacin'].value_counts(normalize=True).mul(100).reset_index()
    df_nacin.columns = ['kategorija', 'postotak']
    df_nacin['tip'] = 'Način studiranja'

    # Spajanje u jedan DataFrame
    df_combined = pd.concat([df_spol, df_nacin])

    # Kreiranje grafikona s postotcima
    fig = px.bar(df_combined, 
                 x='postotak', 
                 y='kategorija', 
                 color='tip',  # Razlikovanje između spola i načina studiranja
                 orientation='h',
                 title="Postotak studenata prema spolu i načinu studiranja",
                 #labels={'postotak': 'Postotak (%)', 'kategorija': 'Kategorija', 'tip': 'Tip podataka'},
                 text=df_combined['postotak'].round(2))  # Prikaz postotaka na grafu

    fig.update_layout(
        legend_title="Grupa",
        height=230,   # Postavlja ukupnu visinu grafikona
        bargap=0.4,   # Povećava razmak između stupaca (smanjuje širinu)
        margin=dict(l=50, r=50, t=50, b=50),  # Smanjuje margine
        title={
            'text':"Postotak studenata prema spolu i načinu studiranja",
            'font': {'size': 16, 'color': 'black'}
        },
        xaxis=dict(
            showticklabels=False,
            title=None),  # ✅ Ugašene oznake na X osi
        yaxis=dict(
            #showticklabels=False,
            title=None
            )   # ✅ Ugašene oznake na Y osi    
    )
    fig.update_traces(
        marker=dict(line=dict(width=2)),  # Dodaje obrub oko stupaca
        texttemplate='%{text:.2f}%%',  # ✅ Prikaz postotka bez znanstvene notacije
        textposition='outside',  # ✅ Postavljanje brojeva iznad stupaca
        textfont=dict(size=16, color='black')  # ✅ Povećanje veličine i boje teksta 
    )

    #yaxis_title="Kategorija", xaxis_title="Postotak (%)",

    #### Graf tortni - način studiranja
    df_status = df_final2['status_studija'].value_counts(normalize=True).mul(100).reset_index()
    df_status.columns = ['status_studija', 'postotak']

    # Kreiranje tortnog grafikona
    fig_status = px.pie(df_status, 
                 names='status_studija', 
                 values='postotak', 
                 title="Postotak studenata prema statusu studija",
                 labels={'postotak': 'Postotak (%)', 'status_studija': 'Status studija'},
                 hole=0.3)  # Dodaje "donut" efekt

    # Podešavanje prikaza postotaka na grafu
    pull_values = [0.1] * min(len(df_status), 10)
    fig_status.update_traces(
        textinfo='percent+label',  # Prikazuje postotak i naziv statusa
        textfont=dict(size=14, color='black'),
        textfont_size=16, 
        pull=pull_values,
        textposition="outside",
        marker=dict(line=dict(color='#000000', width=2))
    )
    return (
        f"Broj diplomiranih: {broj_diplomiranih}",
        f"{postotak_diplomiranih:.2f}%",
        f"Prosječno do diplomiranja: {prosjecno_trajanje_D}",
        f"Broj ispisanih: {broj_ispisanih}",
        f"{postotak_ispisanih:.2f}%",
        f"Prosječno do ispisa: {prosjecno_trajanje_I}",
        ukupno_studenata,
        fig,
        fig_status 
    )



@app.callback(
    Output("filter_nacin", "options"),
    [Input("filter_akademska_godina", "value"),
     Input("student_table", "data")
     ]
)
def update_nacin_options(selected_godina, student_data):
    if not student_data:
        return []

    df = pd.DataFrame(student_data)
    unique_nacini = df["nacin"].unique()

    return [{"label": n, "value": n} for n in unique_nacini]

@app.callback(
    Output("filter_trenutna", "options"),
    [Input("filter_akademska_godina", "value"),
     Input("student_table", "data")
     ]
)
def update_trenutna_options(selected_godina, student_data):
    if not student_data:
        return []

    df = pd.DataFrame(student_data)
    unique_trenutna = sorted(df["trenutna_godina"].unique())

    return [{"label": n, "value": n} for n in unique_trenutna]

@app.callback(
    Output("filter_statusStudij", "options"),
    [Input("filter_akademska_godina", "value"),
     Input("student_table", "data")
    ]
)
def update_statusStudija_options(selected_statusStudija, student_data):
    if not student_data:
        return []

    df = pd.DataFrame(student_data)
    unique_statusiStudija = df["status_studija"].unique()

    return [{"label": n, "value": n} for n in unique_statusiStudija]

if __name__ == '__main__':
    app.run_server(debug=True)

