#!/usr/bin/env python3

import MySQLdb
import pymysql
from selectadb import properties
from PipelineAttributes import stages
from PipelineAttributes import default_attributes
import shutil
import argparse
import time

global error_list

error_list=''

def get_connection(db_user,db_password,db_host,db_database):
        conn = MySQLdb.connect(user=db_user, passwd=db_password, host=db_host,db=db_database)
        return conn

def get_args():

    global properties_file  
    # Assign description to the help doc
    parser = argparse.ArgumentParser(
        description='Script remove the processed submissions to make free space for incoming submissions.')
    parser.add_argument('-p', '--properties_file', type=str, help='Please provide the properties file that is required by SELECTA system', required=True)
    args = parser.parse_args()
    properties_file=args.properties_file

def get_list(conn):
    data_provider_stage='data_provider'
    core_executor_stage='core_executor'
    analysis_reporter_stage='analysis_reporter'
    process_archival_stage='process_archival'
    query=("select process_id,selection_id from process_stages where stage_start is null and "
           "stage_end is null and stage_error is null and stage_name='{}' and "
           "process_id in (select distinct(a.process_id) from process_stages a,process_stages b, "
           "process_stages c  where a.stage_start is not null and a.stage_end is not null and "
           "a.stage_error is null and a.stage_name='{}' and b.stage_start is not null "
           "and b.stage_end is not null and b.stage_error is null and b.stage_name='{}' "
           "and c.stage_start is not null and c.stage_end is not null and c.stage_error is null "
           "and c.stage_name='{}' and a.process_id=b.process_id and b.process_id= "
           "c.process_id").format(process_archival_stage,data_provider_stage,core_executor_stage,analysis_reporter_stage)
    cursor = conn.cursor()
    cursor.execute(query)
    process_archival_list=list()
    for (process_id, selection_id) in cursor:
         stage=stages(process_id,selection_id,process_archival_stage)
         process_archival_list.append(stage)
    return process_archival_list



def delete(dir):
    try:
        shutil.rmtree(dir)
    except shutil.Error as e:
        message='Directory not copied. Error: {}'.format(e)
        error_list.append(message.replace("'",""))
        print(message)


def execute(process_id,prop):
    workdir=prop.workdir+process_id+"/"
    delete(workdir)


if __name__ == '__main__':
    now = time.strftime("%c")
    print("process_archival has been started {}".format(now))
    error_list=list()
    get_args()
    prop=properties(properties_file)
    conn=get_connection(prop.dbuser,prop.dbpassword,prop.dbhost,prop.dbname)
    process_archival_list=get_list(conn)
    for exe in process_archival_list:
        if exe.check_started(conn)==False:
           exe.set_started(conn)
           execute(exe.process_id,prop)
           if len(error_list)!=0:
                final_errors = ' '.join(str(v).replace("'", "") for v in error_list)
                exe.set_error(conn,final_errors)
           else:
                exe.set_finished(conn)
                now = time.strftime("%c")
                print("procees of {} archival finished at {}".format(exe.process_id,now))
        error_list=list()
    now = time.strftime("%c")
    print("process_archival has been finished {}".format(now))
