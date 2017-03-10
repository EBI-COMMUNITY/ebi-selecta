#!/usr/bin/python

import MySQLdb
import mysql.connector
from PipelineAttributes import stages
from selectadb import properties
from PipelineAttributes import default_attributes
from pipelines import dtu_cge
from pipelines import emc_slim
import os
import sys
import hashlib
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

    data_provider_stage='data_provider'
    core_executor_stage='core_executor'
    analysis_reporter_stage='analysis_reporter'
    process_archival_stage='process_archival'
    
          
    query="select process_id,selection_id from process_stages where stage_start is null and stage_end is null and stage_error is \
           null and stage_name='%s' and process_id not in (select distinct(process_id) from process_stages where \
          (stage_start is not null or stage_end is not null) and stage_name in ('%s','%s')) \
           and process_id in (select distinct(process_id) from process_stages where stage_start is not null and stage_end \
            is not null and stage_error is null and stage_name='%s')"%(core_executor_stage,analysis_reporter_stage,process_archival_stage,data_provider_stage)

    cursor = conn.cursor()
    cursor.execute(query)
    
    core_executor_list=list()
    for (process_id, selection_id) in cursor:
         
         stage=stages(process_id,selection_id,core_executor_stage)
         core_executor_list.append(stage)
        
    return core_executor_list

def execute(conn,process_id,selection_id,prop):
    pipeline_name=default_attributes.get_attribute_value(conn,'pipeline_name',process_id)
    print pipeline_name, process_id
    if pipeline_name.upper()=='DTU_CGE':
        execute_dtu_cge(process_id,selection_id,prop)
    elif pipeline_name.upper()=='EMC_SLIM':
        execute_emc_slim(process_id,selection_id,prop)
        
    
def update_process_attributes(conn,process_id,attribute_key,attribute_value):
        
    if process_id!="" and attribute_value!="":
        #query="INSERT INTO process_attributes (process_id,attribute_key,attribute_value) values('%s','%s','%s')"%(process_id,attribute_key,attribute_value)
        query="update process_attributes set attribute_value='%s' where process_id='%s' and attribute_key='%s'"%(attribute_value,process_id,attribute_key)
        cursor = conn.cursor()
            
        try:
            cursor.execute(query)
                #time.sleep(1)
            conn.commit()
         
        except:
            print "Cannot insert:"
            message=str(sys.exc_info()[1])
            error_list.append(message)
            print "Exception: %s"%message
            conn.rollback()    
    
    
def execute_dtu_cge(process_id,selection_id,prop):
    fq1=os.path.basename(default_attributes.get_attribute_value(conn,'fastq1',process_id))
    fq2=os.path.basename(default_attributes.get_attribute_value(conn,'fastq2',process_id))
    pair=default_attributes.get_attribute_value(conn,'pair',process_id)
    run_accession=default_attributes.get_attribute_value(conn,'run_accession',process_id)
    database_dir=prop.dtu_cge_databases
    workdir=prop.workdir+process_id+"/"
    print "Test:"+workdir
    sequencing_machine='Illumina'
    
    cge=dtu_cge(fq1,fq2,database_dir,workdir,sequencing_machine, pair,run_accession)
    print cge.fq1,cge.fq2,cge.database_dir,cge.workdir,cge.sequencing_machine,cge.pair
    gzip_file,tab_file,error_message=cge.execute()
    if error_message!='':
        error_list.append(error_message)
    gzip_file_md5=hashlib.md5(open(gzip_file, 'rb').read()).hexdigest()
    tab_file_md5=hashlib.md5(open(tab_file, 'rb').read()).hexdigest()
    update_process_attributes(conn,process_id,'gzip_analysis_file',gzip_file)
    update_process_attributes(conn,process_id,'tab_analysis_file',tab_file)
    update_process_attributes(conn,process_id,'gzip_analysis_file_md5',gzip_file_md5)
    update_process_attributes(conn,process_id,'tab_analysis_file_md5',tab_file_md5)
    return error_list

def execute_emc_slim(process_id,selection_id,prop):
    fq1=os.path.basename(default_attributes.get_attribute_value(conn,'fastq1',process_id))
    fq2=os.path.basename(default_attributes.get_attribute_value(conn,'fastq2',process_id))
    pair=default_attributes.get_attribute_value(conn,'pair',process_id)
    run_accession=default_attributes.get_attribute_value(conn,'run_accession',process_id)
    #TODO:  not sure needed by SLIM
    workdir=prop.workdir+process_id+"/"
    print "Test:"+workdir
    #TODO: sequencing_machine shall be available in the parameters
    sequencing_machine='Illumina'
    
    slim=emc_slim(fq1,fq2,prop.emc_slim_property_file,workdir,sequencing_machine, pair,run_accession,prop.emc_slim_program)
    print slim.fq1,slim.fq2,slim.emc_slim_property_file,slim.workdir,slim.sequencing_machine,slim.pair,slim.run_accession,slim.emc_slim_program
    gzip_file,tab_file,error_message=slim.execute()
    if error_message!='':
        error_list.append(error_message)
    else: 
        gzip_file_md5=hashlib.md5(open(gzip_file, 'rb').read()).hexdigest()
        tab_file_md5=hashlib.md5(open(tab_file, 'rb').read()).hexdigest()
        update_process_attributes(conn,process_id,'gzip_analysis_file',gzip_file)
        update_process_attributes(conn,process_id,'tab_analysis_file',tab_file)
        update_process_attributes(conn,process_id,'gzip_analysis_file_md5',gzip_file_md5)
        update_process_attributes(conn,process_id,'tab_analysis_file_md5',tab_file_md5)
    return error_list

if __name__ == '__main__':
    error_list=list()
    get_args()
    prop=properties(properties_file)
    #prop=properties('../resources/properties.txt')
    conn=get_connection(prop.dbuser,prop.dbpassword,prop.dbhost,prop.dbname)
    core_executor_list=get_list(conn)
    for exe in core_executor_list:
        if exe.check_started(conn)==False:
           exe.set_started(conn)
           execute(conn,exe.process_id,exe.selection_id,prop)
           if len(error_list)!=0:
               final_errors='\n'.join(error_list) 
               exe.set_error(conn,final_errors) 
           else:
               exe.set_finished(conn) 
        error_list=list()
        
        
