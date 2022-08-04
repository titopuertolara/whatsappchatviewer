from dash import Dash,dcc,html,Output,Input,State
import os
from utils import upload_file,list_files,dummy_connection,create_word_cloud
import sqlite3
import pandas as pd

import base64

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets,suppress_callback_exceptions=True)

path='uploaded'
server = app.server
files_list=list_files(path)
db_obj=dummy_connection('')
app.layout = html.Div([
	html.Div([
	   html.Div(id='uploader-div',
			children=[dcc.Upload(id='file-button',children=[html.Button('SUBIR ARCHIVO')])],
			style={'display':'inline-block'}
			),
		
		html.Div([
				dcc.Loading(id='loading-gif',
					children=[html.P(id='filename-p')],
					type='circle'
				)
		],style={'display':'inline-block'})
				
   	]),
   html.Br(),
   html.P('Bases de datos existentes'),
   html.Div(id='file-list-div',
   	children=[dcc.RadioItems(id='databases-options')]
   	),
   html.Div(html.Button('Cargar BD',id='load-bd',n_clicks=0)),
   dcc.Loading(id='numbers-loader',   
	   children=[html.Div(id='phone-numbers')],
	   type='default'
   ),
   dcc.Checklist(id='watch-conv',options=[{'label':'Ocultar conversación','value':'hidden'}],value=['hidden']),
   html.Div(id='wp-conversation',style={'height':'500px','overflow':'scroll'}),
   html.Img(id='wordcloud-conv')
   #dcc.Graph(id='wordcloud-conv')
])

#hide or show conversation

@app.callback(Output('wp-conversation','style'),
              [Input('watch-conv','value')])
def show_hide_conv(value):
	if value is None:
		value=[]
	
	
	if 'hidden' in value:
		return {'display':'none'}
	else:
		return {'height':'500px','overflow':'scroll'}
	

# Load conversation
@app.callback(Output('wp-conversation','children'),
              Output('wordcloud-conv','src'),
              [Input('numbers-menu','value')])
def get_conversation(cel):
	to_return=''
	if cel is None:
		cel=[]
	query=f"""SELECT key_remote_jid,data,timestamp,key_from_me FROM messages"""
	df=pd.read_sql(query,db_obj.conn)
	if len(cel)>0:
		df=df[df['key_remote_jid'].isin(cel)]
	
	if len(cel)==1:
		to_return=[]
		for i in df.index:
			msg=df.loc[i,'data']
			orientation=df.loc[i,'key_from_me']
			if orientation==1:
				to_return.append(html.Div(msg,style={'margin-left':'50%','width':'40%','background-color': 'lightgreen'}))
				to_return.append(html.Br())
			else:
				to_return.append(html.Div(msg,style={'width':'40%','background-color': 'lightgray'}))			
		
			
	elif len(cel)>1:
		to_return= 'Se seleccionó mas de un número por lo que no se visualizará la conversación'
	else:
		to_return='No hay números seleccionados'
	wc_fig=create_word_cloud(df[df['key_from_me']==0].dropna())
	
	
	
		
		
	return to_return,wc_fig
	
# get bd info
@app.callback(Output('phone-numbers','children'),
				  
             [Input('load-bd','n_clicks'),
              State('databases-options','value')])
def get_numbers(n_clicks,bd):
	response=''
	res_df=pd.DataFrame()
	if bd is not None:
		conn=sqlite3.connect(f'{path}/{bd}', check_same_thread=False)
		db_obj.conn=conn
		try:
			query="""SELECT * FROM messages """
			res_df=pd.read_sql(query,conn)
			numbers=list(res_df['key_remote_jid'].unique())
			
			response=html.Div([
				dcc.Dropdown(id='numbers-menu',options=[{'label':i,'value':i} for i in numbers],multi=True)
			],style={'width':'50%'})
		except Exception as e:
			response='⛔ '+str(e)+' ⛔'
	
	return response

# load db file
@app.callback([Output('filename-p','children'),
               Output('databases-options','options'),
					Input('file-button','filename'),
					Input('file-button','contents')])
					
def get_file(filename,content):
	options=[{'label':'','value':''}]
	if filename is not  None:
		if filename.split('.')[1]=='db':
			try:
				upload_file(path,filename,content)
				msg=f'{filename}'
				
				options=[{'label':i,'value':i} for i in list_files(path) ]
				
				
			except:
				msg=f'Error al subir {filename}'
		else:
			msg='solo se aceptan archivos con extensión .db'
		return [msg],options
	else:
		options=[{'label':i,'value':i} for i in list_files(path) ]
		return [''],options
	
	
	
if __name__=='__main__':
	app.run_server(debug=True)