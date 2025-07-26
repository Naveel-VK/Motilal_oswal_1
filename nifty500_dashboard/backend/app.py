# backend/app.py

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
from xhtml2pdf import pisa
import base64
import tempfile
import os
from io import BytesIO
from predict import get_prediction  # Make sure this function returns a DataFrame with 'Date' and 'Predicted'

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # <-- This is required for Render

# Load stock list
nifty_df = pd.read_csv('assets/nifty500_list.csv')
options = [{'label': row['Company Name'], 'value': row['Symbol']} for _, row in nifty_df.iterrows()]

def generate_table(pred_df):
    return dbc.Table(
        [html.Thead(html.Tr([html.Th("Date"), html.Th("Predicted Price")]))] +
        [html.Tbody([
            html.Tr([
                html.Td(date.strftime("%Y-%m-%d")),
                html.Td(f"{price:.2f}")
            ]) for date, price in zip(pred_df['Date'], pred_df['Predicted'])
        ])],
        bordered=True,
        striped=True,
        hover=True,
        responsive=True,
        className='mt-3',
        id='prediction-table'
    )

# Layout
app.layout = dbc.Container([
    dbc.NavbarSimple(brand="Nifty 500 Stock Dashboard", color="dark", dark=True, className='mb-4'),

    dbc.Row([
        dbc.Col(dcc.Dropdown(id='symbol-dropdown', options=options, value=options[0]['value'], clearable=False), width=4),
        dbc.Col(dbc.Button("Download PDF", id='btn-download-pdf', color='primary'), width='auto'),
    ], className='mb-4'),

    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id='historical-graph', style={'height': '350px'})), width=6),
        dbc.Col(dcc.Loading(dcc.Graph(id='prediction-graph', style={'height': '350px'})), width=6)
    ], className='mb-4'),

    dbc.Card([
        dbc.CardHeader(html.H5("Prediction Table")),
        dbc.CardBody(dcc.Loading(html.Div(id='predicted-table')))
    ], className='mb-4'),

    dcc.Download(id="download-pdf")
], fluid=True)

# Callbacks
@app.callback(
    [Output('historical-graph', 'figure'),
     Output('prediction-graph', 'figure'),
     Output('predicted-table', 'children')],
    [Input('symbol-dropdown', 'value')]
)
def update_output(symbol):
    try:
        df = pd.read_csv(f'backend/data/{symbol}.csv')
        df['Date'] = pd.to_datetime(df['Date'])

        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df['Date'], y=df['Close'], mode='lines', name='Close Price'))
        fig1.update_layout(title="Historical Price", height=350)

        pred_df = get_prediction(symbol)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=pred_df['Date'], y=pred_df['Predicted'], mode='lines+markers', name='Predicted Price'))
        fig2.update_layout(title="Prediction", height=350)

        table = generate_table(pred_df)

        return fig1, fig2, table

    except Exception as e:
        print(f"Error: {e}")
        return go.Figure(), go.Figure(), dbc.Alert("Data not available", color="danger")

@app.callback(
    Output("download-pdf", "data"),
    [Input("btn-download-pdf", "n_clicks")],
    [State('symbol-dropdown', 'value')],
    prevent_initial_call=True
)
def generate_pdf_callback(n_clicks, symbol):
    df = pd.read_csv(f'backend/data/{symbol}.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    pred_df = get_prediction(symbol)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df['Date'], y=df['Close'], mode='lines'))
    fig1.update_layout(title="Historical")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=pred_df['Date'], y=pred_df['Predicted'], mode='lines+markers'))
    fig2.update_layout(title="Prediction")

    def fig_to_base64(fig):
        img_bytes = fig.to_image(format="png")
        return base64.b64encode(img_bytes).decode()

    img1 = fig_to_base64(fig1)
    img2 = fig_to_base64(fig2)

    html_string = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #dddddd; text-align: center; padding: 8px; }}
            th {{ background-color: #4CAF50; color: white; }}
            img {{ width: 100%; height: auto; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h2>Prediction Report for {symbol}</h2>
        <h3>Historical Chart</h3>
        <img src="data:image/png;base64,{img1}" />
        <h3>Prediction Chart</h3>
        <img src="data:image/png;base64,{img2}" />
        <h3>Prediction Table</h3>
        <table>
            <tr><th>Date</th><th>Predicted Price</th></tr>
    """

    for date, price in zip(pred_df['Date'], pred_df['Predicted']):
        html_string += f"<tr><td>{date.strftime('%Y-%m-%d')}</td><td>{price:.2f}</td></tr>"

    html_string += "</table></body></html>"

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmpfile:
        pisa.CreatePDF(html_string, dest=tmpfile)
        tmpfile.seek(0)
        pdf_data = tmpfile.read()
    os.unlink(tmpfile.name)

    return dict(content=pdf_data, filename=f"{symbol}_report.pdf", type="application/pdf")

# Only needed for local development; Render will ignore this line
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
