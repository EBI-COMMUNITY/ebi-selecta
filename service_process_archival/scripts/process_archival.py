#!/usr/bin/env python3

#import MySQLdb
import pymysql as MySQLdb
from selectadb import properties
from PipelineAttributes import stages
from PipelineAttributes import default_attributes
import shutil
import argparse
import time
from reporting import Process_report
import psycopg2
import sys

__author__ = 'Nima Pakseresht, Blaise Alako'


global error_list

error_list=''

def get_connection(db_user,db_password,db_host,db_database , db_port):
        conn = psycopg2.connect(host=db_host, database=db_database, user=db_user, password=db_password, port=db_port)
        return conn

def get_args():

    global properties_file  
    # Assign description to the help doc
    parser = argparse.ArgumentParser(
        description='Script remove the processed submissions to make free space for incoming submissions.')
    parser.add_argument('-p', '--properties_file', type=str, help='Please provide the properties file that is required by SELECTA system', required=True)
    args = parser.parse_args()
    properties_file=args.properties_file


def process_arguments(args):
	"""
	process_arguments : this process the arguments passed
	on the command line
	:param args: list of arguments
	:return: return the configuration file
	"""
	global properties_file
	""" First, construct the parser """
	parser = argparse.ArgumentParser(description='Selection_to_attribute.py removes the processed '
												 'submissions to make free space for incoming submissions.')
	"""Lets us add the first argument """
	parser.add_argument('-p',
						'--properties_file',
						type=str,
						help="Please provide the properties file that is required by SELECTA system",
						dest='properties_file',
						required=True)
	parser.add_argument('--db_live',
						help='Check whether PostGresDB is live and accepting\
								connection', action='store_true')
	options = parser.parse_args(args)
	""" Return the options """
	return options


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
           "c.process_id)").format(process_archival_stage,data_provider_stage,core_executor_stage,analysis_reporter_stage)
    print(query)
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

def archDirectory(src, dest):
    try:
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns('*.fastq'))
        shutil.rmtree(src, ignore_errors=True)
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
        message = 'Directory not copied. Error: {}'.format(e)
        error_list.append(message.replace("'", ""))
        print(message)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)
        message = 'Directory not copied. Error: {}'.format(e)
        error_list.append(message.replace("'", ""))
        print(message)


def execute(process_id,prop):
    src=prop.workdir+process_id
    dest = prop.archivedir+process_id
    print('Source dir: {}\nDestination: {}'.format(src, dest))
    archDirectory(src, dest)


if __name__ == '__main__':
    now = time.strftime("%c")
    print("process_archival started {}".format(now))
    error_list=list()
    #get_args()
    #prop=properties(properties_file)
    options = process_arguments(sys.argv[1:])
    properties_file = options.properties_file
    prop = properties(properties_file)
    lsf = prop.lsf
    if (options.db_live):
        try:
            print('-' * 100)
            print("PostGres DB is live and accepting connection")
            conn = get_connection(prop.dbuser, prop.dbpassword, prop.dbhost, prop.dbname, prop.dbport)
            print('-' * 100)
        except:
            print(sys.exc_info())
    else:
        conn=get_connection(prop.dbuser,prop.dbpassword,prop.dbhost,prop.dbname, prop.dbport)
        process_archival_list=get_list(conn)
        print('-'*100)
        print("Analysis to archive:{}".format(len(process_archival_list)))
        for exe in process_archival_list:
            print('.'*100)
            print("{} Archive check started:".format(exe.process_id))
            if exe.check_started(conn)==False:
               exe.set_started(conn)
               execute(exe.process_id,prop)
               if len(error_list)!=0:
                    final_errors = ' '.join(str(v).replace("'", "") for v in error_list)
                    exe.set_error(conn,final_errors)
               else:
                    exe.set_finished(conn)
                    exe.process_report_set_finished(conn)
                    now = time.strftime("%c")
                    print("process of {} archival finished on {}".format(exe.process_id,now))
                    error_list=list()
            else:
                print("{} Archiving Already started........".format(exe.process_id))
        now = time.strftime("%c")
        message="ARCHIVAL FINISHED {}".format(now)
        print('*'*50)
        print(message)
        print('*'*50)
        conn.close()
