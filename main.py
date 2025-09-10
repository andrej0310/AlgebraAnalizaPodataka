import dash
from dash import dcc, html, Input, Output
from flask import Flask, redirect
import pymssql
import pandas as pd
from flask_talisman import Talisman
import dash_bootstrap_components as dbc
from baza import fetch_data_from_db

#app = dash.Dash(__name__, use_pages=True)


# 🔹 Kreiramo Flask server
server = Flask(__name__)

# 🔹 Direktno preusmeravanje ako korisnik otvori glavnu stranicu "/"
@server.route("/")
def home_redirect():
    return redirect("/pocetnaStranica", code=302)  # 🔄 Flask preusmerava odmah na ispravnu stranicu

csp = {
    "default-src": "'self'",
    "script-src": [
        "'self'", "'unsafe-inline'", "'unsafe-eval'",
        "https://cdn.plot.ly", "https://cdnjs.cloudflare.com",
        "https://code.jquery.com", "https://cdn.jsdelivr.net"
    ],
    "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdn.jsdelivr.net"],
    "img-src": ["'self'", "data:", "https://lh3.googleusercontent.com"],
    "font-src": ["'self'", "https://fonts.gstatic.com"],
    "connect-src": [
        "'self'", "https://cdn.plot.ly", "https://cdnjs.cloudflare.com"
    ],
}

Talisman(server, content_security_policy=csp)


# 🔹 Inicijalizacija Dash aplikacije sa istim Flask serverom
app = dash.Dash(
    __name__,
    server=server,  # 🔹 Vežemo Dash na Flask server
    use_pages=True,  # Omogućavamo višestruke stranice
    suppress_callback_exceptions=True,
    serve_locally=True,  # 🔹 Ovo dodajemo!
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)


image_id = "1IVYXW6Ye48OeHt6Xo89gJPp7NRySHwFH"  # Zameni svojim ID-om
image_url = f"https://lh3.googleusercontent.com/d/{image_id}"

query = "SELECT * FROM dbo.analytics_vss_struktura_akad_godine"
df = fetch_data_from_db(query)

# 🔹 Postavi inicijalnu akademsku godinu
if df.empty:
    default_akademska_godina = "2023/2024"  # 🚀 Postavi sigurnu akademsku godinu ako nema podataka
else:
    default_akademska_godina = df.loc[df['aktualna'] == "1", 'naziv'].values[0] if not df[df['aktualna'] == "1"].empty else df['naziv'].iloc[0]

akademska_godina = default_akademska_godina

default_data = {"akademska_godina": default_akademska_godina}


app.layout = html.Div(style={'background-color': '#F4F4F4', 'padding': '20px'}, children=[
        dcc.Store(id="shared-data", data=default_data, storage_type="session"),
        dcc.Store(id="shared-data-local",data={"a": "b"}),
        dcc.Store(id="shared-data-local1",data={"a": "b"}),
        html.Div([
            dcc.Location(id="url", refresh=False),          
            html.Img(src=image_url, style={'height': '80px', 'margin-right': '20px'}),
            html.H6("Analiza podataka",  style={'color': '#ffffff', 'font-weight': 'bold','font-size':'30px'})
            ],style={'display': 'flex', 'align-items': 'center', 'background-color': '#151515', 'padding': '10px', 'border-radius':'6px'}),
        
        html.Div([
            #html.Div([ 
            
            # PADAJUĆI IZBORNIK AKADEMSKA
        
            # html.Label("Akademska godina:", style={'font-size': '18px', 'font-weight': 'bold', 'margin-right': '10px'}),
            # dcc.Dropdown(
            #     id="akademska-godina-dropdown",
            #     options=[{"label": godina, "value": godina} for godina in df["naziv"]],
            #     value=default_akademska_godina,  # ✅ Inicijalna vrijednost
            #     clearable=False,
            #     style={'width': '150px', 'margin-left': '20px', "margin-right":"100px"},
            #     persistence=True,  # ✅ Pamti odabir korisnika
            #     persistence_type="session"  # ✅ Opcije: "local", "session", "memory"
            #     ),
            # ], style={'display': 'flex', 'align-items': 'center', 'background-color': '#ffffff', 'padding': '10px',"with":"50px"},
            #    className="padajuci-akademska"), 

        # GUMBI ZA ODABIR STRANICA
            html.Div([
                html.A("Kolegij - Prosječne ocjene i prolaznost", id="btn-kolegij", className="btn", href="/ProsjekPredmeti"),
                html.A("Studenti - Analiza po gneraciji",id="btn-student",className="btn", href="/ProsjekStudenti"),
                html.A("Studenti - Analiza po akademskoj godini",id="btn-broj",className="btn", href="/BrojeviStudenti")
            ],className="gumbi")
            
        ], className="button-container"),
        
        html.Hr(),

        # dcc.Loading(
        #     id="loading-container",
        #     type="circle",  # Može biti "default", "circle" ili "dot"
        #     children=[dash.page_container]
        # )
        
        dash.page_container  # 🔹 Dodano kako bi prikazalo dinamične stranice
    ]
)

# @app.callback(
#     Output("shared-data", "data", allow_duplicate=True),
#     [Input("akademska-godina-dropdown", "value"),
#      Input("url", "pathname"),
#      Input("shared-data", "data")],
#     prevent_initial_call='initial_duplicate'  # 🚀 Sprječava inicijalni poziv
# )
# def update_akademska_godina(selected_godina,pathname,shared_data):
    
#     ####
#     #print(f"🔍 [DEBUG] main.py - shared-data primio: {selected_godina}")
#     if selected_godina is None:
#         print("⚠️ [ALERT] shared-data je postao None u main.py!")
#         return {"akademska_godina": "2024/2025"}  # Reset na sigurnu vrijednost
#     ####

#     #if shared_data is None:
#     #   return dash.no_update  # ✅ Sprječava resetiranje na `None`
    
#     return {"akademska_godina": selected_godina}  # ✅ Ažurira vrijednost u `dcc.Store`

@app.callback(
    [Output("btn-kolegij", "className"), Output("btn-student", "className"),Output("btn-broj","className")],
    Input("url", "pathname")
)
def update_active_button(pathname):
    # ✅ Inicijalno otvaranje aplikacije preusmjerava na "/ProsjekPredmeti"
    if pathname == "/ProsjekPredmeti":
        return "btn active", "btn", "btn"
    elif pathname == "/ProsjekStudenti":
        return "btn", "btn active", "btn"
    elif pathname == "/BrojeviStudenti":
        return "btn", "btn" , "btn active"
    return "btn", "btn", "btn"  # Ako URL nije prepoznat


if __name__ == '__main__':
    app.run(debug=True)

