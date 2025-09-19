import os
import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output

# ======================
# 1. Load and prepare data from the web
# ======================
url = "https://cdn.bancentral.gov.do/documents/entorno-internacional/documents/Serie_Historica_Spread_del_EMBI.xlsx?v=1758230753578"

# Read Excel directly from URL
df = pd.read_excel(url, sheet_name="Serie Histórica", header=1)

# Clean dataframe
df.rename(columns={df.columns[0]: "Date"}, inplace=True)
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(axis=1, how="all")
df.columns = df.columns.astype(str).str.strip()
df.set_index("Date", inplace=True)
df = df[~df.index.duplicated(keep="last")]

# Fill missing days
all_days = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")
df = df.reindex(all_days).ffill()
df.index.name = "Date"

# Convert to integers (basis points)
df = df.apply(pd.to_numeric, errors="coerce")
df = (df * 100).round(0).astype("Int64")

# Keep only up to column T (20 columns: Date + 19 countries)
df = df.iloc[:, :20]

# ======================
# 2. Create Dash app
# ======================
app = Dash(__name__)
server = app.server  # required for Render / Railway

# Default start date (Jan 1, 2025)
default_start = pd.Timestamp("2025-01-01")
if default_start < df.index.min():
    default_start = df.index.min()

app.layout = html.Div([
    html.H1("Interactive EMBI Dashboard"),

    html.Label("Select Country/Countries:"),
    dcc.Dropdown(
        options=[{"label": c, "value": c} for c in df.columns if c.lower() != "date"],
        value=["Ecuador"],  # default
        multi=True,
        id="country-selector"
    ),

    html.Label("Select Date Range:"),
    dcc.DatePickerRange(
        id="date-range",
        min_date_allowed=df.index.min(),
        max_date_allowed=df.index.max(),
        start_date=default_start,  # default Jan 1, 2025
        end_date=df.index.max()
    ),

    dcc.Graph(id="embi-graph")
])

# ======================
# 3. Callbacks
# ======================
@app.callback(
    Output("embi-graph", "figure"),
    Input("country-selector", "value"),
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

        # Last value annotation (small label)
        last_date = dff.index[-1]
        last_value = dff[country].iloc[-1]
        fig.add_annotation(
            x=last_date,
            y=last_value,
            text=f"{last_value}",
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            font=dict(color="black", size=10)
        )

    # Add source note separately
    fig.add_annotation(
        text="Source: Central Bank of Dominican Republic",
        xref="paper",
        yref="paper",
        x=0,
        y=-0.15,
        showarrow=False,
        font=dict(size=9, color="gray"),
        align="left"
    )

    fig.update_layout(
        title="EMBI Spread - Selected Countries",
        xaxis_title="Date",
        yaxis_title="Spread (basis points)",
        hovermode="x unified"
    )
    return fig

# ======================
# 4. Run server
# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
