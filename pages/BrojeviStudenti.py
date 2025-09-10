import dash
from dash import dcc, html, Input, Output, callback_context, no_update, State, dash_table, MATCH
import pandas as pd
import pymssql
import plotly.express as px
import warnings
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from baza import fetch_data_from_db, akademske_godine


dash.register_page(__name__, path="/BrojeviStudenti")  # ✅ Ispravno
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy*")


#Dohvaćanje akademksih godina
df_akademske, akademska_godina = akademske_godine()


def get_student_data(akademska_godina):
    """ Dohvati podatke o studentima za određenu akademsku godinu. """
    
    query = """
        SELECT oib, studij_naziv, smjer_naziv, godina, status_semestra, spol, nacin, status_studija
        FROM dbo.analytics_final_statusi_studenata
        WHERE ak_god_naziv = %s
    """

    df = fetch_data_from_db(query, params=[akademska_godina])
    
    return df

def get_student_GS(akademska_godina):
    """ Dohvati podatke o GS studentima za određenu akademsku godinu ili sve GS studente """
    
    if akademska_godina == '':
        query = """
            SELECT prezime, ime, jmbag, ak_god_naziv, godina, semestar_naziv, spol, smjer_naziv, status_semestra, status_studija, datum_statusa, student_tip
            FROM dbo.analytics_final_statusi_studenata
            WHERE student_tip LIKE %s
            AND semestar_naziv = %s
            AND smjer_naziv LIKE %s
        """
        params = ('%Goldsmiths%', 'Zimski semestar', '%(Engleski)%')
        df_GS = fetch_data_from_db(query,params=params)
    else:
        query = """
            SELECT prezime, ime, jmbag, ak_god_naziv, godina, semestar_naziv, spol, smjer_naziv, status_semestra, status_studija, datum_statusa, student_tip
            FROM dbo.analytics_final_statusi_studenata
            WHERE ak_god_naziv = %s
            AND student_tip LIKE %s
            AND semestar_naziv = %s
            AND smjer_naziv LIKE %s
        """
        params = (akademska_godina,'%Goldsmiths%', 'Zimski semestar', '%(Engleski)%')
        df_GS = fetch_data_from_db(query, params=params)
    
    return df_GS

df = get_student_data(akademska_godina)
df_GS = get_student_GS('')
ds_GS_akd = get_student_GS(akademska_godina)


# Kreiranje Dash aplikacije
app = dash.get_app()

