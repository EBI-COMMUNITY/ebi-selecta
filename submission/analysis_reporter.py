#!/usr/bin/env python3
import sys
# sys.path.append('../resources'
import time
import subprocess
import base64
import os

sys.path.append('/home/ubuntu/tools/ebi-selecta/scripts')
import MySQLdb
import pymysql
import ftplib
from selectadb import properties
from sra_objects import analysis_pathogen_analysis
from sra_objects import analysis_file
from sra_objects import submission
from PipelineAttributes import stages
from PipelineAttributes import default_attributes
from lxml import etree
import argparse

__author__ = 'Nima Pakseresht'

global error_list
global log_file

error_list = ''
log_file = 'analysis_reporter.log'


# TODO: Code will get benefit from writing a log file
# TODO: Code also get benefit from checking the checksum of uploaded file.

def get_args():
    global properties_file
    # Assign description to the help doc
    parser = argparse.ArgumentParser(
        description='Script rrmove the processed submissions to make free space for incoming submissions.')
    parser.add_argument('-p', '--properties_file', type=str,
                        help='Please provide the properties file that is required by SELECTA system', required=True)
    args = parser.parse_args()
    properties_file = args.properties_file


def get_list(conn):
    data_provider_stage = 'data_provider'
    core_executor_stage = 'core_executor'
    analysis_reporter_stage = 'analysis_reporter'
    process_archival_stage = 'process_archival'

    query = (
        "select process_id,selection_id from process_stages where stage_start is null and stage_end is null and stage_error "
        "is null and stage_name='{}' and process_id not in (select distinct(process_id) from process_stages where "
        "(stage_start is not null or stage_end is not null) and stage_name='{}') and process_id in "
        "(select distinct(process_id) from process_stages where stage_start is not null and stage_end is not null "
        "and stage_error is null and stage_name='{}') and process_id in  (select distinct(process_id) "
        "from process_stages where stage_start is not null and stage_end is not null and stage_error is "
        "null and stage_name='{}')").format(analysis_reporter_stage, process_archival_stage, data_provider_stage,
                                            core_executor_stage)

    cursor = conn.cursor()
    cursor.execute(query)
    analysis_reporter_list = list()
    for (process_id, selection_id) in cursor:
        stage = stages(process_id, selection_id, analysis_reporter_stage)
        analysis_reporter_list.append(stage)
    return analysis_reporter_list


def get_connection(db_user, db_password, db_host, db_database):
    conn = MySQLdb.connect(user=db_user, passwd=db_password, host=db_host, db=db_database)
    return conn


def calculateMd5(file):
    return hashlib.md5(open(file, 'rb').read()).hexdigest()


def create_analysis_xml(conn, analysis, prop, attributes, analysis_xml):
    print(analysis.process_id, analysis.selection_id)
    run_accession = attributes['run_accession']
    gzip_analysis_file = attributes['gzip_analysis_file']
    tab_analysis_file = attributes['tab_analysis_file']
    gzip_analysis_file_md5 = attributes['gzip_analysis_file_md5']
    tab_analysis_file_md5 = attributes['tab_analysis_file_md5']
    pipeline_name = attributes['pipeline_name']
    study_accession = attributes['study_accession']
    scientific_name = attributes['scientific_name']
    sample_accession = attributes['sample_accession']
    print(run_accession, gzip_analysis_file, gzip_analysis_file_md5, tab_analysis_file, tab_analysis_file_md5)
    analysis_files = list()
    file1 = analysis_file(os.path.basename(tab_analysis_file), 'tab', tab_analysis_file_md5)
    file2 = analysis_file(os.path.basename(gzip_analysis_file), 'other', gzip_analysis_file_md5)
    analysis_files.append(file1)
    analysis_files.append(file2)
    centre_name = "COMPARE"
    alias = pipeline_name.lower() + "_" + analysis.process_id.lower() + "-" + str(analysis.selection_id)
    print('alias:', alias)
    analysis_date = time.strftime("%Y-%m-%dT%H:%M:%S")
    title = "COMPARE project pathogen analysis, using {} pipeline on read data {} from sample {}".format(pipeline_name,
                                                                                                         run_accession,
                                                                                                         sample_accession)
    description = "As part of the COMPARE project submitted data {} from sample {} organism name '{}' has been processed by {} pipeline.".format(
        run_accession, sample_accession, scientific_name, pipeline_name)
    analysis_obj = analysis_pathogen_analysis(alias, centre_name, sample_accession, run_accession, study_accession,
                                              pipeline_name, analysis_date, analysis_files, title, description,
                                              analysis_xml)
    analysis_obj.build_analysis()


def create_submission_xml(conn, analysis, analysis_xml, submission_xml, action):
    alias = "sub_" + analysis.process_id.lower() + "-" + str(analysis.selection_id)
    centre_name = 'COMPARE'
    schema = 'analysis'
    submission_obj = submission(alias, centre_name, action, submission_xml, analysis_xml, schema)
    submission_obj.build_submission()


