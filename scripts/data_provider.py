#!/usr/bin/env python3

import MySQLdb
#import mysql.connector
import pymysql
import os
import base64
from PipelineAttributes import stages
from selectadb import properties
import subprocess
from PipelineAttributes import default_attributes
import sys
import argparse


global error_list
error_list=''


def get_args():

    global properties_file  
    # Assign description to the help doc
    parser = argparse.ArgumentParser(
        description='Script rrmove the processed submissions to make free space for incoming submissions.')
    parser.add_argument('-p', '--properties_file', type=str, help='Please provide the properties file that is required by SELECTA system', required=True)
    args = parser.parse_args()
    properties_file=args.properties_file
	
def get_connection(db_user,db_password,db_host,db_database):
		conn = MySQLdb.connect(user=db_user, passwd=db_password, host=db_host,db=db_database)
		return conn

def get_list(conn):
	stage_name='data_provider'
	query="select process_id,selection_id from process_stages where stage_start is null and stage_end is null and stage_name='{}'".format(stage_name)
	cursor = conn.cursor()
	cursor.execute(query)
	
	data_provider_list=list()
	for (process_id, selection_id) in cursor:
		 
		 stage=stages(process_id,selection_id,stage_name)
		 data_provider_list.append(stage)
		
	return data_provider_list


def get_file_names(conn,process_id):
	value=default_attributes.get_attribute_value(conn,'fastq_files',process_id)
	files=list()
	if ";" in value:
		files=value.split(";")
	else:
		files.append(value)
	
	return files
	
def get_datahub_names(conn,process_id):
	value=default_attributes.get_attribute_value(conn,'datahub',process_id)
	return value
	
	
def create_processing_dir(directory):
	if not os.path.exists(directory):
		os.makedirs(directory)


def get_datahub_account_password(conn,account_id):
		query='select password from account where account_id="{}"'.format(account_id)
		cursor = conn.cursor()
		cursor.execute(query)
		for password in cursor:
			passw=password[0]
			print('*'*100)
			
			print(base64.b64decode(passw[::-1]).decode())
			print('*'*100)
		return base64.b64decode(passw[::-1]).decode()
	


def download_datahub_file(account_name,password,files,outdir):
		for file in files:
			outputfile=outdir+'/'+os.path.basename(file)
			print(file)
			url="ftp://{}:{}@ftp.dcc-private.ebi.ac.uk/data/{}".format(account_name,password,file)
			command="wget -t 2 {} -O {}".format(url,outputfile)
			print('*'*100)
			print('*'*100)
			print(command)
			sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = sp.communicate()
			if out:
				print("standard output of subprocess:")
				print(out)
			if err:
				print("standard error of subprocess:")
				print(err)
			if sp.returncode!=0:
				error_list.append(err)
				print(err, end="", file=sys.stderr)
		
		

if __name__ == '__main__':
	error_list=list()
	get_args()
	prop=properties(properties_file)
	conn=get_connection(prop.dbuser,prop.dbpassword,prop.dbhost,prop.dbname)
	data_provider_list=get_list(conn)
	for data_provider_stage in data_provider_list:
		if data_provider_stage.check_started(conn)==False:
			print("\nTo be started job: process_id:{} collection id: {} dataprovider id: {} ".format(data_provider_stage.process_id,data_provider_stage.selection_id,data_provider_stage.stage_list))
			data_provider_stage.set_started(conn)
			process_dir=prop.workdir+data_provider_stage.process_id
			print("Creating process directory:{}".format(process_dir))
			create_processing_dir(process_dir)
			account_name=get_datahub_names(conn,data_provider_stage.process_id)
			print("account to be processed:{}".format(account_name))
			files=get_file_names(conn,data_provider_stage.process_id)
			print("Files to be downloaded:{}".format(files))
			pw=get_datahub_account_password(conn,account_name)
			download_datahub_file(account_name,pw,files,process_dir) 
			if len(error_list)!=0:
				final_errors=' '.join(str(v).replace("'", "") for v in error_list)
				data_provider_stage.set_error(conn,final_errors)
			else:
				data_provider_stage.set_finished(conn)
		error_list=list()
				
	conn.close()
		
		
	
	
	
	
	
	
	
