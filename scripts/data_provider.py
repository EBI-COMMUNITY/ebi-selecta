import mysql.connector
from PipelineAttributes import stages
from selectadb import properties



def copy_file(infile,outfile):
	print "test"
	
def get_connection(db_user,db_password,db_host,db_database):
		conn = mysql.connector.connect(user=db_user, password=db_password, host=db_host,database=db_database)
		return conn

def get_list(conn):
	stage_name='data_provider'
	query="select process_id,selection_id from process_stages where stage_start is null and stage_name='%s'"%stage_name
	cursor = conn.cursor()
	cursor.execute(query)
	
	data_provider_list=list()
	for (process_id, selection_id) in cursor:
		 print stage_name
		 stage=stages(process_id,selection_id,stage_name)
		 data_provider_list.append(stage)
		
	return data_provider_list

def get_properties(property_file):
	return property_file


if __name__ == '__main__':
	prop=properties('properties.txt')
	conn=get_connection(prop.dbuser,prop.dbpass,prop.dbhost,prop.dbanme)
	data_provider_list=get_list(conn)
	for stage in data_provider_list:
		if stage.check_started()==False:
			print "To be started jobs"
			print dat.process_id,dat.selection_id,dat.stage_list
		
	prop=properties('properties.txt')
	
	
	
	
	
	