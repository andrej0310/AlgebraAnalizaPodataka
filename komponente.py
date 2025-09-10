from dash import html, dcc
import dash_bootstrap_components as dbc

def offcanvas_sadrzaj_info():
    return html.Div(id="offcanvas-body", children=[
        html.P("""
            Ovi grafovi prikazuju kako su se ocjene studenata raspoređivale (distribuirale)
            unutar različitih razreda dolaznosti na predavanja ili vježbe. Svaka kategorija dolaznosti 
            (npr. 70–85%, 85–100%) prikazana je kao posebni box-plot.
        """, style={"margin-bottom": "15px"}),

        html.Ul([
            html.Li("📦 Visina okvira (boxa) prikazuje raspon od 25. do 75. percentila (interkvartilni raspon)."),
            html.Li("📏 Vodoravna crta unutar boxa prikazuje medijan (srednju vrijednost ocjena u toj grupi)."),
            html.Li("🔵 Točkice izvan boxa označavaju potencijalne odstupanja (outliere)."),
            html.Li("👥 Broj iznad stupca (N=...) prikazuje broj studenata u toj kategoriji dolaznosti."),
            html.Li("✅ Postotak iznad pokazuje prolaznost (ocjene > 1) u toj grupi."),
            html.Li("🎨 Boja stupca odgovara kategoriji dolaznosti (vidi legendu s desne strane).")
        ], style={"padding-left": "20px"}),

        html.P("""
            Cilj ovih grafova je vizualno prikazati moguće povezanosti između dolaznosti i uspjeha studenata.
        """, style={"margin-top": "10px"})

    ])


def offcanvas_sadrzaj_tabs():
    return dbc.Tabs([
        dbc.Tab(label="Box plot", tab_id="boxplot", children=[
            dcc.Markdown("""
### 📦 Box plot

Box plot prikazuje raspodjelu ocjena unutar svake grupe dolaznosti.

- **Kutija (box)** prikazuje srednjih 50% podataka (interkvartilni raspon)
- **Crta unutar boxa** = medijan
- **Točkice** = outlieri
- **N iznad grupe** = broj studenata
- **Postotak iznad** = prolaznost (ocjena > 1)

Koristi se za usporedbu kako dolaznost može utjecati na ocjene.
            """)
        ]),
        dbc.Tab(label="Bar chart", tab_id="barchart", children=[
            dcc.Markdown("""
### 📊 Bar chart (stupčasti graf)

Stupčasti graf prikazuje brojčane vrijednosti kao stupce.

- Os X prikazuje kategorije (npr. šifre kolegija)
- Os Y prikazuje vrijednosti (npr. broj upisanih, prosječna ocjena)
- Trend linija može prikazati kretanje vrijednosti između kategorija

Koristan za prikaz broja upisanih, ponavljača, prosječnih ocjena ili prolaznosti.
            """)
        ]),
        dbc.Tab(label="Scatter plot", tab_id="scatter", children=[
            dcc.Markdown("""
### ⚫ Scatter plot (raspršeni graf)

Scatter plot prikazuje pojedinačne vrijednosti u odnosu na dvije varijable.

- Svaka točka = jedan student
- Os X i Y prikazuju dvije mjere (npr. dolaznost vs ocjena)
- Koristi se za vizualnu identifikaciju korelacija

Pomaže otkriti postoji li povezanost između dvije metrike.
            """)
        ])
    ])