def get_account_pass(conn, user):
    query = "select password from account where account_id='{}'".format(user)
    cursor = conn.cursor()
    cursor.execute(query)
    for password in cursor:
        p = password[0]
    return base64.b64decode(p[::-1]).decode()


def uploadFileToEna(filename, user, passw):
    print("uploaing {} ".format(filename))
    command = "curl -T {}  ftp://webin.ebi.ac.uk --user {}:{}".format(filename, user, passw)
    sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = sp.communicate()
    if out:
        print("standard output of subprocess:")
        print(out)
    if err:
        print("standard error of subprocess:")
        print(err)
    if sp.returncode != 0:
        error_list.append(err)
        print(err, file=sys.stderr)
    print("returncode of subprocess:", sp.returncode)
    return err


def submitAnalysis(submission_xml, analysis_xml, user, passw):
    print("Analysis submission started:")
    # command="curl -k  -F \"SUBMISSION=@%s\" -F \"ANALYSIS=@%s\" \"https://www-test.ebi.ac.uk/ena/submit/drop-box/submit/?auth=ENA"%(submission_xml,analysis_xml)+'%20'+user+'%20'+passw+'\"'
    command = "curl -k  -F \"SUBMISSION=@{}\" -F \"ANALYSIS=@{}\" \"https://www.ebi.ac.uk/ena/submit/drop-box/submit/?auth=ENA".format(
        submission_xml, analysis_xml) + '%20' + user + '%20' + passw + '\"'
    print("COMMAND:", command)
    sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = sp.communicate()
    print("SYSOUT:", out)
    print("SYSERR:", err)
    submission_error_messages = list()
    if out:
        root = etree.XML(out)
        root = etree.fromstring(out)
        for messages in root.findall('MESSAGES'):
            for mess in messages.findall('ERROR'):
                submission_error_messages.append('ERROR:' + mess.text)

    print(out)
    print(err)
    print("returncode of subprocess:", sp.returncode)
    return submission_error_messages, sp.returncode, out, err


def post_submission(submission_error_messages, returncode, out, err):
    submission_error = ""
    curl_error = ""
    if len(submission_error_messages) != 0:
        submission_error = '\n'.join(submission_error_messages) + "\n"
    if returncode != 0:
        curl_error = err
    error = submission_error + curl_error
    print(error, file=sys.stderr)
    return error


def terminate(conn, analysis_reporter_stage):
    print("Termination:")
    if len(error_list) != 0:
        final_errors = ' '.join(str(v).replace("'", "") for v in submission_error_messages)
        analysis_reporter_stage.set_error(conn, final_errors.replace("'", ""))
    else:
        analysis_reporter_stage.set_finished(conn)


if __name__ == '__main__':
    get_args()
    prop = properties(properties_file)
    # prop=properties('../resources/properties.txt')
    conn = get_connection(prop.dbuser, prop.dbpassword, prop.dbhost, prop.dbname)
    analysis_reporter_list = get_list(conn)
    error_list = list()
    for analysis_reporter_stage in analysis_reporter_list:
        if analysis_reporter_stage.check_started(conn) == False:
            print("\nTo be started job: process_id:", analysis_reporter_stage.process_id, 'collection id:',
                  analysis_reporter_stage.selection_id, 'stage name:', analysis_reporter_stage.stage_list)
            analysis_reporter_stage.set_started(conn)
            attributes = default_attributes.get_all_attributes(conn, analysis_reporter_stage.process_id)
            analyst_webin = attributes['analyst_webin']
            passw = get_account_pass(conn, analyst_webin)
            gzip_analysis_file = attributes['gzip_analysis_file']
            tab_analysis_file = attributes['tab_analysis_file']
            uploadFileToEna(gzip_analysis_file, analyst_webin, passw)
            uploadFileToEna(tab_analysis_file, analyst_webin, passw)
            analysis_xml = prop.workdir + analysis_reporter_stage.process_id + '/analysis.xml'
            submission_xml = prop.workdir + analysis_reporter_stage.process_id + '/submission.xml'
            create_analysis_xml(conn, analysis_reporter_stage, prop, attributes, analysis_xml)
            action = 'ADD'
            analysis_xml_name = os.path.basename(analysis_xml)
            create_submission_xml(conn, analysis_reporter_stage, analysis_xml_name, submission_xml, action)
            submission_error_messages, returncode, out, err = submitAnalysis(submission_xml, analysis_xml,
                                                                             analyst_webin, passw)
            post_submission_error = post_submission(submission_error_messages, returncode, out, err)
            if post_submission_error != '':
                error_list.append(post_submission_error)
            terminate(conn, analysis_reporter_stage)
            error_list = list()
