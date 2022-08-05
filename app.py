from dash import Dash,dcc,html,Output,Input,State,dash_table
import os
from utils import upload_file,list_files,dummy_connection,create_word_cloud,bar_plot_words
import sqlite3
import pandas as pd
from datetime import datetime,timedelta,date
import time
import datetime
import base64
from icecream import ic


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets,suppress_callback_exceptions=True)

path='uploaded'
server = app.server
files_list=list_files(path)
db_obj=dummy_connection('')
app.layout = html.Div([
	html.Div([
	   html.H3('Visor de mensajes de Whatsapp'),
	   html.P('Suba el archivo con extensión .db, seleccionelo, escoja el rango de fechas a consultar y finalmente haga click en CARGAR DB'),
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
   html.Br(),
   dcc.DatePickerRange(
					id='date-range',
      	  		min_date_allowed=date(2022, 1, 1),
       	  		max_date_allowed=date(2023, 12, 31),
        	  		start_date=date.today()-timedelta(days=30),
        	  		end_date=date.today(),
        	  		style={'display':'inline-block'}
   ),
   html.Div(html.Button('Cargar BD',id='load-bd',n_clicks=0),style={'display':'inline-block'}),
   html.Br(),
   html.Div(id='datatable-div',style={'width':'40%'}),
   
   dcc.Loading(id='numbers-loader',   
	   children=[html.Div(id='phone-numbers')],
	   type='default'
   ),
   html.Br(),
   
   html.Div([
   	dcc.Loading(id='image-loading',
   		children=[html.Img(id='wordcloud-conv',style={'width':'30%','display':'inline-block','margin-top':'6%'})],
   		type='graph'
   	),
   	dcc.Loading(id='barplot-loading',
   		children=[html.Div(id='bar-plot-words',style={'width':'30%','display':'inline-block','margin-left':'50%','margin-top':'-24%'})],
   		type='dot'
   	)
   ]),
   dcc.Checklist(id='watch-conv',options=[{'label':'Ocultar conversación','value':'hidden'}],value=['hidden']),
   html.Div(id='wp-conversation',style={'height':'500px','overflow':'scroll'}),
   dcc.Checklist(id='watch-db',options=[{'label':'Revisar tabla','value':'show'}]),
   html.Div(id='db-table')
   
   #dcc.Graph(id='wordcloud-conv')
])
#hide or show db

@app.callback(Output('db-table','style'),
				  [Input('watch-db','value')])
def show_hide_db(value):
	if value is None:
		value=[]
	if 'show' in value:
		
		return {'display':'block'}
		
	else:
		return {'display':'none'}
		
		
	

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
              Output('db-table','children'),
              Output('bar-plot-words','children'),
              [Input('numbers-menu','value'),
               Input('dates-dict','data')])
def get_conversation(cel,dates_dict):
	to_return=''
	db_content=[]
	fig_list=[]
	print(dates_dict)
	
	if cel is None:
		cel=[]
	
	query=f"""SELECT key_remote_jid,data,timestamp,key_from_me ,strftime('%d-%m-%Y', datetime(timestamp/1000, 'unixepoch')) as fecha 
				FROM messages"""
	df=pd.read_sql(query,db_obj.conn)
	df=df.dropna()
	df=df[(df['timestamp']>=dates_dict['start_ts']) & (df['timestamp']<=dates_dict['end_ts']) ] 
	
	
	
	
	if len(cel)>0:
		df=df[df['key_remote_jid'].isin(cel)]		
		
	
	if len(cel)==1:
		to_return=[]
		for i in df.index:
			msg=df.loc[i,'data']
			orientation=df.loc[i,'key_from_me']
			spec_date=df.loc[i,'fecha']
			if orientation==1:
				to_return.append(html.Div(f'({spec_date}){msg}',style={'margin-left':'50%','width':'40%','background-color': 'lightgreen'}))
				to_return.append(html.Br())
			else:
				to_return.append(html.Div(f'({spec_date}){msg}',style={'width':'40%','background-color': 'lightgray'}))
				to_return.append(html.Br())			
		
			
	elif len(cel)>1:
		to_return= 'Se seleccionó mas de un número por lo que no se visualizará la conversación'
	else:
		to_return='No hay números seleccionados'
	wc_fig=create_word_cloud(df[df['key_from_me']==0].dropna())
	fig_list.append(dcc.Graph(figure=bar_plot_words(df[df['key_from_me']==0].dropna())))
	
	db_content.append(
		dash_table.DataTable(id='msg-ranking',
			columns=[{'name':i,'id':i} for i in df.columns],
			data=df.to_dict('records'),
						
			export_format='xlsx',
			style_table={'overflowY':'auto','overflowX':'auto','width':'auto'},
			style_header={'backgroundColor': '#393F56','fontWeight': 'bold','color':'white'},
			page_size=5,
			style_cell={'textAlign': 'left','font-family': 'Arial,Helvetica,sans-serif',
   											'textOverflow': 'ellipsis',
   											'overflow': 'hidden',
   	   									'maxWidth': 0
   					}
						
						
				)	
		)
	
	
		
		
	return to_return,wc_fig,db_content,fig_list
	
# get bd info
@app.callback(Output('phone-numbers','children'),
              Output('datatable-div','children'),            
				  
             [Input('load-bd','n_clicks'),
              State('databases-options','value'),
              State('date-range','start_date'),
              State('date-range','end_date')])
def get_numbers(n_clicks,bd,start_date,end_date):
	
	start_date_ts= datetime.datetime.timestamp(datetime.datetime.strptime(start_date,"%Y-%m-%d"))
	end_date_ts= datetime.datetime.timestamp(datetime.datetime.strptime(end_date,"%Y-%m-%d"))
	response=''
	
	div_data_table_list=[]
	if bd is not None:
		conn=sqlite3.connect(f'{path}/{bd}', check_same_thread=False)
		db_obj.conn=conn
		try:
			query="""SELECT * FROM messages """
			res_df=pd.read_sql(query,conn)
			res_df=res_df[(res_df['timestamp']>=1000*start_date_ts) & (res_df['timestamp']<=1000*end_date_ts) ]
			message_count=res_df[res_df['key_from_me']==0].groupby(['key_remote_jid']).count().reset_index()[['key_remote_jid','key_from_me']]\
			.sort_values(by='key_from_me',ascending=False)
			
			message_count=message_count.rename(columns={'key_from_me':'Cant. mensajes','key_remote_jid':'Teléfono'})
			columns_datatable=[{'name':i,'id':i} for i in message_count.columns]
			content_datatable=message_count.to_dict('records')
			div_data_table_list.append(
					dash_table.DataTable(id='msg-ranking',
						columns=columns_datatable,
						data=content_datatable,
						
						export_format='xlsx',
						style_table={'overflowY':'auto','overflowX':'auto','width':'auto'},
						style_header={'backgroundColor': '#393F56','fontWeight': 'bold','color':'white'},
						page_size=5,
						style_cell={'textAlign': 'left','font-family': 'Arial,Helvetica,sans-serif',
   											'textOverflow': 'ellipsis',
   											'overflow': 'hidden',
   											'maxWidth': 0
   					}
						
						
					)
			)
			numbers=list(res_df['key_remote_jid'].unique())
			
			response=html.Div([
			
			   html.Br(),
				dcc.Dropdown(id='numbers-menu',options=[{'label':i,'value':i} for i in numbers],multi=True),
				dcc.Store(id='dates-dict',data={'start_ts':1000*start_date_ts,'end_ts':1000*end_date_ts})
				
			
			],style={'width':'50%'})
		except Exception as e:
			response='⛔ '+str(e)+' ⛔'
	
	return response,div_data_table_list

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