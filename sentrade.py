#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import chart_studio.plotly as py
import plotly.graph_objs as go
import requests
import pandas as pd
import json
import datetime as dt
import colorlover as cl
import datetime as dt
import flask
import os
import pymongo 
from sshtunnel import SSHTunnelForwarder
from plotly.subplots import make_subplots

from textwrap import dedent as d
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from plotly import tools
from data import correlation_analysis

__author__ = "Davide Locatelli, Longzhen Li, Ziyou Zhang"
__status__ = "Prototype"

app = dash.Dash(__name__, meta_tags=[{"name":"viewport", "content": "width=device-width"}])
server = app.server

colorscale = cl.scales['9']['qual']['Paired']

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/dash-stock-ticker-demo.csv')
db_client = pymongo.MongoClient("mongodb://admin:sentrade@45.76.133.175", 27017)
db = db_client["sentrade_db"]
#load news
#this is just for apple, we can change according to the ticker inserted
response = requests.get('https://newsapi.org/v2/everything?'
       'q=Apple&'
       'from=2020-01-20&'
       'sortBy=popularity&'
       'apiKey=954c05db19404ee99531875f66d9d138')
#print (response.json())

def update_news():
    articles = response.json()["articles"]
    df = pd.DataFrame(articles)
    df = pd.DataFrame(df[["title","url"]])
    max_rows = 10
    return html.Div(
        children =[
            html.P(className="p-news",children="Headlines"),
            html.P(
                className="p-news-float-right",
                children="Last update: "
                + datetime.datetime.now().strftime("%H:%M:%S")
            ),
            html.Table(
                className="table-news",
                children= [
                    html.Tr(
                        children=[
                            html.Td(
                                children=[
                                    html.A(
                                        className="td-link",
                                        children=df.iloc[i]["title"],
                                        href=df.iloc[i]["url"],
                                        target="_blank",
                                    )
                                ]
                            )
                        ]
                    )
                    for i in range(min(len(df),max_rows))
                ],
            ),
        ]
    )

app.layout = html.Div(
    children=[
        html.Div(
            className='top-bar',
            children=[
                html.H2(
                    'SENTRADE',
                    style={'display': 'inline',
                    'float': 'left',
                    'font-size': '3em',
                    'margin-left': '7px',
                    'font-weight': '900',
                    'font-family': 'Product Sans',
                    'color': 'black',
                    'margin-top': '0px',
                    'margin-bottom': '0'
                    }
                ),
                html.H4(
                    'Financial Sentiment Analysis',
                    style={'display': 'inline',
                    'float': 'left',
                    'font-size': '1.8em',
                    'margin-left': '7px',
                    'font-weight': '500',
                    'font-family': 'Product Sans',
                    'color': '#9C9C9C',
                    'margin-top': '14px',
                    'margin-bottom': '0'
                    }
                ),
                dcc.Dropdown(
                    id='stock-ticker-input',
                    options=[
                        {'label':'AMZN','value':'AMZN','disabled':False},
                        {'label':'AAPL','value':'AAPL', 'disabled':False},
                        {'label':'FB','value':'FB','disabled':False},
                        {'label':'GOOG','value':'GOOG','disabled':False},
                        {'label':'MSFT','value':'MSFT','disabled':False},
                        {'label':'NFLX','value':'NFLX','disabled':False},
                        {'label':'TSLA','value':'TSLA','disabled':False},
                        {'label':'UBER','value':'UBER','disabled':False},
                    ],
                    multi=False,
                    placeholder ='Select Ticker',
                    style={'display': 'inline',
                    'width':'35%',
                    'float': 'right',
                    'font-size': '1.2em',
                    'font-weight': '500',
                    'font-family': 'Product Sans',
                    'color': '#9C9C9C',
                    'margin-top': '6px'
                    }
                )
            ]
        ),
        html.Div(
            className = 'left-bar',
            children = [
                html.Div(
                    className='graph',
                    id='graph',
                ),
                html.Div(
                    className='click-data',
                    children=[
                        dcc.Markdown(d("""Financial Data""")),
                        html.Pre(id='click-data'),
                    ],
                ),
            ]
        )
    ]
)

@app.callback(
    dash.dependencies.Output('graph','children'),
    [dash.dependencies.Input('stock-ticker-input', 'value')])
