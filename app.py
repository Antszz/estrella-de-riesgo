from functools import lru_cache

from dash import Dash, dcc, html, Input, Output

import datos
import estrella
import estrella_plotly as ep

DF = datos.cargar()


@lru_cache(maxsize=8)
def clusters_completos(k):
    return datos.segmentar_clusters(DF, k=k)

LENTES = {
    "perfil": "Perfil de riesgo (clusters FAMD)",
    "URBANICITY": "Zona (urbana / rural)",
    "CAR_USE": "Uso del auto",
    "CAR_TYPE": "Tipo de auto",
    "EDUCATION": "Educacion",
    "OCCUPATION": "Ocupacion",
    "MSTATUS": "Estado civil",
}

LEYENDA = (
    "**Como leer cada estrella:** el **nucleo** indica la tasa de reclamo (color) "
    "y el monto medio del reclamo (tamano); el **radar** muestra el perfil de las "
    "variables numericas (mas lejos del centro = percentil mas alto); el **anillo** "
    "muestra la composicion de las variables categoricas (ancho del arco = proporcion). "
    "Color: **azul = menor riesgo · gris ≈ promedio (26.7%) · rojo = mayor riesgo**. "
    "El color de un arco es el riesgo propio de esa categoria (igual en todos los glifos); "
    "lo que cambia entre segmentos es el ancho del arco."
)

app = Dash(__name__)
app.title = "Estrella de Riesgo"

app.layout = html.Div(style={"maxWidth": "1180px", "margin": "0 auto",
                             "fontFamily": "system-ui, sans-serif", "padding": "12px"}, children=[
    html.H2("Estrella de Riesgo — exploracion visual de datos mixtos de seguros"),
    dcc.Markdown(LEYENDA, style={"fontSize": "14px", "color": "#333",
                                 "background": "#f6f6f6", "padding": "10px", "borderRadius": "6px"}),
    html.Div(style={"display": "flex", "gap": "24px", "flexWrap": "wrap",
                    "alignItems": "flex-end", "margin": "14px 0"}, children=[
        html.Div([html.Label("Segmentar por"),
                  dcc.Dropdown(id="lente", clearable=False, value="perfil",
                               options=[{"label": v, "value": k} for k, v in LENTES.items()],
                               style={"width": "260px"})]),
        html.Div([html.Label("Numero de perfiles (k) — solo aplica a 'Perfil de riesgo'"),
                  dcc.Slider(id="k", min=3, max=8, step=1, value=6,
                             marks={i: str(i) for i in range(3, 9)})],
                 style={"width": "260px"}),
        html.Div([html.Label("Orden de los ejes"),
                  dcc.RadioItems(id="orden", value="iv",
                                 options=[{"label": " por asociacion con el reclamo", "value": "iv"},
                                          {"label": " alfabetico", "value": "alfa"}])]),
        html.Div([html.Label("Zona"),
                  dcc.Dropdown(id="filtro_zona", clearable=False, value="Todos",
                               options=[{"label": z, "value": z} for z in
                                        ["Todos"] + sorted(DF["URBANICITY"].unique())],
                               style={"width": "160px"})]),
    ]),
    dcc.Loading(dcc.Graph(id="grafico", style={"height": "720px"}), type="circle"),
    html.Div(id="pie", style={"fontSize": "13px", "color": "#666", "marginTop": "8px"}),
])


@app.callback(
    Output("grafico", "figure"), Output("pie", "children"),
    Input("lente", "value"), Input("k", "value"),
    Input("orden", "value"), Input("filtro_zona", "value"))
def actualizar(lente, k, orden, zona):
    if lente == "perfil":
        etiquetas_full = clusters_completos(k)
        if zona == "Todos":
            df, etiquetas = DF, etiquetas_full
        else:
            mask = (DF["URBANICITY"] == zona).values
            df = DF[mask].reset_index(drop=True)
            etiquetas = etiquetas_full[mask].reset_index(drop=True)
    else:
        df = DF if zona == "Todos" else DF[DF["URBANICITY"] == zona]
        df = df.reset_index(drop=True)
        etiquetas = datos.segmentar_por_categoria(df, lente)
    titulos = None

    resumen = datos.resumen_segmentos(df, etiquetas)
    if titulos is None:
        if lente == "perfil":
            titulos = [f"Perfil {s} · reclamo {resumen[s]['tasa_reclamo']*100:.0f}% · n={resumen[s]['n']}"
                       for s in sorted(resumen)]
        else:
            titulos = [f"{s} · reclamo {resumen[s]['tasa_reclamo']*100:.0f}% · n={resumen[s]['n']}"
                       for s in sorted(resumen)]
    ctx = estrella.contexto(df, orden=orden)
    fig = ep.figura_segmentos(resumen, ctx, titulos=titulos)
    pie = f"{len(df):,} asegurados · {len(resumen)} segmentos · " \
          f"tasa de reclamo global de la seleccion: {df[datos.OBJETIVO_FLAG].mean()*100:.1f}%"
    return fig, pie


server = app.server

if __name__ == "__main__":
    import os
    puerto = int(os.environ.get("PORT", 8050))
    app.run(debug=False, host="0.0.0.0", port=puerto)
