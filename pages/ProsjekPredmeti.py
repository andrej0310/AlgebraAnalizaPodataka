import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Dash, no_update, callback_context
from dash.dependencies import Input, Output, State, MATCH
import requests
from io import BytesIO
from dash.exceptions import PreventUpdate
from dash import dash_table
from dash.dash_table.Format import Group
import os
from baza import fetch_data_from_db, akademske_godine
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
from scipy.stats import norm
import io
import dash_daq as daq
from komponente import offcanvas_sadrzaj_info, offcanvas_sadrzaj_tabs




dash.register_page(__name__, path="/ProsjekPredmeti")  # ✅ Ispravno


#Dohvaćanje akademksih godina
df_akademske, akademska_godina = akademske_godine()
df = pd.DataFrame()
df_grouped = pd.DataFrame()
all_options = [] #get_popis_kolegija(akademska_godina)


def get_grupna_analiza(k1, k2, k3=None, k4=None):
    if k3 is None and k4 is None:
        query = """
        SELECT kolegij_naziv, kolegij_sifra, akademska_godina, student, jmbag, priznat_ponavlja, ocjena, predavanja_dolaznost, vjezbe_dolaznost, potpis, potpis_datum, student_tip
        from dbo.analytics_final_studentipredmeti
        WHERE kolegij_sifra IN (%s,%s)
        """
        params = (k1,k2)

    elif k3 is not None and k4 is None:
        query = """
        SELECT kolegij_naziv, kolegij_sifra, akademska_godina, student, jmbag, priznat_ponavlja, ocjena, predavanja_dolaznost, vjezbe_dolaznost, potpis, potpis_datum, student_tip
        from dbo.analytics_final_studentipredmeti
        WHERE kolegij_sifra IN (%s,%s,%s)
        """
        params = (k1,k2,k3)

    elif k3 is not None and k4 is not None:
        query = """
        SELECT kolegij_naziv, kolegij_sifra, akademska_godina, student, jmbag, priznat_ponavlja, ocjena, predavanja_dolaznost, vjezbe_dolaznost, potpis, potpis_datum, student_tip
        from dbo.analytics_final_studentipredmeti
        WHERE kolegij_sifra IN (%s,%s,%s,%s)
        """
        params = (k1,k2,k3,k4)
    else:
        query = """
        SELECT kolegij_naziv, kolegij_sifra, akademska_godina, student, jmbag, priznat_ponavlja, ocjena, predavanja_dolaznost, vjezbe_dolaznost, potpis, potpis_datum, student_tip
        from dbo.analytics_final_studentipredmeti
        WHERE kolegij_sifra IN (%s,%s)
        """
        params = ('00-00-000','00-00-000')

    df = fetch_data_from_db(query, params=params)
    return df

def get_padajuci_data(akademska_godina):

    query = """
        SELECT DISTINCT studij, smjer,skolska_godina 
        from dbo.analytics_final_studentipredmeti
        WHERE akademska_godina = %s
    """
    df = fetch_data_from_db(query, params=[akademska_godina])

    return df

df_padajuci = pd.DataFrame()

