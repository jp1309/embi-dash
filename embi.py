import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output

# ======================
# 1. Cargar y preparar los datos
# ======================
file_path = r"C:\Users\JUANER\PycharmProjects\PythonProject\embi\Serie_Historica_Spread_del_EMBI.xlsx"
df = pd.read_excel(file_path, sheet_name="Serie Histórica", header=1)

# Renombrar y limpiar
df.rename(columns={df.columns[0]: "Fecha"}, inplace=True)
df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
df = df.dropna(axis=1, how="all")
df.columns = df.columns.astype(str).str.strip()
df.set_index("Fecha", inplace=True)
df = df[~df.index.duplicated(keep="last")]

# Rellenar fechas faltantes
all_days = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")
df = df.reindex(all_days).ffill()
df.index.name = "Fecha"

# Convertir columnas a numéricas y escalar valores (enteros)
df = df.apply(pd.to_numeric, errors="coerce")
df = (df * 100).round(0).astype("Int64")

# ======================
# 2. Crear la app Dash
# ======================
app = Dash(__name__)

app.layout = html.Div([
    html.H1("EMBI Dashboard Interactivo"),

    html.Label("Seleccionar País(es):"),
    dcc.Dropdown(
        options=[{"label": c, "value": c} for c in df.columns if c.lower() != "fecha"],
        value=["Ecuador"],  # valor por defecto
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

# ======================
# 3. Callbacks para actualizar el gráfico
# ======================
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
            x=dff.index,
            y=dff[country],
            mode="lines",
            name=country
        ))

        # Último valor
        last_date = dff.index[-1]
        last_value = dff[country].iloc[-1]

        # Etiqueta más pequeña, sin fondo
        fig.add_annotation(
            x=last_date,
            y=last_value,
            text=f"{last_value}",
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            font=dict(color="black", size=10)
        )

    fig.update_layout(
        title="EMBI Spread - Países seleccionados",
        xaxis_title="Fecha",
        yaxis_title="Spread (puntos básicos)",
        hovermode="x unified"
    )
    return fig

# ======================
# 4. Ejecutar servidor
# ======================
if __name__ == "__main__":
    app.run(debug=True)
