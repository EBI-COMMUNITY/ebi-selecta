#!/usr/bin/python
import sys
#sys.path.append('../resources'
import time
import subprocess
import base64
import os
from _ast import alias
sys.path.append('../scripts')
import mysql.connector
import ftplib
from selectadb import properties
from sra_objects import analysis_pathogen_analysis
from sra_objects import analysis_file
from sra_objects import submission
from PipelineAttributes import stages
from PipelineAttributes import default_attributes
from lxml import etree


__author__ = 'Nima Pakseresht'

def get_list(conn):
	
	data_provider_stage='data_provider'
	core_executor_stage='core_executor'
	analysis_reporter_stage='analysis_reporter'
	process_archival_stage='process_archival'
	
	query="select process_id,selection_id from process_stages where stage_start is null and stage_end is null and stage_error \
		   is null and stage_name='%s' and process_id not in (select distinct(process_id) from process_stages where \
		   (stage_start is not null or stage_end is not null) and stage_name='%s') and process_id in \
			(select distinct(process_id) from process_stages where stage_start is not null and stage_end is not null \
			 and stage_error is null and stage_name='%s') and process_id in  (select distinct(process_id) \
			  from process_stages where stage_start is not null and stage_end is not null and stage_error is \
			   null and stage_name='%s')"%(analysis_reporter_stage,process_archival_stage,data_provider_stage,core_executor_stage)

	cursor = conn.cursor()
	cursor.execute(query)
	
	analysis_reporter_list=list()
	for (process_id, selection_id) in cursor:
		 
		 stage=stages(process_id,selection_id,analysis_reporter_stage)
		 analysis_reporter_list.append(stage)
		
	return analysis_reporter_list




def get_connection(db_user,db_password,db_host,db_database):
		conn = mysql.connector.connect(user=db_user, password=db_password, host=db_host,database=db_database)
		return conn

def calculateMd5(file):
	return  hashlib.md5(open(file, 'rb').read()).hexdigest()
	
	
		
		
def create_analysis_xml(conn,analysis,prop,attributes,analysis_xml):
		 print analysis.process_id,analysis.selection_id
		 #attributes=default_attributes.get_all_attributes(conn,analysis.process_id)
		 run_accession=attributes['run_accession']   
		 gzip_analysis_file=attributes['gzip_analysis_file']
		 tab_analysis_file=attributes['tab_analysis_file']
		 gzip_analysis_file_md5=attributes['gzip_analysis_file_md5']
		 tab_analysis_file_md5=attributes['tab_analysis_file_md5']
		 pipeline_name=attributes['pipeline_name']
		 study_accession=attributes['study_accession']
		 scientific_name=attributes['scientific_name']
		 print run_accession,gzip_analysis_file,gzip_analysis_file_md5,tab_analysis_file,tab_analysis_file_md5
	 
		 analysis_files=list()
		 file1=analysis_file(os.path.basename(tab_analysis_file),'tab',tab_analysis_file_md5)
		 file2=analysis_file(os.path.basename(gzip_analysis_file),'other',gzip_analysis_file_md5)
		 analysis_files.append(file1)
		 analysis_files.append(file2)
	 
		 centre_name="COMPARE"
		 alias=pipeline_name.lower()+"_"+analysis.process_id.lower()+"-"+str(analysis.selection_id)
		 print 'alias:',alias
		 analysis_date=time.strftime("%Y-%m-%dT%H:%M:%S")
		 title="COMPARE project pathogen analysis using %s pipeline on read data %s"%(pipeline_name,run_accession)
		 description="As part of the COMPARE project submitted data %s organism name '%s' has been processed by %s pipeline and result has been submitted to ENA archive."%(run_accession,scientific_name,pipeline_name)
	 
		 analysis_obj=analysis_pathogen_analysis(alias,centre_name,run_accession,study_accession,pipeline_name,analysis_date,analysis_files,title,description,analysis_xml)
		 analysis_obj.build_analysis()


