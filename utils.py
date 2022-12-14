import base64
import sqlite3
import os
from wordcloud import WordCloud
from io import BytesIO
import plotly.express as px
import pandas as pd
import re

class dummy_connection:
	def __init__(self,conn):
		self.conn=conn


class text_cleaner:
	def __init__(self,text):
		self.text=text
	def remove_accents(self):
		vowels=[('a','á'),('e','é'),('i','í'),('o','ó'),('u','ú')]
		for v in vowels:
			self.text=self.text.replace(v[1],v[0])
	def lower_text(self):
		self.text=self.text.lower()
	def remove_prepositions(self):
		spanish_prep=['a','desde','hasta','para','por','segun','sin','sobre','tras','antes','en','la','el','durante',\
							'despues','hace','contra','cerca','o','ya','un','y','lo','de','con','que','del','lo','gracia',\
							'gracias','muchas','hola','buenos','dias','saludo','buenas','a','e','i','o','u','buen','dia',\
							'es','dia','se','al','asi','cual','si','no','me','tu','pero','los','las','como','tardes']
		text_list=self.text.split()
		text_list=[i.strip() for i in text_list]
		text_list=[i for i in text_list if i not in spanish_prep]
		
	
		#print(text_list)
		self.text=' '.join(text_list)
	def remove_punctuation(self):
		self.text=re.sub(r'[^\w\s]','',self.text)
		
	



def upload_file(path,filename,content):
	data=content.encode("utf8").split(b";base64,")[1]
	with open(f'{path}/{filename}','wb') as fp:
		
		fp.write(base64.decodebytes(data))
	
	
def list_files(path):
	file_list=[]
	for fn in os.listdir(path):
		
		if fn.endswith('.db'):
			file_list.append(fn)
	return file_list

def create_word_cloud(df):
	text=' '.join(df['data'].to_list())
	
	cleaner_obj=text_cleaner(text)
	cleaner_obj.lower_text()
	cleaner_obj.remove_accents()
	cleaner_obj.remove_prepositions()
	cleaner_obj.remove_punctuation()
	try:
		wordcloud = WordCloud(max_font_size=40,background_color="white").generate(cleaner_obj.text)
	except:
		wordcloud = WordCloud(max_font_size=40,background_color="white").generate('vacío')
		
	#wordcloud.to_file('test.png')
	# export option1 (faster)
	
	img=BytesIO()
	wordcloud.to_image().save(img,format='PNG')
	return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())
	
	#export option2 (easier but slower)	
	
	#img=wordcloud.to_image()
	#fig=px.imshow(img)
	
	#return fig
def bar_plot_words(df):
	text=' '.join(df['data'].to_list())
	cleaner_obj=text_cleaner(text)
	cleaner_obj.lower_text()
	cleaner_obj.remove_accents()
	cleaner_obj.remove_prepositions()
	cleaner_obj.remove_punctuation()

	df=pd.DataFrame({'words':cleaner_obj.text.split()})
	df_count=df['words'].value_counts().reset_index().sort_values(by='words',ascending=False)[0:100]
	fig=px.bar(df_count,x='index',y='words')
	
	return fig
	
	


	
	


		
		
		
