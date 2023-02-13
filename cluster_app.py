from dash import Dash, dcc, html, Input, Output,State,ctx, dash_table
import os
import pandas as pd
from kmodes.kmodes import KModes
import plotly.graph_objects as go
import plotly.express as  px

import numpy as np
import math
from sklearn.preprocessing import OrdinalEncoder
from utils import get_plot,train_model

#from xgboost import XGBClassifier
#from xgboost import plot_importance
#from matplotlib import pyplot
#from sklearn.ensemble import RandomForestClassifier
#from sklearn.model_selection import train_test_split
#from sklearn.metrics import classification_report
#from catboost import CatBoostClassifier
#from sklearn.metrics import confusion_matrix
#from sklearn.linear_model import LogisticRegression


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets,suppress_callback_exceptions=True)

server = app.server
#source filname (only categorical variables)
filename_c='datos.csv'
# remove unnamed column
data=pd.read_csv(filename_c)
try:
    del data['Unnamed: 0']
except:
    print('no se pudo borrar Unammed')
#custom filter
data=data[data['SI VIVE EN BOGOTA, INDIQUE LA LOCALIDAD DE VIVIENDA EN LA QUE SE ENCUENTRA']!='NO APLICA']
#creating ordinal encoder
preprocessor=OrdinalEncoder()
X=preprocessor.fit_transform(data)

# app layout
app.layout=html.Div([
    html.Div([
        html.H3('Kmodes inspector'),
        html.H4(f'{filename_c} {len(data)} registros'),
        html.Div(dcc.Dropdown(id='nclusters',placeholder='# clusters',options=[{'label':i,'value':i} for i in range(2,11)]),style={'width':'20%','display':'inline-block'}),
        html.Div(id='div-button',children=[html.Button('Go',id='cluster-btn',n_clicks=0)],style={'display':'inline-block','position':'absolute','margin-left':'10px'})
        
    ]),
    
    dcc.Loading(id='loading1',children=[html.Div(id='questions-div')],type='graph'),
    html.P(id='saving-alert'),
    html.Div([
        html.Div(id='cluster-summary',style={'width':'25%','display':'inline-block'}),
        html.Div([dcc.Loading(id='loading2',children=[html.Div(id='questions-plot')],type='graph')],style={'display':'inline-block','width':'70%'}),
    ]),
    dcc.Loading(id='loading3',children=[html.Div(id='centroid-div')],type='graph'),
    html.Div(id='algo-list',style={'display':'inline-block'}),
    html.Br(),
    dcc.Loading(id='loading4',children=[html.Div(id='train-result-div',style={'margin-top':'-8%'})],type='cube')
        
    


])

# this callback triggers kmodes algorithm
@app.callback(Output('questions-div','children'),
              Output('centroid-div','children'),
              Output('cluster-summary','children'),
              Output('algo-list','children'),
              Output('saving-alert','children'),             
              [Input('cluster-btn','n_clicks')
              ,State('nclusters','value')])