def get_students_data(akademska_godina):
    
    ak = akademska_godina

    params = (ak,'%dodatna nastava%')
    query = """
        SELECT * FROM dbo.analytics_final_studentipredmeti WHERE akademska_godina = %s AND kolegij_naziv NOT LIKE %s
    """
    df = fetch_data_from_db(query, params=params)

    
    # 🔹 Osvježavanje df_grouped
    df_total = df.groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
    df_total.rename(columns={'ocjena': 'broj_studenata'}, inplace=True)

    df_passed = df[df["ocjena"] > 1].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
    df_passed.rename(columns={'ocjena': 'broj_studenata_prosli'}, inplace=True)

    df_avg = df[df["ocjena"] > 1].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].mean().reset_index()
    df_avg.rename(columns={'ocjena': 'prosjek_ocjena'}, inplace=True)

    df_ponavljaci_total = df[df["priznat_ponavlja"] == "Ponavlja"].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
    df_ponavljaci_total.rename(columns={'ocjena': 'broj_ponavljaca'}, inplace=True)

    df_ponavljaci_passed = df[(df["ocjena"] > 1) & (df["priznat_ponavlja"] == "Ponavlja")].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
    df_ponavljaci_passed.rename(columns={'ocjena': 'broj_ponavljaca_prosli'}, inplace=True)


    df_priznati_total = df[df["priznat_ponavlja"] == "Priznat"].groupby(["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"])['ocjena'].count().reset_index()
    df_priznati_total.rename(columns={'ocjena': 'broj_priznatih'}, inplace=True)

  
    # Spajanje podataka
    df_grouped = df_total.merge(df_passed, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
    df_grouped = df_grouped.merge(df_avg, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
    df_grouped = df_grouped.merge(df_ponavljaci_total, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
    df_grouped = df_grouped.merge(df_ponavljaci_passed, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
    df_grouped = df_grouped.merge(df_priznati_total, on=["kolegij_naziv", "smjer", "skolska_godina", "studij", "kolegij_sifra"], how="left")
    df_semestar = df[['kolegij_sifra', 'semestar']].drop_duplicates()  # Makni duplikate
    df_grouped = df_grouped.merge(df_semestar, on='kolegij_sifra', how='left')

    df_grouped.fillna(0, inplace=True)

    df_grouped["prolaznost"] = (df_grouped["broj_studenata_prosli"] / df_grouped["broj_studenata"]) * 100
    df_grouped["prolaznost_ponavljaca"] = (df_grouped["broj_ponavljaca_prosli"] / df_grouped["broj_ponavljaca"]) * 100

    df_grouped["kolegij_full"] = df_grouped["kolegij_naziv"] + " (" + df_grouped["kolegij_sifra"].astype(str) + ")"

    return df_grouped

# Funkcija za dohvat prethodne akademske godine
def get_previous_years(current_year, df, steps=1):
    """Vraća akademsku godinu koja je `steps` mjesta prije `current_year`."""
    godine_lista = df["naziv"].tolist()
    if current_year in godine_lista:
        index = godine_lista.index(current_year)
        return godine_lista[index - steps] if index >= steps else current_year  # Ako nema dovoljno godina unazad, vraća istu
    return current_year


app = dash.get_app()
#server = app.server  # Ovo je potrebno za Render!


#TAB-A
tabA_content = html.Div(style={'background-color': '#F4F4F4', 'padding': '20px'}, children=[
        # Header naslovom
    html.Div([
        html.Hr(className="custom-line"),
        html.H2("Prosječne ocjene i prolaznost (studij, smjer i godina)")
    ]),

    # Dropdown filteri
    html.Div([
        html.Label("Studij:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id='studij_dropdown', 
                     options=[],
                     placeholder="Odaberi studij",
                     #value=sorted(df_grouped['studij'].unique()),
                     style={'font-size': '14px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown"),

        html.Label("Smjer:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id='smjer_dropdown', 
                     options=[],
                     placeholder="Odaberi smjer",
                     style={'font-size': '14px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown"),

        html.Label("Školska godina:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id='godina_dropdown', 
                     options=[{'label': 'Sve', 'value': 'Sve'}] + [],
                     placeholder="Odaberi školsku godinu",
                     #value='Sve',
                     style={'font-size': '14px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                     className="my-dropdown")
    ], style={'display': 'flex', 'justify-content': 'center',  "align-items": "center", "width": "100%"}),
    
    dcc.Loading(
        id="loading-container-1",
        type="circle",  # Može biti "default", "circle" ili "dot"
        children=[
            html.Div([
                # Grafovi
                dcc.Graph(id='graf', style={'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}),
                dcc.Graph(id='prolaznost_graf', style={'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}),
                dcc.Graph(id='prolaznost_ponavljaci_graf', style={'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'})
            ],style={'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center','width': '60%', 'margin':'auto', 'gap':'15px'})
        ]
    )
])

#TAB-B
tabB_content = html.Div(style={'background-color': '#F4F4F4', 'padding': '20px'}, children=[
    html.Div([
        html.Hr(className="custom-line"),
        html.H3("Broj studenata koji nisu položili kolegij", className="table-title"),
        
         # Dropdown filteri
        html.Div([
            html.Label("Studij:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
            dcc.Dropdown(id='studij_dropdown-n', 
                        options=[],
                        placeholder="Odaberi studij",
                        #value=sorted(df_grouped['studij'].unique()),
                        style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                        className="my-dropdown"),

            html.Label("Smjer:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
            dcc.Dropdown(id='smjer_dropdown-n', 
                        options=[],
                        placeholder="Odaberi smjer",
                        style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                        className="my-dropdown"),

            html.Label("Školska godina:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
            dcc.Dropdown(id='godina_dropdown-n', 
                        options=[{'label': 'Sve', 'value': 'Sve'}] + [],
                        placeholder="Odaberi školsku godinu",
                        #value='Sve',
                        style={'font-size': '18px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                        className="my-dropdown")
        ], style={'display': 'flex', 'justify-content': 'center',  "align-items": "center", "width": "100%"}),


        dash_table.DataTable(
            id="pivot-tablica-nepolozeni",
            style_table={'overflowX': 'auto'},

            # ✅ Stilizacija zaglavlja tablice
            style_header={
                'backgroundColor': '#be1e67',  # Roza zaglavlje
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'border': '1px solid #ddd'
            },

            # ✅ Stilizacija ćelija podataka
            style_data={
                'textAlign': 'center',
                'padding': '8px',
                'border': '1px solid #ddd'
            },

            # ✅ Dodaj CSS pravila kako bi omogućili hover efekt
            css=[
                {"selector": "tbody tr:hover td", "rule": "background-color: #dd6519 !important; color: white !important;"},
                {"selector": ".dash-spreadsheet", "rule": "border-collapse: collapse !important;"}
            ]
        )
    ]),

    #Preuzimanje pivot excelice sa nepoloženima
    html.Div([
        html.Hr(className="custom-line"),
        html.Label("Preuzimanje Excel pivot tablice sa brojem studenata koji nisu položili, a imaju potpis (svi studiji):",
            className="excel-label"
        )
        ],className="excel-container"
    ),
   
   html.Div([
        html.Label("Filtriraj po semestru:", className="semester-label"),  # ✅ Dodana klasa

        dcc.Dropdown(
            id="filter_semestar",
            options=[
                {"label": "Zimski semestar", "value": "Zimski semestar"},
                {"label": "Ljetni semestar", "value": "Ljetni semestar"}
            ],
            placeholder="Odaberi semestar",
            clearable=True,
            className="semester-dropdown"  # ✅ Dodana klasa
        ),

        html.Button("📥 Preuzmi Excel", id="download-btn", n_clicks=0, className="excel-button"),  # ✅ Dodana klasa
        dcc.Download(id="download-excel")

        ], className="semester-filter-container"
    )
])

#TAB-C
tabC_content = html.Div(style={'background-color': '#F4F4F4', 'padding': '20px'}, children=[
        # Header naslovom
    html.Div([
        html.Hr(className="custom-line"),
        html.H2("Analiza kolegija", style={"text-align": "center"})
    ]),
    html.Div([
        html.Label("Semestar:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(id='semestar_dropdown-k', 
                    options=["Zimski semestar", "Ljetni semestar"],
                    placeholder="Odaberi semestar",
                    style={'font-size': '14px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                    className="my-dropdown"),
        
        html.Label("Kolegij:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
        dcc.Dropdown(
            id="dynamic-dropdown",
            options=[], #[{"label": option, "value": option} for option in all_options],
            placeholder="Odaberi ili počni tipkati...",
            multi=False,
            searchable=True,  # Omogućuje pretragu unutar dropdowna
            style={'font-size': '14px','width': '80%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
            className="my-dropdown"
        )
    ], style={'display': 'flex', 'justify-content': 'center', "align-items": "center", "width": "70%", 'margin':'auto'}),

    dcc.Loading(
        id="loading-container-1",
        type="circle",  # Može biti "default", "circle" ili "dot"
        children=[
            html.Div([    
                html.Div([
                    dbc.Card([
                        dbc.CardHeader("PODACI O KOLEGIJU",className="card-header"),
                        dbc.CardBody([
                            html.H5(id="broj-ukupno", className="card-title"),
                            html.H2(id="posto-prolaz", className="card-text"),
                            html.H2(id="kolegij-prosjek", className="card-text"),
                        ])
                    ], className="status-card", style={'width':'30%'}),
                ], style={'display': 'flex', 'justify-content': 'center',  "align-items": "center", "width": "100%",'margin':'15px'}
                ),
      
                html.Div(style={'display': 'flex', 'justify-content': 'center','gap':'15px','margin-bottom':'15px','height':'450px'}, 
                    children=[
                        dcc.Graph(id="priznat_ponavlja_graf", style={'width': '25%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}),
                        dcc.Graph(id="potpis_graf", style={'width': '25%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'})
                    ]
                ),
            ]),
            
            html.Div([    
                html.Hr(className="custom-line"),
                html.Div([
                    html.Label("Korelacija dolaznosti na predavanja/vježbe sa ocjenama"),
                    html.Button(
                        html.Img(src="/assets/Info_ikona_2.png",id="info-icon"),
                    id="info-button"
                    ),
                    dbc.Offcanvas(
                        id="offcanvas-info",
                        title="📊 Objašnjenje",
                        is_open=False,
                        placement="start",
                        scrollable=True,
                        backdrop=True,
                        children=offcanvas_sadrzaj_info()
                    )
                ],style={'display': 'flex', "gap":"20px", 'justify-content': 'center'})
            ],className="graph-naslov"
            ),    
            html.Div(style={'display': 'flex', 'justify-content': 'center','gap':'15px','margin-bottom':'15px','height':'520px'}, 
                children=[
                    dcc.Graph(id="boxplot-predavanja", style={'width': '35%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}),
                    dcc.Graph(id="boxplot-vjezbe", style={'width': '35%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'})
                ]
            ),

            html.Div([    
                html.Label("Distribucija ocjena na kolegiju")
                ],className="graph-naslov"
            ),
            html.Div([  
                dcc.Graph(id="graf-kolegij-ocjene", className="distribution-graph", style={'width':'60%','border': '2px solid black'})
            ], style={'display': 'flex', 'margin':'auto','gap':'15px','height':'400px'})
        ]    
    ),
    
    # Usporedba više kolegija
    html.Div([
        html.Hr(className="custom-line"),
        html.Label("Analiza usporedbe više kolegija")
        ],className="graph-naslov"
    ),
    html.Div([
        html.Div([
            html.Label("Kolegij 1:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}), 
            dcc.Dropdown(id='k1-akademska', 
                    options=[],
                    value  = None,
                    placeholder="Odaberi akademsku",
                    style={'font-size': '14px','width': '90%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                    className="my-dropdown-1"),
            dcc.Dropdown(
                id="k1-dropdown",
                options=[], 
                placeholder="Kolegij - Odaberi ili počni tipkati...",
                multi=False,
                searchable=True,  # Omogućuje pretragu unutar dropdowna
                style={'font-size': '14px','width': '90%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                className="my-dropdown-2"
            )
        ], style={'display': 'flex', 'gap':'15px', 'justify-content': 'center'}),
        html.Div([
            html.Label("Kolegij 2:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
            dcc.Dropdown(id='k2-akademska', 
                    options=[],
                    value  = None,
                    clearable=False,
                    placeholder="Odaberi akademsku",
                    style={'font-size': '14px','width': '90%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                    className="my-dropdown-1"),
            dcc.Dropdown(
                id="k2-dropdown",
                options=[],
                value = None, 
                placeholder="Kolegij - Odaberi ili počni tipkati...",
                multi=False,
                searchable=True,  # Omogućuje pretragu unutar dropdowna
                style={'font-size': '14px','width': '90%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                className="my-dropdown-2"
            )
        ],style={'display': 'flex', 'gap':'15px', 'justify-content': 'center'}),
        html.Div([
            html.Label("Kolegij 3:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
            dcc.Dropdown(id='k3-akademska', 
                options=[],
                value  = None,
                clearable=False,
                placeholder="Odaberi akademsku",
                style={'font-size': '14px','width': '90%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                className="my-dropdown-1"),
            dcc.Dropdown(
                id="k3-dropdown",
                options=[], 
                placeholder="Kolegij - Odaberi ili počni tipkati...",
                multi=False,
                searchable=True,  # Omogućuje pretragu unutar dropdowna
                style={'font-size': '14px','width': '90%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                className="my-dropdown-2"
            )
        ],style={'display': 'flex', 'gap':'15px', 'justify-content': 'center'}),
        html.Div([
            html.Label("Kolegij 4:", style={'display': 'flex', 'align-items': 'center','font-size': '20px', 'font-weight': 'bold'}),
            dcc.Dropdown(id='k4-akademska', 
                options=[],
                value  = None,
                clearable=False,
                placeholder="Odaberi akademsku",
                style={'font-size': '14px','width': '90%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                className="my-dropdown-1"),
            dcc.Dropdown(
                id="k4-dropdown",
                options=[], 
                placeholder="Kolegij - Odaberi ili počni tipkati...",
                multi=False,
                searchable=True,  # Omogućuje pretragu unutar dropdowna
                style={'font-size': '14px','width': '90%', 'margin': '12px', 'backgroundColor': '#ffffff', 'color': '#000000'},
                className="my-dropdown-2"
            )
        ],style={'display': 'flex', 'gap':'15px', 'justify-content': 'center'}),
    ], style={'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center','width': '70%', 'margin':'auto', 'gap':'5px'}
    ),
    html.Div([
        html.Button("Prikaži analizu", id="generate-graphs", n_clicks=0, disabled=True)
    ], style={'display': 'flex', 'gap':'15px', 'justify-content': 'center', 'margin-top': '20px', 'margin-bottom': '20px' }),

    dcc.Loading(
        id="loading-container-2",
        type="circle",  # Može biti "default", "circle" ili "dot"
        children=[
            html.Div([
                html.Div([
                        daq.BooleanSwitch(
                            id="switch-bar",
                            on=True,
                            label="Prikaži stupce",
                            labelPosition="top",
                            color="#be1e67",  
                            style={"fontWeight": "bold", "fontSize": "16px"}
                        )
                    ]),

                    html.Div([
                        daq.BooleanSwitch(
                            id="switch-trend",
                            on=True,
                            label="Prikaži trend liniju",
                            labelPosition="top",
                            color="#be1e67",  
                            style={"fontWeight": "bold", "fontSize": "16px"}
                        )
                    ])
            ], style={"display": "flex", 'justify-content': 'center', "width":"15%", "gap": "30px", "margin-bottom": "30px", 'margin-left':'15%', 'border': '2px solid black','padding': '10px', 'border-radius': '8px'}),
            
            html.Div([
                dcc.Graph(id="graf-prosjecne-ocjene", 
                    className="graf-grupna",
                    style={'width': '35%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}),
                dcc.Graph(id="graf-prolaznost", 
                    className="graf-grupna",
                    style={'width': '35%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}),
            ], style={'display': 'flex', 'justify-content': 'center','gap':'15px','margin-bottom':'15px','height':'520px'}),
            html.Div([
                dcc.Graph(id="graf-upisani", 
                          className="graf-grupna",
                          style={'width': '35%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}),
                dcc.Graph(id="graf-ponavljaci", 
                          className="graf-grupna",
                          style={'width': '35%', 'border': '2px solid black', 'padding': '10px', 'border-radius': '8px'}),
            ], style={'display': 'flex', 'justify-content': 'center','gap':'15px','margin-bottom':'15px','height':'520px'})
        ]
     )
])

tabs = html.Div([
    dbc.Tabs(
        [
            dbc.Tab(label="Prosjek i Prolaznost", tab_id="tab-A"),
            dbc.Tab(label="Ne položeni", tab_id="tab-B"),
            dbc.Tab(label="Analiza kolegija", tab_id="tab-C")
        ],
        id="tabs-stranica1",
        active_tab="tab-A",  # Prvi tab je inicijalno aktivan
        className="nav-tabs mt-3"
    ),
    html.Div(id="content-stranica1")  # Ovdje će se prikazivati sadržaj odabranog taba
])

# **Layout aplikacije**
layout = dbc.Container([
    
    dcc.Store(id="kolegij-data"),
    dcc.Store(id="k1-selected-value"),  # ✅ Store za držanje odabrane vrijednosti
    
    html.Div([
        html.H1("Kolegij - Prosječne ocjene i prolaznost", style={"text-align": "center"}),    
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

# **Callback funkcija za prebacivanje sadržaja u tabovima**
@app.callback(
        Output("content-stranica1", "children"), 
        [Input("tabs-stranica1", "active_tab")]
)
def switch_tab(at):
    if at == "tab-A":
        return tabA_content
    elif at == "tab-B":
        return tabB_content
    elif at == "tab-C":
        return tabC_content
    return html.P("Ovo ne bi trebalo biti prikazano...")



 ####  TAB A #######

@app.callback(
    [Output('smjer_dropdown', 'options'),
    Output('godina_dropdown', 'options'),
    Output('smjer_dropdown', 'value'),
    Output('godina_dropdown', 'value')],
    Input('studij_dropdown', 'value')
)
def update_smjer_godina_dropdown(selected_studij):
    if not selected_studij:
        return [], [], None, None


    df_padajuci_filtred =  df_padajuci[df_padajuci["studij"] == selected_studij]
    smjer_options = [{'label': smjer, 'value': smjer} for smjer in sorted(df_padajuci_filtred['smjer'].unique())]
    godina_options = [{'label': godina, 'value': godina} for godina in sorted(df_padajuci_filtred['skolska_godina'].unique())]

    return smjer_options, godina_options, None, None

#padajući
@app.callback(
    [Output('studij_dropdown', 'options'),
    Output('studij_dropdown', 'value')],
    [Input("url", "pathname"),
    Input('akademska-godina-dropdown','value')]
)
def update_data(pathname, selected_akgodina):
           
    global df_padajuci
    df_padajuci = get_padajuci_data(selected_akgodina)    

    if df_padajuci.empty:
        return [], None
    
    # 🔹 Ažuriranje dropdown opcija
    studiji_options = [{'label': s, 'value': s} for s in sorted(df_padajuci['studij'].unique())]
    
    return studiji_options, None

@app.callback(
    Output('graf', 'figure'),
     Output('prolaznost_graf', 'figure'),
     Output('prolaznost_ponavljaci_graf', 'figure'),
    [
     Input('godina_dropdown', 'value'),
     State('akademska-godina-dropdown','value'),
     State('studij_dropdown', 'value'),
     State('smjer_dropdown', 'value'),
    ]
)
def update_graph(selected_godina, slected_akgodina, selected_studij, selected_smjer):
    
    if not selected_godina or not selected_studij or not selected_smjer:
        fig1 = go.Figure()
        fig2 = go.Figure()
        fig3 = go.Figure()
        fig1.update_layout(title="Nema dostupnih podataka", height=300)
        fig2.update_layout(title="Nema dostupnih podataka", height=300)
        fig3.update_layout(title="Nema dostupnih podataka", height=300)

        return fig1, fig2, fig3


    global df_grouped

    akademska_godina = slected_akgodina
    df_grouped = get_students_data(akademska_godina)
    
    filtered_df = df_grouped[
        (df_grouped['studij'] == selected_studij) &
        (df_grouped['smjer'] == selected_smjer if selected_smjer else True) &
        ((df_grouped['skolska_godina'] == selected_godina) if selected_godina != 'Sve' else True)
    ]

    num_kolegija = len(filtered_df)
    height = 300 + num_kolegija * 30

     # 🔹 Definiraj prilagođene boje za semestar
    semestar_colors = {"Zimski semestar": "#1f77b4", "Ljetni semestar": "#ff7f0e"}  # Plava za zimski, narančasta za ljetni


    fig1 = px.bar(filtered_df,
                  x="prosjek_ocjena",
                  y="kolegij_full",
                  orientation="h",
                  title="Prosječna ocjena po kolegiju",
                  text=filtered_df["prosjek_ocjena"].round(2),
                  hover_data={"broj_studenata": True, "broj_studenata_prosli":True, "broj_ponavljaca": True, "broj_priznatih": True},
                  color="semestar",  # 🔹 Dodana boja prema semestru
                  color_discrete_map=semestar_colors,  # Prilagođene boje
    )
    fig2 = px.bar(filtered_df,
                  x="prolaznost",
                  y="kolegij_full",
                  orientation="h",
                  title="Prolaznost po kolegiju (%)",
                  text=filtered_df["prolaznost"].round(2),
                  hover_data={"broj_studenata": True, "broj_studenata_prosli":True},
                  color="semestar",  # 🔹 Dodana boja prema semestru
                  color_discrete_map=semestar_colors,  # Prilagođene boje
    )
    fig3 = px.bar(filtered_df,
                  x="prolaznost_ponavljaca",
                  y="kolegij_full",
                  orientation="h",
                  title="Prolaznost ponavljača (%)",
                  text=filtered_df["prolaznost_ponavljaca"].round(2),
                  hover_data={"broj_ponavljaca": True, "broj_ponavljaca_prosli":True},
                  color="semestar",  # 🔹 Dodana boja prema semestru
                  color_discrete_map=semestar_colors,  # Prilagođene boje
    )

    for fig in [fig1, fig2, fig3]:
        fig.update_traces(marker=dict(line=dict(width=2)), textposition='outside', textfont_size=12)
        fig.update_layout(yaxis_title="Naziv kolegija (Šifra)", 
                          height=height,
                          title={
                                "font": {
                                "family": "Arial",
                                "size": 30,
                                "color": "darkblue",
                                "weight": "bold"
                                },
                                "x": 0.5,
                                "xanchor": "center"
    })

    fig1.update_layout(xaxis_title="Prosječna ocjena")
    fig2.update_layout(xaxis_title="Prolaznost (%)")
    fig3.update_layout(xaxis_title="Prolaznost ponavljača (%)")

    return fig1, fig2, fig3


#####  TAB B ##########

#Tab2 - Dropdown
@app.callback(
    [Output('smjer_dropdown-n', 'options'),
    Output('godina_dropdown-n', 'options'),
    Output('smjer_dropdown-n', 'value'),
    Output('godina_dropdown-n', 'value')],
    Input('studij_dropdown-n', 'value')
)
def update_smjer_godina_dropdown(selected_studij):
    if not selected_studij:
        return [], [], None, None


    df_padajuci_filtred =  df_padajuci[df_padajuci["studij"] == selected_studij]
    smjer_options = [{'label': smjer, 'value': smjer} for smjer in sorted(df_padajuci_filtred['smjer'].unique())]
    godina_options = [{'label': godina, 'value': godina} for godina in sorted(df_padajuci_filtred['skolska_godina'].unique())]

    return smjer_options, godina_options, None, None


@app.callback(
    [Output('studij_dropdown-n', 'options'),
    Output('studij_dropdown-n', 'value')],
    Input('akademska-godina-dropdown','value')
)
def update_data(selected_akgodina):
           
    global df_padajuci
    df_padajuci = get_padajuci_data(selected_akgodina)    

    if df_padajuci.empty:
        return [], None   
    
    # 🔹 Ažuriranje dropdown opcija
    studiji_options = [{'label': s, 'value': s} for s in sorted(df_padajuci['studij'].unique())]
    
    return studiji_options, None


#### PIVOT ###
def get_students_pivot(akademska_godina):
    
    ak = akademska_godina

    query = """
        SELECT kolegij_naziv, kolegij_sifra, studij, smjer, skolska_godina, ocjena, potpis, semestar, grupa 
        FROM dbo.analytics_final_studentipredmeti WHERE akademska_godina = %s
    """
    df = fetch_data_from_db(query, params=[ak])

    return df

@app.callback(
    Output("pivot-tablica-nepolozeni", "columns"),
    Output("pivot-tablica-nepolozeni", "data"),
    [
        Input("studij_dropdown-n", "value"),
        Input("smjer_dropdown-n", "value"),
        Input("godina_dropdown-n", "value"),
        State('akademska-godina-dropdown','value')
    ]
)
def update_pivot_table(s_studij, s_smjer, s_godina, s_akgodina):
    # Filtriranje podataka prema odabranim kriterijima
    
    if not s_studij or not s_smjer or not s_godina:
        return [], []

    df_pivot = get_students_pivot(s_akgodina)
    
    filtered_df = df_pivot[
        (df_pivot["studij"] == s_studij) &
        (df_pivot["smjer"] == s_smjer if s_smjer else True) &
        (df_pivot["skolska_godina"] == s_godina if s_godina != 'Sve' else True)
    ]

    # Filtriranje samo studenata koji nisu položili (ocjena = 0 i potpis = 1)
    df_failed = filtered_df[(filtered_df["ocjena"] == 0) & (filtered_df["potpis"] == 1)].copy()

    # Dodavanje stupca s kombinacijom kolegij_naziv + kolegij_sifra
    df_failed["kolegij_full"] = df_failed["kolegij_naziv"] + " (" + df_failed["kolegij_sifra"].astype(str) + ")"

    # Grupiranje i pivotiranje podataka
    df_pivot = df_failed.groupby(["kolegij_full", "semestar", "grupa"])["ocjena"].count().reset_index()
    df_pivot_table = df_pivot.pivot(index=["kolegij_full", "semestar"], columns="grupa", values="ocjena").fillna(0)

    # Resetiranje indeksa za prikaz u Dash tablici
    df_pivot_table.reset_index(inplace=True)

    # **Sortiranje prema semestru** → Prvo "Zimski", zatim "Ljetni"
    df_pivot_table["semestar"] = pd.Categorical(df_pivot_table["semestar"], categories=["Zimski semestar", "Ljetni semestar"], ordered=True)
    df_pivot_table = df_pivot_table.sort_values(by="semestar")

    # Priprema podataka za prikaz u Dash tablici
    columns = [{"name": col, "id": col} for col in df_pivot_table.columns]
    data = df_pivot_table.to_dict("records")

    return columns, data


#GENERIRANJE PIVOT TABLICE SA NEPOLOŽENIMA - SVI STUDIJI TE AKADEMKSE
def get_student_data_pivot(akademska_godina):
    """ Dohvaća podatke iz SQL baze na temelju akademske godine. """
    
    ak = akademska_godina
    query = """
        SELECT kolegij_naziv, kolegij_sifra, jmbag, grupa, semestar
        FROM dbo.analytics_final_studentipredmeti
        WHERE akademska_godina = %s 
        AND ocjena = 0 AND potpis = 1
    """
    df = fetch_data_from_db(query, params=[ak])
    
    return df

def create_pivot_table(df,selected_semestar=None):
    """ Kreira pivot tablicu na temelju preuzetih podataka i filtrira po semestru. """

    # ✅ Ako je korisnik odabrao semestar, filtriraj podatke
    if selected_semestar:
        df = df[df["semestar"] == selected_semestar].copy()

    # ✅ Spajanje naziva kolegija i šifre u jedan stupac
    df["kolegij_full"] = df["kolegij_naziv"] + " (" + df["kolegij_sifra"].astype(str) + ")"

    # ✅ Kreiranje pivot tablice
    pivot_df = df.pivot_table(
        index=["kolegij_full"],  # Redovi -> Spojeni naziv i šifra kolegija
        columns=["grupa"],        # Stupci -> Grupe
        values="jmbag",           # Vrijednosti -> Brojanje JMBAG-a
        aggfunc="count"           # Brojanje broja JMBAG-a
    )

    return pivot_df

def save_pivot_to_excel(df_pivot):
    """ Sprema pivot tablicu u Excel i vraća putanju do datoteke. """
    
    file_path = "pivot_table.xlsx"

    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df_pivot.to_excel(writer, sheet_name="PivotTablica")

    return file_path

@app.callback(
    Output("download-excel", "data"),
    [Input("download-btn", "n_clicks"),
     State("filter_semestar", "value"),
     State("akademska-godina-dropdown", "value")],  # ✅ Dodan semestar filter
    prevent_initial_call=True
)
def generate_and_download_pivot(n_clicks, selected_semestar, selected_akgodina):
    if n_clicks is None:
        raise PreventUpdate  # ⛔ Sprječava callback ako nije kliknut gumb
    
    # ✅ Dohvati podatke iz SQL baze
    df = get_student_data_pivot(selected_akgodina)

    # ✅ Generiraj pivot tablicu s filtriranim semestrom
    df_pivot = create_pivot_table(df, selected_semestar)

    # ✅ Spremi pivot tablicu u Excel
    file_path = save_pivot_to_excel(df_pivot)

    # ✅ Omogući preuzimanje datoteke
    return dcc.send_file(file_path)


####### TAB C #########

def get_popis_kolegija(akademska_godina, semestar):
    query = """
        SELECT DISTINCT kolegij_naziv, kolegij_sifra
        FROM dbo.analytics_final_studentipredmeti
        WHERE akademska_godina = %s AND semestar = %s
    """
    params = (akademska_godina,semestar)
    df = fetch_data_from_db(query, params=params)
    
    return df

def get_popis_kolegija_all(akademska_godina):
    query = """
        SELECT DISTINCT kolegij_naziv, kolegij_sifra
        FROM dbo.analytics_final_studentipredmeti
        WHERE akademska_godina = %s
    """
    df = fetch_data_from_db(query, params=[akademska_godina])
    
    return df      


# ✅ Callback za filtriranje opcija u Dropdownu
@app.callback(
    Output("dynamic-dropdown", "options"),
    [Input("dynamic-dropdown", "search_value"),       # Dohvaća trenutno upisani tekst
     Input('akademska-godina-dropdown','value'),
     Input('semestar_dropdown-k', 'value')
    ]
)
def update_dropdown_options(search_value, ak_god_selected, semestar_selected):
    
    df_all_options = get_popis_kolegija(ak_god_selected, semestar_selected)

    all_options = sorted(
    [{"label": f"{naziv} ({sifra})", "value": sifra} for naziv, sifra in zip(df_all_options["kolegij_naziv"], df_all_options["kolegij_sifra"])],
    key=lambda x: x["label"]  # 🔹 Sortira prema labeli (kolegij_naziv)
    )

    # 🔹 Ako nema unesenog teksta, prikazujemo sve opcije
    if not search_value:
        return all_options

    # 🔹 Filtriranje opcija koje sadrže upisani tekst u nazivu ili šifri kolegija
    filtered_options = [
        option for option in all_options if search_value.lower() in option["label"].lower()
    ]

    return filtered_options


def get_ocjene_koelgij(sifra):
    query = """
        SELECT *
        from dbo.analytics_final_studentipredmeti
        WHERE kolegij_sifra = %s AND ocjena > 1
    """
    df = fetch_data_from_db(query, params=[sifra])
    
    return df 


@app.callback(
    [Output("kolegij-data", "data"),
     Output("k1-selected-value", "data")
    ],
    Input("dynamic-dropdown", "value")
)
def get_kolegij_data(slectded_kolegj):

    query = """
        SELECT *
        from dbo.analytics_final_studentipredmeti
        WHERE kolegij_sifra = %s
    """

    df_all = fetch_data_from_db(query, params=[slectded_kolegj])

    return df_all.to_json(date_format="iso", orient="split"), {"selected_k1": slectded_kolegj}


# Distribucija ocjena
@app.callback(
     Output("graf-kolegij-ocjene", "figure"),
     [Input("kolegij-data", "data"),
      State("dynamic-dropdown", "value")
     ]
)
def graf_distribucija_ocjena(data_json,selected_value):
    
    if not selected_value:
        fig = go.Figure()
        fig.update_layout(title="Nema dostupnih podataka", height=300)
        return fig

    df = get_ocjene_koelgij(selected_value)

    # 🔹 Definiranje mogućih ocjena i raspona za normalnu distribuciju
    ocjene_x = np.array([2, 3, 4, 5])
    x_smooth = np.linspace(1, 5, 300)  # ✅ Normalna distribucija sada ide od 1 do 5

    # 🔹 Postavljanje normalne distribucije s vrhom na 3
    mu = 3  # ✅ Sredina distribucije je sada 3
    sigma = df["ocjena"].std() if df["ocjena"].std() > 0 else 0.5  # ✅ Ako je sigma 0, koristimo 0.5 da izbjegnemo greške

    # 🔹 Generiranje normalne distribucije
    gauss_curve = norm.pdf(x_smooth, mu, sigma)

    # ✅ Skaliranje krivulje prema broju ocjena
    gauss_curve = gauss_curve * len(df) * (max(ocjene_x) - min(ocjene_x)) / 4

    # 🔹 Histogram stvarnih ocjena (prikazuje broj ocjena, ne gustoću)
    fig = px.histogram(df, x="ocjena", nbins=4, 
                       title="Distribucija ocjena i normalna raspodjela",
                       labels={"ocjena": "Ocjene", "count": "Broj ocjena"},
                       opacity=0.6,
                       category_orders={"ocjena": [2, 3, 4, 5]})

    # 🔹 Sužavanje i razmicanje plavih stupaca
    fig.update_traces(
        marker=dict(line=dict(width=1, color="black")),  # ✅ Dodaje obrub oko stupaca
        marker_color="blue",  # ✅ Boja stupaca
    )

    # 🔹 Normalna distribucija (crvena krivulja, glatka i s vrhom na 3)
    fig.add_trace(go.Scatter(x=x_smooth, y=gauss_curve, 
                             mode="lines", 
                             name=f"Normalna distribucija (μ=3, σ={sigma:.2f})",
                             line=dict(color="red", width=2)))

    # 🔹 Stilizacija x-osi (prikazuje samo moguće ocjene) i razmak stupaca
    fig.update_layout(
        xaxis=dict(tickmode="array", tickvals=[2, 3, 4, 5]),  # ✅ Prikazuje samo ocjene 2,3,4,5
        xaxis_title="Ocjene",
        yaxis_title="Broj ocjena",
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(x=0.7, y=1.1),
        font=dict(size=14),
        bargap=0.2,  # ✅ Razmak između stupaca
        bargroupgap=0.1  # ✅ Dodatni razmak između grupa stupaca
    )

    return fig

@app.callback(
    [Output("broj-ukupno", "children"),
    Output("posto-prolaz", "children"),
    Output("kolegij-prosjek", "children"),
    Output("priznat_ponavlja_graf", "figure"),
    Output("potpis_graf", "figure"),
    ],  
    Input("kolegij-data", "data")
)
def update_student_kartice(data_json):

    # Dekodiranje JSON-a natrag u DataFrame
    df_all = pd.read_json(io.StringIO(data_json), orient="split")

    #print(df_all.head(10))

    if df_all.empty:
        fig_1 = go.Figure()
        fig_2 = go.Figure()
        fig_1.update_layout(title="Nema dostupnih podataka", height=420)
        fig_2.update_layout(title="Nema dostupnih podataka", height=420)

        return "0", "0%", "0.0", fig_1, fig_2

    # Pretvaranje ocjena 0 u 1
    df_all["ocjena"] = df_all["ocjena"].replace(0, 1)

    # Izračuni
    ukupan_broj_studenata = len(df_all)
    prolaznost = (df_all[df_all["ocjena"] > 1].shape[0] / ukupan_broj_studenata) * 100
    prosjek_ocjena = df_all[df_all["ocjena"] > 1]["ocjena"].mean()

    # Priprema podataka za tortne grafikone
    df_priznat = df_all["priznat_ponavlja"].fillna("Prvi puta")  # Zamjenjujemo sve NaN vrijednosti s "Prvi puta"

    # Osiguravamo da su sve vrijednosti ispravno mapirane
    df_priznat = df_priznat.apply(lambda x: "Priznat" if x == "Priznat" else ("Ponavlja" if x == "Ponavlja" else "Prvi puta"))

    # Kreiranje DataFrame-a s brojem studenata po kategoriji
    priznat_counts = df_priznat.value_counts().reset_index()
    priznat_counts.columns = ["Status", "Broj studenata"]

    df_all["potpis_status"] = df_all["potpis_datum"].notna().replace({True: "Ima potpis", False: "Nema potpis"})
    potpis_counts = df_all["potpis_status"].value_counts().reset_index()
    potpis_counts.columns = ["Potpis", "Broj studenata"]

    # Dinamički izračun pull vrijednosti (razmaka segmenata)
    max_value = priznat_counts["Broj studenata"].max()  # Najveći broj studenata u bilo kojoj kategoriji
    priznat_counts["pull_value"] = 0.05 + (1 - priznat_counts["Broj studenata"] / max_value) * 0.1  # Dinamičan pull
    potpis_counts["pull_value"] = 0.05 + (1 - potpis_counts["Broj studenata"] / max_value) * 0.1  # Dinamičan pull


    # Prvi tortni grafikon - Priznat/Ponavlja
    fig_1 = px.pie(
        priznat_counts, 
        names="Status", 
        values="Broj studenata", 
        title="Omjer studenata po prvi puta/priznat/ponavlja",
        color="Status",
        color_discrete_map={"Prvi puta": "#1f77b4", "Ponavlja": "#ff7f0e", "Priznat": "#2ca02c"},
        hole=0.3
    )
    fig_1.update_traces(
        textinfo="label+percent+value",
        textfont_size=16, 
        pull=priznat_counts["pull_value"].tolist(),
        textposition="outside",
        marker=dict(line=dict(color='#000000', width=2))
    )
    # Pomicanje naslova prema gore
    fig_1.update_layout(
        title_x=0.5,  # Centriranje naslova
        title_y=0.95,  # Pomicanje naslova prema gore
        margin=dict(t=60, b=40)  # Dodavanje dodatnog prostora
    )

    # Drugi tortni grafikon - Potpis
    fig_2 = px.pie(
        potpis_counts, 
        names="Potpis", 
        values="Broj studenata", 
        title="Omjer studenata koji imaju potpis",
        color="Potpis",
        color_discrete_map={"Ima potpis": "#1f77b4", "Nema potpis": "#ff7f0e"},
        hole=0.3
    )
    fig_2.update_traces(
        textinfo="label+percent+value",
        textfont_size=16, 
        pull=potpis_counts["pull_value"].tolist(),
        textposition="outside",
        marker=dict(line=dict(color='#000000', width=2))
    )

    # Pomicanje naslova prema gore
    fig_2.update_layout(
        title_x=0.5,  # Centriranje naslova
        title_y=0.95,  # Pomicanje naslova prema gore
        margin=dict(t=60, b=40)  # Dodavanje dodatnog prostora
    )  

    return(
        f"Ukupno studenata: {ukupan_broj_studenata}",
        f"Prolaznost: {prolaznost:.2f}%",
        f"Prosječna ocjena: {prosjek_ocjena:.2f}",
        fig_1,
        fig_2,
    )

@app.callback(
    [Output("boxplot-predavanja", "figure"),
    Output("boxplot-vjezbe", "figure")
    ],  
    Input("kolegij-data", "data")
)
def update_korelacija(data_json):
    
    df = pd.read_json(io.StringIO(data_json), orient="split")
    df['ocjena'] = df['ocjena'].replace(0, 1)
    
    if df.empty:
        fig_3 = go.Figure()
        fig_4 = go.Figure()
        fig_3.update_layout(title="Nema dostupnih podataka", height=500)
        fig_4.update_layout(title="Nema dostupnih podataka", height=500)
        return fig_3, fig_4

    # Kopiranje DataFrame-a kako bismo izbjegli SettingWithCopyWarning
    df_filtered = df[(df['priznat_ponavlja'] != 'Priznat') & (df['priznat_ponavlja'] != 'Ponavlja')].copy()

    # Računanje podataka za predavanja
    bins_predavanja = [50, 55, 70, 85, 100]
    labels_predavanja = ["50-55%", "55-70%", "70-85%", "85-100%"]
    df_filtered['dolaznost_predavanja'] = pd.cut(df_filtered['predavanja_dolaznost'], bins=bins_predavanja, labels=labels_predavanja, include_lowest=True)

    group_counts_predavanja = df_filtered.groupby('dolaznost_predavanja', observed=False).size()
    group_above_1_predavanja = df_filtered[df_filtered['ocjena'] > 1].groupby('dolaznost_predavanja', observed=False).size()
    group_percent_above_1_predavanja = (group_above_1_predavanja / group_counts_predavanja * 100).fillna(0).round(1)

    # Računanje podataka za vježbe
    bins_vjezbe = [60, 70, 80, 90, 100]
    labels_vjezbe = ["60-70%", "70-80%", "80-90%", "90-100%"]
    df_filtered['dolaznost_vjezbe'] = pd.cut(df_filtered['vjezbe_dolaznost'], bins=bins_vjezbe, labels=labels_vjezbe, include_lowest=True)

    group_counts_vjezbe = df_filtered.groupby('dolaznost_vjezbe', observed=False).size()
    group_above_1_vjezbe = df_filtered[df_filtered['ocjena'] > 1].groupby('dolaznost_vjezbe', observed=False).size()
    group_percent_above_1_vjezbe = (group_above_1_vjezbe / group_counts_vjezbe * 100).fillna(0).round(1)

        # Definirane boje za svaku grupu
    boje = ['#E69F00', '#D55E00', '#CC79A7', '#0072B2']

    # Poboljšan izgled boxplotova za predavanja
    figure_predavanja = go.Figure()

    for i, label in enumerate(labels_predavanja):
        df_sub = df_filtered[df_filtered['dolaznost_predavanja'] == label]

        if df_sub.empty:
            # Dodajemo prazan boxplot kako bi se razred prikazao na grafu
            figure_predavanja.add_trace(go.Box(
                y=[None],  # None osigurava da je boxplot prazan
                name=label,
                marker=dict(color=boje[i], opacity=0.3),
                showlegend=False
            ))
        else:
            figure_predavanja.add_trace(go.Box(
                y=df_sub['ocjena'],
                name=label,
                marker=dict(color=boje[i], opacity=0.8),
                boxmean=True,
                width=0.5
            ))

    # Dodavanje oznaka N i postotka
    for i, label in enumerate(labels_predavanja):
        n_value = group_counts_predavanja.get(label, 0)  # Default na 0 ako nema podataka
        percent_value = group_percent_above_1_predavanja.get(label, "0%")  # Default na 0% ako nema podataka
        figure_predavanja.add_annotation(
            x=label, y=5.8,
            text=f"N={n_value}",
            showarrow=False,
            font=dict(size=14, color="black", family="Arial", weight="bold")
        )
        figure_predavanja.add_annotation(
            x=label, y=5.5,
            text=f"{percent_value} %",
            showarrow=False,
            font=dict(size=14, color="darkblue", family="Arial", weight="bold")
        )

    figure_predavanja.update_layout(
        title="Distribucija ocjena prema dolaznosti na predavanja (bez ponavljača)",
        yaxis=dict(gridcolor="lightgray", range=[0, 6], tickvals=[0, 1, 2, 3, 4, 5, 6]),
        boxmode='group'
    )

    # Poboljšan izgled boxplotova za vježbe
    figure_vjezbe = go.Figure()

    for i, label in enumerate(labels_vjezbe):
        df_sub = df_filtered[df_filtered['dolaznost_vjezbe'] == label]

        if df_sub.empty:
            # Dodajemo prazan boxplot kako bi se razred prikazao na grafu
            figure_vjezbe.add_trace(go.Box(
                y=[None],
                name=label,
                marker=dict(color=boje[i], opacity=0.3),
                showlegend=False
            ))
        else:
            figure_vjezbe.add_trace(go.Box(
                y=df_sub['ocjena'],
                name=label,
                marker=dict(color=boje[i], opacity=0.8),
                boxmean=True,
                width=0.5
            ))

    # Dodavanje oznaka N i postotka
    for i, label in enumerate(labels_vjezbe):
        n_value = group_counts_vjezbe.get(label, 0)
        percent_value = group_percent_above_1_vjezbe.get(label, "0%")
        figure_vjezbe.add_annotation(
            x=label, y=5.8,
            text=f"N={n_value}",
            showarrow=False,
            font=dict(size=14, color="black", family="Arial", weight="bold")
        )
        figure_vjezbe.add_annotation(
            x=label, y=5.5,
            text=f"{percent_value} %",
            showarrow=False,
            font=dict(size=14, color="darkblue", family="Arial", weight="bold")
        )

    figure_vjezbe.update_layout(
        title="Distribucija ocjena prema dolaznosti na vježbe (bez ponavljača)",
        yaxis=dict(gridcolor="lightgray", range=[0, 6], tickvals=[0, 1, 2, 3, 4, 5, 6]),
        boxmode='group'
    )

    return figure_predavanja, figure_vjezbe


#### Usporedba više kolegija ######
@app.callback(
    Output("k1-akademska", "options"),
    Output("k1-akademska", "value"),
    Input("akademska-godina-dropdown", "value"),
    Input("dynamic-dropdown", "value")
)
def update_primary_dropdowns(selected_year, slected_kolegij):
    """Ažurira opcije i početne vrijednosti za prvi dropdowna."""
    
    options = [{"label": godina, "value": godina} for godina in df_akademske["naziv"]]
    
    return options, selected_year

@app.callback(
    [Output("k2-akademska", "options"),
     Output("k3-akademska", "options"),
     Output("k4-akademska", "options"),
     Output("k2-akademska", "value"),
     Output("k3-akademska", "value"),
     Output("k4-akademska", "value")],
    Input("k1-akademska", "value")
)
def update_secondary_dropdowns(selected_year):
    """Ažurira opcije i početne vrijednosti za ostala tri dropdowna."""
    
    options = [{"label": godina, "value": godina} for godina in df_akademske["naziv"]]
    
    prev_year_1 = get_previous_years(selected_year, df_akademske, steps=1)
    prev_year_2 = get_previous_years(selected_year, df_akademske, steps=2)
    prev_year_3 = get_previous_years(selected_year, df_akademske, steps=3)

    return options, options, options, prev_year_1, prev_year_2, prev_year_3

@app.callback(
    [Output("k1-dropdown", "options"),
     Output("k1-dropdown", "value")],
    [Input("k1-dropdown", "search_value"),       
     Input('k1-akademska', 'value'),
     Input("k1-selected-value", "data")],  # Umjesto `dynamic-dropdown`, sada koristimo Store
    [State("k1-dropdown", "value")],
    prevent_initial_call=False  # ✅ Omogućava ažuriranje kod prvog pokretanja
)
def update_k1_dropdown_options(search_value, ak_god_selected, stored_data, current_value):
    df_all_options_1 = get_popis_kolegija_all(ak_god_selected)

    all_options_1 = sorted(
        [{"label": f"{naziv} ({sifra})", "value": sifra} for naziv, sifra in zip(df_all_options_1["kolegij_naziv"], df_all_options_1["kolegij_sifra"])],
        key=lambda x: x["label"]
    )

    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    # 🔹 Provjera postoji li spremljena vrijednost
    selected_k1 = stored_data["selected_k1"] if stored_data else None  

    print(f"Stored K1 value: {selected_k1}")  # ✅ Debugging

    # ✅ Provjeri postoji li `selected_k1` u opcijama prije postavljanja
    if selected_k1 and selected_k1 in [opt["value"] for opt in all_options_1]:
        print(f"Postavljam K1 na: {selected_k1}")
        return all_options_1, selected_k1  # ✅ Postavlja vrijednost samo ako postoji

    # 🔹 Ako nema unesenog teksta, prikaži sve opcije
    if not search_value:
        return all_options_1, current_value  

    # 🔹 Filtriranje opcija prema unesenom tekstu
    filtered_options = [
        option for option in all_options_1 if search_value.lower() in option["label"].lower()
    ]

    return filtered_options, current_value

@app.callback(
    [Output("k2-dropdown", "options"),
     Output("k2-dropdown", "value"),
     Output("k3-dropdown", "options"),
     Output("k3-dropdown", "value"),
     Output("k4-dropdown", "options"),
     Output("k4-dropdown", "value")],
    [Input("k1-dropdown", "value"),
     Input("k1-akademska", "value")],
    [State("k2-akademska", "value"),
     State("k3-akademska", "value"),
     State("k4-akademska", "value")
    ]
)
def update_k234_dropdowns(k1_selected, ak_god_selected,k2,k3,k4):
    
    df_all_options = get_popis_kolegija_all(ak_god_selected)
    df_all_options_2 = get_popis_kolegija_all(k2)
    df_all_options_3 = get_popis_kolegija_all(k3)
    df_all_options_4 = get_popis_kolegija_all(k4)

    all_options = sorted(
        [{"label": f"{naziv} ({sifra})", "value": sifra} for naziv, sifra in zip(df_all_options["kolegij_naziv"], df_all_options["kolegij_sifra"])],
        key=lambda x: x["label"]
    )

    all_options_2 = sorted(
        [{"label": f"{naziv} ({sifra})", "value": sifra} for naziv, sifra in zip(df_all_options_2["kolegij_naziv"], df_all_options_2["kolegij_sifra"])],
        key=lambda x: x["label"]
    )
    all_options_3 = sorted(
        [{"label": f"{naziv} ({sifra})", "value": sifra} for naziv, sifra in zip(df_all_options_3["kolegij_naziv"], df_all_options_3["kolegij_sifra"])],
        key=lambda x: x["label"]
    )
    all_options_4 = sorted(
        [{"label": f"{naziv} ({sifra})", "value": sifra} for naziv, sifra in zip(df_all_options_4["kolegij_naziv"], df_all_options_4["kolegij_sifra"])],
        key=lambda x: x["label"]
    )

    # Ako je K1 odabran, postavi isti kolegij u K2, K3 i K4 ako postoji
    if k1_selected:
        selected_k1_label = next((opt["label"].split(" (")[0] for opt in all_options if opt["value"] == k1_selected), None)

        matching_k2 = next((opt["value"] for opt in all_options_2 if opt["label"].split(" (")[0] == selected_k1_label), None)
        matching_k3 = next((opt["value"] for opt in all_options_3 if opt["label"].split(" (")[0] == selected_k1_label), None)
        matching_k4 = next((opt["value"] for opt in all_options_4 if opt["label"].split(" (")[0] == selected_k1_label), None)

        return all_options_2, matching_k2, all_options_3, matching_k3, all_options_4, matching_k4

    return all_options_2, None, all_options_3, None, all_options_4, None  # Ako nema K1, ostavi prazno


# Callback za aktivaciju gumba
@app.callback(
    Output("generate-graphs", "disabled"),
    [Input("k1-dropdown", "value"),
     Input("k2-dropdown", "value")]
)
def enable_button(k1_selected, k2_selected):
    """Gumb je aktivan samo ako su K1 i K2 odabrani."""
    return not (k1_selected and k2_selected)  # Ako oba imaju vrijednost, gumb je aktivan



### GRAFOVI ### 
def trend_percent(series):
    trend = [None]
    for i in range(1, len(series)):
        prev = series[i - 1]
        curr = series[i]
        if prev == 0:
            trend.append(None)
        else:
            trend.append(round(((curr - prev) / prev) * 100, 2))
    return trend

def create_trend_figure(bar_data, title, y_label, decimals=0, base_index=None, show_bar=True, show_trend=True):
    y_vals = bar_data.values
    x_vals = bar_data.index if base_index is None else base_index

    text_vals = [f"{v:.{decimals}f}" if decimals else str(v) for v in y_vals]
    trend_vals = trend_percent(y_vals)
    trend_texts = [f"{t}%" if t is not None else "" for t in trend_vals]

    fig = go.Figure()

    if show_bar:
        fig.add_bar(
            x=x_vals,
            y=y_vals,
            text=text_vals,
            textposition='auto',
            textfont=dict(size=16),
            marker=dict(color='rgba(0, 102, 255, 0.7)'),
            width=0.4,
            name=y_label
        )

    if show_trend:
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines+markers+text",
            text=trend_texts,
            textposition="top right",
            textfont=dict(size=16),
            name="Trend",
            line=dict(color="red"),
            yaxis="y2"
        ))

    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,  # centriraj naslov (opcionalno)
            'xanchor': 'center',
            'font': {
                'size': 20,
                'family': 'Arial Black',
                'color': 'black'
            }
        },
        xaxis_title="Šifra kolegija",
        yaxis=dict(title=y_label),
        yaxis2=dict(overlaying="y", side="right", showgrid=False, showticklabels=False),
        height=500,
        margin=dict(t=50, b=40)
    )

    return fig

# Callback za generiranje 4 odvojena grafa
@app.callback(
    [Output("graf-upisani", "figure"),
     Output("graf-ponavljaci", "figure"),
     Output("graf-prosjecne-ocjene", "figure"),
     Output("graf-prolaznost", "figure")
    ],
    [Input("generate-graphs", "n_clicks"),
    Input("k1-dropdown", "value"),
    Input("switch-bar", "on"),
    Input("switch-trend", "on")],
    [
     State("k2-dropdown", "value"),
     State("k3-dropdown", "value"),
     State("k4-dropdown", "value"),  
    ]
)
def generate_graphs(n_clicks, k1, show_bar, show_trend, k2,k3,k4):
    
    ctx = dash.callback_context
    triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""

    if n_clicks == 0 or triggered == "k1-dropdown":
        fig1 = go.Figure()
        fig2 = go.Figure()
        fig3 = go.Figure()
        fig4 = go.Figure()
        fig1.update_layout(title="Nema dostupnih podataka", height=500)
        fig2.update_layout(title="Nema dostupnih podataka", height=500)
        fig3.update_layout(title="Nema dostupnih podataka", height=500)
        fig4.update_layout(title="Nema dostupnih podataka", height=500)
        return fig1, fig2, fig3, fig4

    if k3 is None and k4 is None:
        df_filtered = get_grupna_analiza(k1,k2)
    elif k3 is not None and k4 is None:
        df_filtered = get_grupna_analiza(k1,k2,k3)
    elif k3 is not None and k4 is not None:
        df_filtered = get_grupna_analiza(k1,k2,k3,k4)

     # Dobavi kolegije (redoslijed)
    kolegiji = df_filtered["kolegij_sifra"].unique()

    # Upisani
    df_upisani = df_filtered[~df_filtered["priznat_ponavlja"].isin(["Priznat", "Ponavlja"])]
    broj_upisanih = df_upisani.groupby("kolegij_sifra").size().reindex(kolegiji, fill_value=0)

    # Ponavljači – svi kolegiji kao i kod upisanih
    df_ponavljaci = df_filtered[df_filtered["priznat_ponavlja"] == "Ponavlja"]
    broj_ponavljaca = df_ponavljaci.groupby("kolegij_sifra").size().reindex(kolegiji, fill_value=0)

    # Prosječne ocjene
    df_prosjecne_ocjene = df_filtered[df_filtered["ocjena"] > 1]
    prosjek_ocjena = df_prosjecne_ocjene.groupby("kolegij_sifra")["ocjena"].mean().round(2).reindex(kolegiji, fill_value=0)

    # Prolaznost
    broj_svih = df_filtered.groupby("kolegij_sifra").size()
    broj_prosli = df_filtered[df_filtered["ocjena"] > 1].groupby("kolegij_sifra").size()
    prolaznost = ((broj_prosli / broj_svih) * 100).round(2).reindex(kolegiji, fill_value=0)

    # Grafovi
    fig_upisani = create_trend_figure(broj_upisanih, "Broj upisanih studenata", "Broj studenata", decimals=0, show_bar=show_bar, show_trend=show_trend)
    fig_ponavljaci = create_trend_figure(broj_ponavljaca, "Broj ponavljača", "Broj ponavljača", decimals=0, base_index=broj_upisanih.index, show_bar=show_bar, show_trend=show_trend)
    fig_prosjecne_ocjene = create_trend_figure(prosjek_ocjena, "Prosječne ocjene", "Prosječna ocjena", decimals=2, show_bar=show_bar, show_trend=show_trend)
    fig_prolaznost = create_trend_figure(prolaznost, "Prolaznost", "Prolaznost (%)", decimals=2, show_bar=show_bar, show_trend=show_trend)

    return fig_upisani, fig_ponavljaci, fig_prosjecne_ocjene, fig_prolaznost

@app.callback(
    Output("offcanvas-info", "is_open"),
    Input("info-button", "n_clicks"),
    State("offcanvas-info", "is_open")
)
def toggle_offcanvas(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(debug=True)