def create_submission_xml(conn,analysis,analysis_xml,submission_xml,action):
		 
		 alias="sub_"+analysis.process_id.lower()+"-"+str(analysis.selection_id)
		 centre_name='COMPARE'
		 schema='analysis'
		 submission_obj=submission(alias,centre_name,action,submission_xml,analysis_xml,schema)
		 submission_obj.build_submission()

#curl -F "SUBMISSION=@submission.xml"  -F "ANALYSIS=@analysis.xml" "https://www-test.ebi.ac.uk/ena/submit/drop-box/submit/?auth=ENA%20USERNAME%20PASSWORD

def get_account_pass(conn,user):
		query="select password from account where account_id='%s'"%user
		cursor = conn.cursor()
		cursor.execute(query)
		for password in cursor:
				 p=password[0]
		return base64.b64decode(p[::-1])

def uploadFileToEna(filename,user,passw):
		print "uploaing %s "%filename
		command="curl -T %s  ftp://webin.ebi.ac.uk --user %s:%s"%(filename,user,passw)
		sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = sp.communicate()
		if out:
			print "standard output of subprocess:"
			print out
		if err:
		   print "standard error of subprocess:"
		   print err
		print "returncode of subprocess:"
		print sp.returncode
	
	
		
def submitAnalysis(submission_xml,analysis_xml,user,passw):
		print "Analysis submission started:"
		print submission_xml,analysis_xml,user,passw
		command="curl -F \"SUBMISSION=@%s\" -F \"ANALYSIS=@%s\" \"https://www-test.ebi.ac.uk/ena/submit/drop-box/submit/?auth=ENA"%(submission_xml,analysis_xml)+'%20'+user+'%20'+passw+'\"'
		print command
		
		
		sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = sp.communicate()
		submission_error_messages=list()
		if out:
			print "standard output of subprocess:"
			print out
			root = etree.XML(out)
			root = etree.fromstring(out)
			
			for messages in root.findall('MESSAGES'):
				print messages 
				for mess in messages.findall('ERROR'):
					submission_error_messages.append(mess.text)
				#rank = messages.find('ERROR').text
				#name = messages.get('ERROR')
				#print name, rank
			#print(root.find(".//ERROR").tag)
			#print(root.get(".//ERROR"))
		if err:
		   print "standard error of subprocess:"
		   print err
		
		print "returncode of subprocess:",sp.returncode
		if len(submission_error_messages)!=0:
			for err in submission_error_messages:
				print "ERROR:",err
		return submission_error_messages,sp.returncode,out,err
		

if __name__ == '__main__':
	
	 prop=properties('../resources/properties.txt')
	 conn=get_connection(prop.dbuser,prop.dbpassword,prop.dbhost,prop.dbname)
	 analysis_reporter_list=get_list(conn)
	 for analysis in analysis_reporter_list:
	 	 attributes=default_attributes.get_all_attributes(conn,analysis.process_id)
	 	 analyst_webin=attributes['analyst_webin']
	 	 passw=get_account_pass(conn,analyst_webin)
	 	 gzip_analysis_file=attributes['gzip_analysis_file']
		 tab_analysis_file=attributes['tab_analysis_file']
		 #uploadFileToEna(gzip_analysis_file,analyst_webin,passw)
		 #uploadFileToEna(tab_analysis_file,analyst_webin,passw)
	 	 analysis_xml=prop.workdir+analysis.process_id+'/analysis.xml'
	 	 submission_xml=prop.workdir+analysis.process_id+'/submission.xml'
	 	 create_analysis_xml(conn,analysis,prop,attributes,analysis_xml)
	 	 action='VALIDATE'
	 	 analysis_xml_name=os.path.basename(analysis_xml)
	 	 create_submission_xml(conn,analysis,analysis_xml_name,submission_xml,action)
	 	 submission_error_messages,sp.returncode,out,err=submitAnalysis(submission_xml,analysis_xml,analyst_webin,passw)
		
	 
	
   