#TAB1
tab1_content = html.Div(style={'background-color': '#F4F4F4', 'padding': '20px'}, children=[ 
    # Header naslovom
    html.Div([
        html.H2("Studenti - Brojevi studenata", style={"text-align": "center"}),
        
    ]),
   
    # Dropdown filteri

  
    html.Div([
        html.Label("Studij:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id="dropdown-studij", 
                     placeholder="Odaberi studij", 
                     options=[],
                     multi=False,
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown"),

        html.Label("Smjer:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id="dropdown-smjer", 
                     placeholder="Odaberi smjer", 
                     options=[],
                     multi=False,
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown"),

        html.Label("Školska godina", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id="dropdown-godina", 
                     placeholder="Odaberi školsku godinu", 
                     options=[],
                     multi=False,
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown")
    ], style={'display': 'flex', 'justify-content': 'center',  "align-items": "center", "width": "100%"}),

    html.Div([    
        html.Label("Broj studenata (po akademskoj godini)")
    ],className="graph-naslov"),
    
    dcc.Loading(
        id="loading-container",
        type="circle",  # Može biti "default", "circle" ili "dot"
        children=[
            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("UKUPAN BROJ STUDENATA", className="card-title"),
                        html.H2(id="total-students", className="card-text")
                    ])
                ], className="student-card")  
            ],style={'display':'flex','justify-content': 'center',  "align-items":'center','margin-bottom':'15px'}),

            html.Div(style={'display': 'flex', 'justify-content': 'center','gap':'15px','margin-bottom':'15px'}, children=[
                dcc.Graph(id="graf-studenti-status", style={'width': '25%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}),
                dcc.Graph(id="graf-studenti-zavrseno", style={'width': '25%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'})
            ]),
            html.Div(style={'display': 'flex', 'justify-content': 'center','gap':'15px'}, children=[ 
                dcc.Graph(id="graf-studenti-nacin", style={'width': '25%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}),
                dcc.Graph(id="graf-studenti-spol", style={'width': '25%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}) 
            ]),
        ]
    ),

    #Skriveni objekti zbog Callbacka
    html.Div([
        dcc.Dropdown(id="dropdown-smjer-gs", options=[], style={"display": "none"}),
        dcc.Dropdown(id="dropdown-godina-gs", options=[], style={"display": "none"})
    ])
  
])


#TAB2
tab2_content = html.Div(style={'background-color': '#F4F4F4', 'padding': '20px'}, children=[
     
    # Header naslovom
    html.Div([
        html.H2("Goldsmiths studenati", style={"text-align": "center"}),   
    ]),

    html.Div([
        html.Label("Smjer:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id="dropdown-smjer-gs", 
                     placeholder="Odaberi smjer", 
                     options=[],
                     multi=False,
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown"),

        html.Label("Školska godina", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id="dropdown-godina-gs", 
                     placeholder="Odaberi školsku godinu", 
                     options=[],
                     multi=False,
                     style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown")
    ], style={'display': 'flex', 'justify-content': 'center',  "align-items": "center", "width": "100%"}),

    html.Div([    
        html.Label("Broj studenata (po akademskoj godini)")
    ],className="graph-naslov"),
    
    dcc.Loading(
        id="loading-container",
        type="circle",  # Može biti "default", "circle" ili "dot"
        children=[
            dbc.Container([
                dash_table.DataTable(
                    id="gs-student-table",
                    columns=[
                        {"name": "Prezime", "id": "prezime"},
                        {"name": "Ime", "id": "ime"},
                        {"name": "JMBAG", "id": "jmbag"},
                        {"name": "Smjer", "id": "smjer_naziv"},
                        {"name": "Student tip", "id": "student_tip"},
                        {"name": "Status studija", "id":"status_studija"},
                        {"name": "ECTS Zimski", "id": "ects_zimski"},
                        {"name": "ECTS Zimski P", "id": "ects_zimski_p"},
                        {"name": "ECTS Ljetni", "id": "ects_ljetni"},
                        {"name": "ECTS Ljetni P", "id": "ects_ljetni_p"},
                    ],
                    style_table={"width": "100%", "overflowX": "auto"},  # 🚀 Rasteže tablicu po širini
                    style_cell={"textAlign": "left", "padding": "10px"},  # 📌 Poravnava tekst i dodaje padding
                    style_header={"backgroundColor": "#007bff", "color": "white", "fontWeight": "bold"},  # 📌 Plavo zaglavlje
                )
            ], fluid=True)
        ]
    ),

    #Dodani skriveni objekti zbog Callbacka
    html.Div([
        dcc.Dropdown(id="dropdown-studij", options=[], style={"display": "none"}),
        dcc.Dropdown(id="dropdown-smjer", options=[], style={"display": "none"}),
        dcc.Dropdown(id="dropdown-godina", options=[], style={"display": "none"}),
    ])
    
])

# Tabs komponenta**
tabs = html.Div([
    dbc.Tabs(
        [
            dbc.Tab(label="Brojevi studenata", tab_id="tab-1"),
            dbc.Tab(label="Goldsmiths", tab_id="tab-2"),
        ],
        id="tabs",
        active_tab="tab-1",  # Prvi tab je inicijalno aktivan
        className="nav-tabs mt-3"
    ),
    html.Div(id="content")  # Ovdje će se prikazivati sadržaj odabranog taba
])

# **Layout aplikacije**
layout = dbc.Container([
            dcc.Location(id="url", refresh=False),
            html.Div([
                html.H1("Studenti - Analiza po akademskoj godini", style={"text-align": "center"}),    
            ]),

            # PADAJUĆI IZBORNIK AKADEMSKA
            html.Div([
                html.Label("Akademska godina:", style={'font-size': '18px', 'font-weight': 'bold', 'margin-right': '10px'}),
                dcc.Dropdown(
                    id="akademska-godina-dropdown",
                    options=[{"label": godina, "value": godina} for godina in df_akademske["naziv"]],
                    value=akademska_godina,  # ✅ Inicijalna vrijednost
                    clearable=False,
                    style={'width': '150px', 'margin-left': '20px', "margin-right":"100px"},
                    persistence=True,  # ✅ Pamti odabir korisnika
                    persistence_type="session"  # ✅ Opcije: "local", "session", "memory"
                    ),
                ], style={'display': 'flex', 'align-items': 'center', 'background-color': '#ffffff', 'padding': '10px',"with":"50px"},
                   className="padajuci-akademska"
            ),
            
            tabs,

    ], fluid=True  # ✅ Osigurava prilagodbu širine ekrana
)

#**Callback funkcija za prebacivanje sadržaja u tabovima**
@app.callback(
        Output("content", "children"), 
        [Input("tabs", "active_tab")]
)
def switch_tab(at):
    if at == "tab-1":
        return tab1_content
    elif at == "tab-2":
        global df_GS
        df_GS = get_student_GS(akademska_godina)
        return tab2_content
    return html.P("Ovo ne bi trebalo biti prikazano...")

#SVI STUDENTI
@app.callback(
    Output('dropdown-studij', 'options'),
    Output('dropdown-smjer', 'options'),
    Output('dropdown-godina', 'options'),
    Output('dropdown-studij', 'value'),
    Output('dropdown-smjer', 'value'),
    Output('dropdown-godina', 'value'),
    Output('dropdown-smjer-gs','options'),
    Output('dropdown-godina-gs','options'),
    Output('dropdown-smjer-gs','value'),
    Output('dropdown-godina-gs','value'),
    Input("url", "pathname"),
    Input('akademska-godina-dropdown','value'),
    State('dropdown-studij', 'value'),
    State('dropdown-smjer', 'value'),
    State('dropdown-godina', 'value'),
    State('dropdown-smjer-gs','value'),
    State('dropdown-godina-gs','value')
)
def update_dropdown_options(pathname,selected_akgodina, selected_studij, selected_smjer, selected_godina, selected_sm_gs, selected_g_gs):
    
    #Akademska godina
    akademska_godina = selected_akgodina

    ## SVI STUDENTI
    global df    
    df = get_student_data(akademska_godina)
    
    # 🔹 Generiranje opcija za dropdown-e
    studij_options = [{"label": str(s), "value": str(s)} for s in sorted(df["studij_naziv"].dropna().unique())]
    smjer_options = []  # Prazan na početku
    godina_options = [{'label': g, 'value': g} for g in sorted(df['godina'].unique())]

    # Provjera da li su prethodno odabrane vrijednosti još uvijek dostupne
    if selected_studij not in [s["value"] for s in studij_options]:
        selected_studij = None
    if selected_smjer not in [s["value"] for s in smjer_options]:
        selected_smjer = None
    if selected_godina not in [g["value"] for g in godina_options]:
        selected_godina = None

    ## GS STUDENTI
    global df_GS_akd
    df_GS_akd = get_student_GS(akademska_godina)
    # 🔹 Generiranje opcija za dropdown-e
    smjer_options_gs = [{"label": str(sm), "value": str(sm)} for sm in sorted(df_GS_akd["smjer_naziv"].dropna().unique())]
    godina_options_gs = [{'label': go, 'value': go} for go in sorted(df_GS_akd['godina'].unique())]
     # Provjera da li su prethodno odabrane vrijednosti još uvijek dostupne
    if selected_sm_gs not in [sm["value"] for sm in smjer_options_gs]:
        selected_sm_gs = None
    if selected_g_gs not in [go["value"] for go in godina_options_gs]:
        selected_g_gs = None

    return studij_options, smjer_options, godina_options, selected_studij, selected_smjer, selected_godina, smjer_options_gs, godina_options_gs, selected_sm_gs, selected_g_gs

@app.callback(
    Output('dropdown-smjer', 'options', allow_duplicate=True),  # ✅ Omogućava dupli output
    Output('dropdown-smjer', 'value', allow_duplicate=True),
    Input('dropdown-studij', 'value'),
    State('dropdown-smjer', 'value'),
    prevent_initial_call=True  # ⚠️ Mora biti postavljeno na True
)
def update_smjer_dropdown(selected_studij,selected_smjer):
    if not selected_studij:
        raise PreventUpdate  # ⛔ Sprječava prazno ažuriranje

    filtered_df = df[df['studij_naziv'] == selected_studij]
    smjer_options = [{'label': smjer, 'value': smjer} for smjer in sorted(filtered_df['smjer_naziv'].unique())]

    # Ako prethodno odabrani smjer postoji u novim opcijama, zadrži ga
    if selected_smjer in [s["value"] for s in smjer_options]:
        return smjer_options, selected_smjer
    
    return smjer_options, None
######

@app.callback(
    Output("graf-studenti-status", "figure"),
    Output("graf-studenti-nacin", "figure"),
    Output("graf-studenti-spol", "figure"),
    Output("graf-studenti-zavrseno", "figure"),
    Output("total-students", "children"),
    [Input("dropdown-studij", "value"),
     Input("dropdown-smjer", "value"),
     Input("dropdown-godina", "value"),
     Input('akademska-godina-dropdown','value'),]
)
def update_student_graphs(selected_studij, selected_smjer, selected_godina,selected_akgodina):
    """Generira tri tortna grafikona:
    1. Broj studenata po statusu (U, P, M)
    2. Broj redovnih i izvanrednih studenata
    3. Broj muških i ženskih studenata
    4. Broj ispis, diplomirao, mobilnost
    """
    akademska_godina = selected_akgodina

    df = get_student_data(akademska_godina)

    # Primjena filtera
    if selected_studij:
        df = df[df["studij_naziv"] == selected_studij]
    if selected_smjer:
        df = df[df["smjer_naziv"] == selected_smjer]
    if selected_godina:
        df = df[df["godina"] == selected_godina]

    # Makni duplikate po OIB-u
    df = df.drop_duplicates(subset=["oib", "studij_naziv"])
    
    total_students = len(df)

    # Ako nema podataka, vrati prazne grafikone s porukom
    if df.empty:
        return px.pie(title="Nema podataka"), px.pie(title="Nema podataka"), px.pie(title="Nema podataka"), px.pie(title="Nema podataka"), f"{total_students} studenata"

    ### 🔹 1. Tortni grafikon - Broj studenata po statusu
    status_counts = df["status_semestra"].value_counts().reset_index()
    status_counts.columns = ["status", "broj_studenata"]
    status_labels = {"U": "Redovni", "P": "Ponavljači", "M": "Mirovanje"}
    status_counts["status"] = status_counts["status"].map(status_labels)

    fig_status = px.pie(
        status_counts, names="status", values="broj_studenata",
        title="Broj studenata po statusu",
        color="status",
        color_discrete_map={"Redovni": "#1f77b4", "Ponavljači": "#ff7f0e", "Mirovanje": "#2ca02c"},
        hole=0.4
    )
    fig_status.update_traces(textinfo="label+percent+value",textfont_size=16, pull=[0.1] * len(status_counts),textposition="outside",marker=dict(line=dict(color='#000000', width=2)))

    ### 🔹 2. Tortni grafikon - Broj redovnih i izvanrednih studenata
    nacin_counts = df["nacin"].value_counts().reset_index()
    nacin_counts.columns = ["nacin", "broj_studenata"]
    fig_nacin = px.pie(
        nacin_counts, names="nacin", values="broj_studenata",
        title="Redovni vs. Izvanredni",
        color="nacin",
        color_discrete_map={"Redovni": "#636EFA", "Izvanredni": "#EF553B"},
        hole=0.4,
    )
    fig_nacin.update_traces(textinfo="label+percent+value",textfont_size=16, pull=[0.1] * len(nacin_counts),textposition="outside",marker=dict(line=dict(color='#000000', width=2)))

    ### 🔹 3. Tortni grafikon - Broj muških i ženskih studenata
    spol_counts = df["spol"].value_counts().reset_index()
    spol_counts.columns = ["spol", "broj_studenata"]
    fig_spol = px.pie(
        spol_counts, names="spol", values="broj_studenata",
        title="Muški vs. Ženski",
        color="spol",
        color_discrete_map={"Muški": "#FFA07A", "Ženski": "#9400D3"},
        hole=0.4
    )
    fig_spol.update_traces(textinfo="label+percent+value",textfont_size=16, pull=[0.1] * len(spol_counts),textposition="outside",marker=dict(line=dict(color='#000000', width=2)))

    # Dodaj animaciju za glatkiji prijelaz
    fig_status.update_layout(transition_duration=500)
    fig_spol.update_layout(transition_duration=500)
    fig_nacin.update_layout(transition_duration=500)


    ### 🔹 4. Tortni grafikon - Broj diplomirali, ispisani, završena mobilnost
    lista_filter = ["diplomirala/o", "ispis", "završena mobilnost"]
    zavrseno_filter = df[df["status_studija"].isin(lista_filter)]
    zavrseno_counts = zavrseno_filter["status_studija"].value_counts().reset_index()
    zavrseno_counts.columns = ["zavrseno", "broj_studenata"]
    status_l = {
    "diplomirala/o": "Diplomirali",
    "ispis": "Ispisani",
    "završena mobilnost": "Završena mobilnost"
    }
    zavrseno_counts["zavrseno"] = zavrseno_counts["zavrseno"].map(status_l)
    fig_zavrseno = px.pie(
        zavrseno_counts, names="zavrseno", values="broj_studenata",
        title="Diplomirali / Ispisani / Završena mobilnost",
        color="zavrseno",
        color_discrete_map={"Diplomirali": "#3A25BE", "Ispisani": "#BE2556","Završena mobilnost":"#2ca02c"},
        hole=0.4
    )
    fig_zavrseno.update_traces(textinfo="label+value",textfont_size=16, pull=[0.1] * len(spol_counts),textposition="outside",marker=dict(line=dict(color='#000000', width=2)))

    return fig_status, fig_nacin, fig_spol, fig_zavrseno, f"{total_students} studenata"


### GS STUDENTI TABLICA
def get_gs_student_table(selected_smjer_gs, selected_godina_gs):
    """Generira tablicu sa studentima Goldsmiths programa sa ECTS podacima."""

    # 🔹 Filtriramo `df_GS_akd` prema odabranom smjeru i godini
    df_filtered = df_GS_akd[
        (df_GS_akd["smjer_naziv"] == selected_smjer_gs) &
        (df_GS_akd["godina"] == selected_godina_gs)
    ]
    
    # Ako nema podataka, vraćamo prazan DataFrame
    if df_filtered.empty:
        return pd.DataFrame(columns=["prezime", "ime", "jmbag", "smjer_naziv", "student_tip", 
                                     "ECTS zimski", "ECTS zimski P", "ECTS ljetni", "ECTS ljetni P"])

    # 🔹 Dohvat kolegija studenata iz `dbo.analytics_final_studentipredmeti`
    jmbags = tuple(df_filtered["jmbag"].unique())  # Pretvaramo u tuple za SQL IN ()

    query_kolegiji = """
        SELECT jmbag, kolegij_sifra, semestar, priznat_ponavlja, akademska_godina
        FROM dbo.analytics_final_studentipredmeti
        WHERE jmbag IN %s AND akademska_godina = %s
    """
    params = (jmbags, akademska_godina)  # Pravilno definiranje parametara
    df_kolegiji = fetch_data_from_db(query_kolegiji,params=params)

    # 🔹 Dohvat ECTS bodova za kolegije iz `dbo.analytics_vss_predmeti`
    query_ects = """
        SELECT sifra, ects
        FROM dbo.analytics_vss_predmeti
    """
    df_ects = fetch_data_from_db(query_ects)

    # 🔹 Spajamo kolegije sa ECTS podacima
    df_kolegiji = df_kolegiji.merge(df_ects, left_on="kolegij_sifra", right_on="sifra", how="left")

    # 🔹 Grupiramo podatke po studentima i računamo ECTS bodove
    df_ects_agg = df_kolegiji.groupby("jmbag").agg(
        ects_zimski=pd.NamedAgg(column="ects", aggfunc=lambda x: x[
            (df_kolegiji["semestar"] == "Zimski semestar") & (df_kolegiji["priznat_ponavlja"] != "Ponavlja")].sum()),
        ects_zimski_p=pd.NamedAgg(column="ects", aggfunc=lambda x: x[
            (df_kolegiji["semestar"] == "Zimski semestar") & (df_kolegiji["priznat_ponavlja"] == "Ponavlja")].sum()),
        ects_ljetni=pd.NamedAgg(column="ects", aggfunc=lambda x: x[
            (df_kolegiji["semestar"] == "Ljetni semestar") & (df_kolegiji["priznat_ponavlja"] != "Ponavlja") ].sum()),
        ects_ljetni_p=pd.NamedAgg(column="ects", aggfunc=lambda x: x[
            (df_kolegiji["semestar"] == "Ljetni semestar") & (df_kolegiji["priznat_ponavlja"] == "Ponavlja")].sum())
    ).reset_index()

    # 🔹 Spajamo podatke sa filtriranim studentima
    df_final = df_filtered.merge(df_ects_agg, on="jmbag", how="left").fillna(0)

    # 🔹 Odabiremo tražene stupce
    df_final = df_final[["prezime", "ime", "jmbag", "smjer_naziv", "student_tip", "status_studija", 
                         "ects_zimski", "ects_zimski_p", "ects_ljetni", "ects_ljetni_p"]]

    return df_final

@app.callback(
    Output("gs-student-table", "data"),
    Input("dropdown-smjer-gs", "value"),
    Input("dropdown-godina-gs", "value")
)
def update_gs_table(selected_smjer_gs, selected_godina_gs):
    if not selected_smjer_gs or not selected_godina_gs:
        raise PreventUpdate
    
    #print(selected_smjer_gs,selected_godina_gs)

    df_gs_table = get_gs_student_table(selected_smjer_gs, selected_godina_gs)
    return df_gs_table.to_dict("records")

if __name__ == '__main__':
    app.run_server(debug=True)
