import base64
import sqlite3
import os
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

class dummy_connection:
	def __init__(self,conn):
		self.conn=conn