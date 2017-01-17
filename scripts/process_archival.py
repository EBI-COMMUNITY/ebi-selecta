#!/usr/bin/python

import MySQLdb
import mysql.connector
from selectadb import properties


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






