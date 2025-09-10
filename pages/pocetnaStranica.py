import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Dash, no_update
from dash.dependencies import Input, Output, State, MATCH





dash.register_page(__name__, path="/pocetnaStranica")  # ✅ Ispravno


app = dash.get_app()


layout = html.Div(style={'background-color': '#F4F4F4', 'padding': '20px'}, children=[
    
    # Header naslovom
    html.Div([
        html.H1("POČETNA STRANICA")
    ])
])



if __name__ == '__main__':
    app.run_server(debug=True)
