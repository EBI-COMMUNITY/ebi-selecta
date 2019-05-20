#!/usr/bin/env python3

import pymysql as MySQLdb
from PipelineAttributes import stages
from selectadb import properties
from PipelineAttributes import default_attributes

from pipelines import DtuCge
from pipelines import EmcSlim
from pipelines import UAntwerpBacpipe
import os
import sys
import hashlib
import argparse
from bsub import bsub
import re
import subprocess as sp
import time
from joblib import Parallel, delayed
import multiprocessing
import datetime
import itertools
import random
from collections import deque
from tabulate import tabulate
import psycopg2



__author__='Blaise Alako'

"""
Purpose: Report on the SELECTA processing pipeline data transit. 
Make use of the 
1) process_report table in SELECTADB_production
2) Analysis table at ERAPRO
"""


def get_args():
    global properties_file
    # Assign description to the help doc
    parser = argparse.ArgumentParser(
        description='Reports on the SELECTA processing pipeline data transit.')
    parser.add_argument('-p', '--properties_file', type=str,
                        help='Please provide the properties file that is required by SELECTA system', required=True)
    args = parser.parse_args()
    properties_file = args.properties_file


def get_connection(db_user, db_password, db_host, db_database, db_port):
    """ Some core_executor takes over 48 hour to complete hence increase of mysql connect_time out variable, """
    conn = psycopg2.connect(host=db_host, database=db_database, user=db_user, password=db_password, port=db_port)
    return conn


def process_report(conn):
    query = "select  datahub, PipelineName, studyAccession, sum(RunProcessed) as RunProcessed, sum(DoubleEnd) as DoubleEnd, sum(SingleEnd) as SingleEnd, \
    sum(AnalysisSubmitted) as AnalysisSubmitted, sum(runSubmitted) as runSubmitted from(select selection_id,\
    datahub, pipeline_name PipelineName, study_accession studyAccession, runs_processed as RunProcessed, \
    CASE WHEN attribute_key = 'pair' and attribute_value='True' THEN runs_processed ELSE 0 END AS DoubleEnd, \
    CASE WHEN attribute_key = 'pair' and attribute_value='False' THEN runs_processed ELSE 0 END AS SingleEnd, \
    analysis_submitted AnalysisSubmitted, run_submitted runSubmitted \
    /*A_run_archived runArchived*/\
    from (select P.selection_id, P.datahub, P.pipeline_name, tmptbl.study_accession, tmptbl.attribute_key, tmptbl.attribute_value, tmptbl.runs_processed , tmptbl.analysis_submitted, tmptbl.run_submitted from \
    (SELECT A.selection_id, A.study_accession, B.attribute_key, B.attribute_value, count(A.study_accession) as runs_processed, count(A.analysis_id) as analysis_submitted, count(A.submission_id) as run_submitted \
    FROM process_report as A join process_attributes as B on A.process_id=B.process_id \
    where B.attribute_key='pair'  group by  A.selection_id, A.study_accession, B.attribute_key, B.attribute_value) tmptbl join \
    process_selection P on tmptbl.selection_id=P.selection_id) as processed \
    GROUP BY selection_id, study_accession, attribute_value, attribute_key) as summary \
    GROUP BY selection_id, datahub, studyAccession;"
    #print('-'*100)
    #print(query)
    #print('-'*100)
    error_list=[]
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        cursor.close()
    except psycopg2.ProgrammingError as exc:
        error_list.append(exc.message)
        print(exc.message)
    except psycopg2.InterfaceError as exc:
        error_list.append(exc.message)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
    except:
        print("Cannot insert:")
        message = str(sys.exc_info()[1])
        error_list.append(message)
        print("Exception: {}".format(message))
        conn.rollback()
    return cursor.fetchall()


def analysis_report(conn):
    query = "select selection_id, study_accession, analysis_id, submission_id from process_report \
    where process_report_start_time is not null and analysis_id is not null or submission_id is not null"
    #print(query)
    error_list=[]
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        cursor.close()
    except psycopg2.ProgrammingError as exc:
        error_list.append(exc.message)
        print(exc.message)
    except psycopg2.InterfaceError as exc:
        error_list.append(exc.message)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
    except:
        print("Cannot insert:")
        message = str(sys.exc_info()[1])
        error_list.append(message)
        print("Exception: {}".format(message))
        conn.rollback()
    return cursor.fetchall()


if __name__ == '__main__':
    get_args()
    prop = properties(properties_file)
    conn = get_connection(prop.dbuser, prop.dbpassword, prop.dbhost, prop.dbname, prop.dbport)
    process_report_list = process_report(conn)
    #print(process_report_list)
    report=list()
    for row in (process_report_list):
        report.append(row)
    print(tabulate(report, headers=['datahub', 'PipelineName', 'studyAccession',  'RunProcessed',  'DoubleEnd', 'SingleEnd','AnalysisSubmitted', 'runSubmitted']))
