import os
import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output

# === Datos ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "Serie_Historica_Spread_del_EMBI.xlsx")

# Lee el Excel
df = pd.read_excel(file_path, sheet_name="Serie Histórica", header=1)

# Limpieza
df.rename(columns={df.columns[0]: "Fecha"}, inplace=True)
df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
df = df.dropna(axis=1, how="all")
df.columns = df.columns.astype(str).str.strip()
df.set_index("Fecha", inplace=True)
df = df[~df.index.duplicated(keep="last")]

# Rango diario y ffill
all_days = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")
df = df.reindex(all_days).ffill()
df.index.name = "Fecha"

# Números enteros en puntos básicos
df = df.apply(pd.to_numeric, errors="coerce")
df = (df * 100).round(0).astype("Int64")

# === App ===
app = Dash(__name__)
server = app.server  # necesario para gunicorn

app.layout = html.Div([
    html.H1("EMBI Dashboard Interactivo"),
    html.Label("Seleccionar País(es):"),
    dcc.Dropdown(
        options=[{"label": c, "value": c} for c in df.columns if c.lower() != "fecha"],
        value=["Ecuador"],
        multi=True,
        id="pais-selector"
    ),
    html.Label("Seleccionar Rango de Fechas:"),
    dcc.DatePickerRange(
        id="date-range",
        min_date_allowed=df.index.min(),
        max_date_allowed=df.index.max(),
        start_date=df.index.min(),
        end_date=df.index.max()
    ),
    dcc.Graph(id="embi-graph")
])

@app.callback(
    Output("embi-graph", "figure"),
    Input("pais-selector", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_graph(selected_countries, start_date, end_date):
    if not selected_countries:
        return go.Figure()

    dff = df.loc[start_date:end_date, selected_countries]

    fig = go.Figure()
    for country in selected_countries:
        fig.add_trace(go.Scatter(
            x=dff.index, y=dff[country], mode="lines", name=country
        ))
        # etiqueta del último valor
        last_date = dff.index[-1]
        last_value = dff[country].iloc[-1]
        fig.add_annotation(
            x=last_date, y=last_value, text=f"{last_value}",
            showarrow=False, xanchor="left", yanchor="middle",
            font=dict(color="black", size=10)
        )

    fig.update_layout(
        title="EMBI Spread - Países seleccionados",
        xaxis_title="Fecha",
        yaxis_title="Spread (puntos básicos)",
        hovermode="x unified"
    )
    return fig

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