def update_graph(ticker):
    graph = []

    if not ticker:
        graph.append(html.H3(
            "No ticker selected.",
            style={
                'margin-top':'0px',
                'textAlign':'center',
                'color':'#9C9C9C'
            }
        ))
    else:
        graph.append(html.H3(
            ticker,
            style={
                'font-size':'2.5em',
                'margin-left':'20px',
                'textAlign':'left',
                'color':'black'
            }
        ))
        stock_price_collection = db["stock_price"]
        sentiment_collection = db["news"]

        close = []
        stock_date = []
        for record in stock_price_collection.find({"company_name":ticker}):
            close.append(record["close"])
            stock_date.append(record["date"])
        
        polarity = []
        sent_date = []
        for record in sentiment_collection.find():
            polarity.append(record["polarity"])
            sent_date.append(record["date"])

        eth_close = go.Scatter(
            y = close,
            x = stock_date,
            name = "Close",
            mode = "lines",
            line=dict(color="#7a90e0")
        )
        eth_polarity = go.Scatter(
            y = polarity,
            x = sent_date,
            name = "Sentiment",
            mode = "lines",
            line=dict(color="#FFC300")
        )
        fig = make_subplots(specs=[[{"secondary_y":True}]])
        fig.add_trace(eth_close,secondary_y=False)
        fig.add_trace(eth_polarity,secondary_y=True)
        fig.update_layout(
            margin= {'b': 0, 'r': 10, 'l': 60, 't': 0},                   
            legend= {'x': 0},
            xaxis=go.layout.XAxis(
                rangeslider=dict(
                    visible=False
                ),
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                            label="1D",
                            step="day",
                            stepmode="backward"),
                        dict(count=7,
                            label="1W",
                            step="day",
                            stepmode="backward"),
                        dict(count=1,
                            label="1M",
                            step="month",
                            stepmode="backward"),
                        dict(count=3,
                            label="3M",
                            step="month",
                            stepmode="backward"),
                        dict(count=6,
                            label="6M",
                            step="month",
                            stepmode="backward"),
                        dict(count=1,
                            label="1Y",
                            step="year",
                            stepmode="backward"),
                        dict(label='ALL',step="all")
                    ]),
                    font=dict(
                        family="Arial",
                        size=16,
                        color="white"),
                    bgcolor="#BABABA",
                    activecolor='#949494',
                    x=0.35,
                    y=-0.13
                ),
                type="date"
            )
        )
        graph.append(dcc.Graph(figure=fig,style={'margin-top':'0','height':'400'}))
    return graph
"""
    # Graph and news
    html.Div(
        className="two columns panel",
        children=[
            # Div for Graph
            html.Div(
                dcc.Graph(
                    id='output-graph',
                    figure={
                        'data': [
                            {'x': [], 'y': [], 'type': 'scatter', 'name': 'stock', 'mode': 'markers'},
                        ],
                        'layout': {
                            'title': 'stock sentiment',
                            'xaxis': {
                                'title':'sentiment_score'
                                },
                            'yaxis': {
                                'title':'stock_price_change'
                            }
                        }
                    },
                    style={
                        'width':'100%'
                        }
                )
            ),
            # Div for News Headlines
            html.Div(
                className="div-news",
                children=[html.Div(id="news", children=update_news())], 
                style={'width':'50%'}
            ), 
        ], 
        style={'columnCount': 2, 'width':'100%'}
    ),

html.Div(className="inputbox",children=[dcc.Input(id='input-box', value='', type='text'),html.Button('Submit', id='button'),], style={'width':'50%'}),


@app.callback(
    Output('output-graph', 'figure'),
    [Input('button', 'n_clicks')],
    [State('input-box', 'value')]
    )
def update_graph(no_clicked,input_value):

    sentiment_scores, price_changes = correlation_analysis("temp_twitter.json", "temp_sentiment.json", "temp_stock.json")

    if no_clicked is None:
         raise PreventUpdate
    elif input_value is None:
         raise PreventUpdate
    else: 
        return {  
        'data': [
                {'x': sentiment_scores, 'y': price_changes, 'type': 'scatter', 'name': 'stock', 'mode': 'markers', 'marker': {'size': 12}},
                ],
        'layout': {
            'title': 'stock sentiment',
            'xaxis': {
                'title':'sentiment_score'
            },
            'yaxis': {
                'title':'stock_price_change'
            }
            }           
        }
"""
if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=80)