def show_kmodes(n_clicks,nclusters):
    
    
    if 'cluster-btn'== ctx.triggered_id and nclusters is not None: 
        try:
            del data['cluster']
        except:
            pass
        print('clustering')
        #kmodes
        km = KModes(n_clusters=nclusters, init='Huang', n_init=5, verbose=1,n_jobs=3)
        km.fit(X)
        # getting centroids
        centroidskmodes=pd.DataFrame(preprocessor.inverse_transform(km.cluster_centroids_),columns=data.columns)
        #predicting over main dataset
        data['cluster']=km.predict(X)
        #saving results
        data.to_csv(f'data_{nclusters}_clusters.csv',index=False)
        #counting clusters
        summary_df=data['cluster'].value_counts().reset_index()
        summary_df=summary_df.rename(columns={'index':'CLUSTER','cluster':'CANTIDAD'})
        #summary_df['CLUSTER']=summary_df['CLUSTER'].astype('object')
        different_columns=[]
        #getting columns with different answers
        for c in centroidskmodes.columns:
            if len(centroidskmodes[c].unique())>1:
                different_columns.append(c)
        centroidskmodes=centroidskmodes[different_columns]
        centroidskmodes['cluster']=[i for i in range(nclusters)]
        centroidskmodes=centroidskmodes[[centroidskmodes.columns[-1]]+list(centroidskmodes.columns[:-1])]
        columns=[{'name':i,'id':i} for i in centroidskmodes.columns]
        #creating datatable with centroids
        cent_datatable= html.Div([dash_table.DataTable(
            id='centroid_table',
            style_table={'height':'300px','overflowY':'auto','overflowX':'auto','width':'auto'},
            style_header={'backgroundColor': '#393F56','fontWeight': 'bold','color':'white'},
            export_format='xlsx',
            page_size=7,
            style_cell={'textAlign': 'left','font-family': 'Arial,Helvetica,sans-serif',
                        'textOverflow': 'ellipsis',
                        'overflow': 'hidden',
                        'maxWidth': 0
                        },
            tooltip_data=[
                {column: {'value': str(value), 'type': 'markdown'} for column, value in row.items() } 
                    for row in centroidskmodes.to_dict('records')
            ],
            tooltip_header={i:i for i in centroidskmodes.columns},
            columns=columns,
            data=centroidskmodes.to_dict('records')

            
        )])
        print(summary_df)
        # barplot for cluster amount
        color_map={i:j for i,j in enumerate(px.colors.qualitative.D3)}
        fig_summary=px.bar(summary_df,y='CLUSTER',x='CANTIDAD',color_discrete_map=color_map,color='CLUSTER')
        fig_summary.update_yaxes(type='category')
        #fig_summary.update_layout(yaxis_range=[0,nclusters])
        summary_fig=dcc.Graph(figure=fig_summary)
        
        #retrieving menu with ml algorithms for variable importance
        train_btn=html.Div(id='btn-ml-div',n_clicks=0,children=[html.Button('Get importances',id='train-btn')]
                           ,style={'display':'inline-block','margin-left':'25%','margin-top':'-11%','position':'absolute'}
                            )
        ml_algorithms_list=html.Div(id='algo-div-list',
            children=[dcc.Dropdown(id='algorithm-id-list',
            options=[{'label':i,'value':i} for i in ['Xgbc','RandomForest','Catboost','LogisticReg']],
            placeholder='Select model type')],
            

            style={'display':'inline-block','width':'23%','position':'absolute','margin-top':'-11%'})
        title_ml_box=html.H5(id='title_ml',children=['Importancia de las variables'],style={'margin-top':'-13%','position':'absolute'})
        algo_list_box=[title_ml_box,ml_algorithms_list,train_btn]
        print(ml_algorithms_list)
        cent_div=html.Div([html.H5('Centroides'),cent_datatable])
        return dcc.Dropdown(id='questions-drop',options=[{'label':i,'value':i} for i in data.columns[:-1]],value=data.columns[0]),\
              cent_div,summary_fig,algo_list_box,f' Se ha creado el archivo data_{nclusters}_clusters.csv'
    return '','','','',''

# plotting clustering results by column
@app.callback(Output('questions-plot','children'),
              [Input('questions-drop','value')])
def show_plot(question):
    try:
        return dcc.Graph(figure=get_plot(question,data))
    except:
        return ''
@app.callback(Output('train-result-div','children'),
              [Input('train-btn','n_clicks'),
              State('algorithm-id-list','value')])

#shoing ML training results
def show_ml_insights(ml_btn,algorithm):
    
    if 'train-btn'==ctx.triggered_id and algorithm is not None:
        print(algorithm)
        # training data
        class_report,conf_matr,importances=train_model(data,model_type=algorithm)
        class_report=pd.DataFrame(class_report).reset_index()
        print(importances)
        importances=importances.reset_index()

        # table with importances by columns
        imp_datatable= html.Div(id='imp-div',children=[html.H5('Importancias'),dash_table.DataTable(
            id='importance_table',
            style_table={'overflowY':'auto','overflowX':'auto'},
            style_header={'backgroundColor': '#393F56','fontWeight': 'bold','color':'white'},
            export_format='xlsx',
            page_size=10,
            style_cell={'textAlign': 'left','font-family': 'Arial,Helvetica,sans-serif',
                        'textOverflow': 'ellipsis',
                        'overflow': 'hidden',
                        'maxWidth': 0
                        },
            tooltip_data=[
                {column: {'value': str(value), 'type': 'markdown'} for column, value in row.items() } 
                    for row in importances.to_dict('records')
            ],
            tooltip_header={i:i for i in importances.columns},
            columns=[{'name':i,'id':i } for i in importances.columns],
            data=importances.to_dict('records')

            
        )],style={'display':'inline-block','width':'46%'})
        # table with training performance
        class_report_datatable= html.Div(id='train-table-div',children=[html.H5('Performance'),dash_table.DataTable(
            id='importance_table',
            style_table={'height':'300px','overflowY':'auto','overflowX':'auto','width':'50%'},
            style_header={'backgroundColor': '#393F56','fontWeight': 'bold','color':'white'},
            export_format='xlsx',
            page_size=10,
            style_cell={'textAlign': 'left','font-family': 'Arial,Helvetica,sans-serif',
                        'textOverflow': 'ellipsis',
                        'overflow': 'hidden',
                        'maxWidth': 0
                        },
            tooltip_data=[
                {column: {'value': str(value), 'type': 'markdown'} for column, value in row.items() } 
                    for row in class_report.to_dict('records')
            ],
            tooltip_header={i:i for i in class_report.columns},
            columns=[{'name':i,'id':i } for i in class_report.columns],
            data=class_report.to_dict('records')

            
        )],style={'display':'inline-block','width':'54%','position':'absolute','margin-left':'9%'})
        train_result=html.Div([imp_datatable,class_report_datatable])
        
        return train_result


    return ''


if __name__=='__main__':
    app.run_server(debug=True)
