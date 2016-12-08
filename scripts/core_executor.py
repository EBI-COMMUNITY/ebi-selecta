import mysql.connector
from PipelineAttributes import stages
from selectadb import properties
from PipelineAttributes import default_attributes
from pipelines import dtu_cge
import os
import hashlib

def get_connection(db_user,db_password,db_host,db_database):
        conn = mysql.connector.connect(user=db_user, password=db_password, host=db_host,database=db_database)
        return conn

def get_list(conn):
    #stage_name='core_executor'
    data_provider_stage='data_provider'
    core_executor_stage='core_executor'
    analysis_reporter_stage='analysis_reporter'
    process_archival_stage='process_archival'
    
    
    #query="select process_id,selection_id from process_stages where stage_start is null and stage_name='%s' and process_id not in \
    #      (select distinct(process_id) from process_stages where  (stage_start is not null or stage_end is not null) and stage_name in \
    #      ('analysis_reporter','process_archival')) and process_id in \
    #      (select distinct(process_id) from process_stages where stage_start is not null and \
    #      stage_end is not null and stage_error is null)"%stage_name
          
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
        
    
def insert_into_process_attributes(conn,process_id,attribute_key,attribute_value):
        
    if process_id!="" and attribute_value!="":
        query="INSERT INTO process_attributes (process_id,attribute_key,attribute_value) values('%s','%s','%s')"%(process_id,attribute_key,attribute_value)
        cursor = conn.cursor()
            
        try:
            cursor.execute(query)
                #time.sleep(1)
            conn.commit()
         
        except:
            print "Cannot insert:"
            message=str(sys.exc_info()[1])
            print "Exception: %s"%message
            conn.rollback()    
    
    
def execute_dtu_cge(process_id,selection_id,prop):
    fq1=os.path.basename(default_attributes.get_attribute_value(conn,'fastq1',process_id))
    fq2=os.path.basename(default_attributes.get_attribute_value(conn,'fastq2',process_id))
    pair=default_attributes.get_attribute_value(conn,'pair',process_id)
    run_accession=default_attributes.get_attribute_value(conn,'run_accession',process_id)
    database_dir=prop.dtu_cge_databases
    workdir=prop.workdir+process_id+"/"
    sequencing_machine='Illumina'
    
    cge=dtu_cge(fq1,fq2,database_dir,workdir,sequencing_machine, pair,run_accession)
    print cge.fq1,cge.fq2,cge.database_dir,cge.workdir,cge.sequencing_machine,cge.pair
    gzip_file,tab_file=cge.execute()
    gzip_file_md5=hashlib.md5(open(gzip_file, 'rb').read()).hexdigest()
    tab_file_md5=hashlib.md5(open(tab_file, 'rb').read()).hexdigest()
    #insert_into_process_attributes(conn,process_id,'gzip_analysis_file',gzip_file)
    #insert_into_process_attributes(conn,process_id,'tab_analysis_file',tab_file)
    insert_into_process_attributes(conn,process_id,'gzip_analysis_file_md5',gzip_file_md5)
    insert_into_process_attributes(conn,process_id,'tab_analysis_file_md5',tab_file_md5)

if __name__ == '__main__':
    prop=properties('properties.txt')
    conn=get_connection(prop.dbuser,prop.dbpassword,prop.dbhost,prop.dbname)
    core_executor_list=get_list(conn)
    for exe in core_executor_list:
        execute(conn,exe.process_id,exe.selection_id,prop)
        
        