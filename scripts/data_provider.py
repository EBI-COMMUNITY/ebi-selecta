import mysql.connector
import os
import base64
from PipelineAttributes import stages
from selectadb import properties
from PipelineAttributes import default_attributes



def copy_file(infile,outfile):
	print "test"
	
def get_connection(db_user,db_password,db_host,db_database):
		conn = mysql.connector.connect(user=db_user, password=db_password, host=db_host,database=db_database)
		return conn

def get_list(conn):
	stage_name='data_provider'
	query="select process_id,selection_id from process_stages where stage_name='%s'"%stage_name
	cursor = conn.cursor()
	cursor.execute(query)
	
	data_provider_list=list()
	for (process_id, selection_id) in cursor:
		 
		 stage=stages(process_id,selection_id,stage_name)
		 data_provider_list.append(stage)
		
	return data_provider_list


def get_file_names(conn,process_id):
	value=default_attributes.get_attribute_value(conn,'fastq_files',stage.process_id)
	files=list()
	if ";" in value:
		files=value.split(";")
	else:
		files.append(value)
	
	return files
	
def get_datahub_names(conn,process_id):
	value=default_attributes.get_attribute_value(conn,'datahub',stage.process_id)
	return value
	
	
def create_processing_dir(directory):
	if not os.path.exists(directory):
		os.makedirs(directory)


def get_datahub_account_password(conn,account_id):
		query='select password from account where account_id="%s"'%account_id
		cursor = conn.cursor()
		cursor.execute(query)
		for password in cursor:
			passw=password[0]
		return base64.b64decode(passw[::-1])
	


def download_datahub_file(account_name,password,files,outdir):
		for file in files:
			outputfile=outdir+'/'+os.path.basename(file)
			url="ftp://%s:%s@ftp.dcc-private.ebi.ac.uk/data/%s"%(account_name,password,file)
			command="wget -t 2 %s -O %s"%(url,outputfile)
			#TODO: You need to check to see if the file has been downloaded or not here or somewhere else in the code /data/fastq
			print command
			#os.system(command)

if __name__ == '__main__':
	prop=properties('properties.txt')
	
	conn=get_connection(prop.dbuser,prop.dbpassword,prop.dbhost,prop.dbname)
	data_provider_list=get_list(conn)
	for stage in data_provider_list:
		if stage.check_started(conn)==False:
			print "\nTo be started job: process_id:", stage.process_id,'collection id:',stage.selection_id,'stage name:',stage.stage_list
			process_dir=prop.workdir+stage.process_id
			print "Creating process directory:",process_dir
			account_name=get_datahub_names(conn,stage.process_id)
			print "account to be processed:",account_name
			files=get_file_names(conn,stage.process_id)
			print "Files to be downloaded:",files
			pw=get_datahub_account_password(conn,account_name)
			download_datahub_file(account_name,pw,files,process_dir)
			
		
		
	
	
	
	
	
	
	