#!/usr/bin/env python3
import sys
import time
import subprocess
import base64
import os
import re
import ftplib
from selectadb import properties
from sra_objects import analysis_pathogen_analysis
from sra_objects import analysis_file
from sra_objects import submission
from PipelineAttributes import stages
from PipelineAttributes import default_attributes
from lxml import etree
import argparse
import datetime
from joblib import Parallel, delayed
import multiprocessing
from reporting import Process_report
import psycopg2

__author__ = 'Nima Pakseresht, Blaise Alako'

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
    print('-'*100)
    print(query)
    print('-'*100)
    cursor = conn.cursor()
    cursor.execute(query)
    #cursor.close()
    analysis_reporter_list = list()
    for (process_id, selection_id) in cursor:
        stage = stages(process_id, selection_id, analysis_reporter_stage)
        analysis_reporter_list.append(stage)
    return analysis_reporter_list


def get_connection(db_user, db_password, db_host, db_database, db_port):
    conn = psycopg2.connect(host=db_host, database=db_database, user=db_user, password=db_password,  port=db_port)
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

    tab_analysis_file2 = attributes['tab_analysis_file2']
    tab_analysis_file3 = attributes['tab_analysis_file3']
    tab_analysis_file4 = attributes['tab_analysis_file4']

    if (os.path.isfile(tab_analysis_file2)):
        tab_analysis_file2_md5 = attributes['tab_analysis_file2_md5']
    if (os.path.isfile(tab_analysis_file3)):
        tab_analysis_file3_md5 = attributes['tab_analysis_file3_md5']
    if (os.path.isfile(tab_analysis_file4)):
        tab_analysis_file4_md5 = attributes['tab_analysis_file4_md5']

    pipeline_version = None
    pipeline_name = attributes['pipeline_name']
    if pipeline_name.lower() =='dtu_cge':
        pipeline_version = prop.dtu_cge_version
    elif pipeline_name.lower() =='emc_slim':
        pipeline_version = prop.emc_slim_version
    elif pipeline_name.lower() =='uantwerp_bacpipe':
        pipeline_version = prop.uantwerp_bacpipe_version
    elif pipeline_name.lower() =='rivm_jovian':
        pipeline_version = prop.rivm_jovian_version

    selecta_version = prop.selecta_version
    study_accession = attributes['study_accession']
    scientific_name = attributes['scientific_name']
    sample_accession = attributes['sample_accession']

    print(run_accession, gzip_analysis_file, gzip_analysis_file_md5, tab_analysis_file, tab_analysis_file_md5)
    analysis_files = list()
    file1 = analysis_file(os.path.basename(tab_analysis_file), 'tab', tab_analysis_file_md5)
    analysis_files.append(file1)
    file2 = analysis_file(os.path.basename(gzip_analysis_file), 'other', gzip_analysis_file_md5)
    analysis_files.append(file2)
    if (os.path.isfile(tab_analysis_file2)):
        file3= analysis_file(os.path.basename(tab_analysis_file2), 'tab', tab_analysis_file2_md5)
        analysis_files.append(file3)
    if (os.path.isfile(tab_analysis_file3)):
        file4 = analysis_file(os.path.basename(tab_analysis_file3), 'tab', tab_analysis_file3_md5)
        analysis_files.append(file4)
    if (os.path.isfile(tab_analysis_file4)):
        file5= analysis_file(os.path.basename(tab_analysis_file4), 'tab', tab_analysis_file4_md5)
        analysis_files.append(file5)


    print('*'*100)
    print("Analysis files:\n {} ".format(analysis_files))
    print('*'*100)
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
                                              pipeline_name, pipeline_version, selecta_version,  analysis_date, analysis_files, title, description,
                                              analysis_xml)
    print('*'*100)
    print(description)
    print('*'*100)
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
    trialcount=0
    print("uploading {} ".format(filename))
    command = "curl -T {}  ftp://webin.ebi.ac.uk --user {}:{}".format(filename, user, passw)
    md5downloaded = "curl -s ftp://webin.ebi.ac.uk/{} --user {}:{} | md5sum | cut -f1 -d ' '".format(os.path.basename(filename), user,passw)
    md5uploaded = "md5sum {} | cut -f1 -d ' '".format(filename)
    print('-'*100)
    print("CURL command:\n{}".format(command))
    print("Downlad command:\n{}".format(md5downloaded))
    print("MD5 uploaded:\n{}".format(md5uploaded))
    print('-'*100)
    uploadmd5,uploaderr = subprocess.Popen(md5uploaded, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = sp.communicate()
    downloadmd5,downloaderr = subprocess.Popen(md5downloaded, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    uploadmd5=uploadmd5.decode().strip(' \t\n\r')
    downloadmd5=downloadmd5.decode().strip(' \t\n\r')
    print('*'*100)
    print("{} {} {}".format(os.path.basename(filename),uploadmd5,downloadmd5))
    print(filename)
    print("U:{}\nD:{}".format(uploadmd5,downloadmd5))
    print('*'*100)
    if(uploadmd5 == downloadmd5):
        if out:
            print("standard output of subprocess:")
            print(out)
        if err:
            print("standard error of subprocess:")
            print(err)
        if sp.returncode != 0:
            error_list.append(err.decode())
            print(err.decode(), file=sys.stderr)
        print("returncode of subprocess:", sp.returncode)
        return err.decode()
    else:
        time.sleep(10)
        uploadFileToEna(filename, user, passw)
        trialcount +=1
        if trialcount >10:
            return err.decode()



def submitAnalysis(submission_xml, analysis_xml, user, passw,url):
    print("Analysis submission started:")
    command = "curl -k  -F \"SUBMISSION=@{}\" -F \"ANALYSIS=@{}\" \"{}".format(submission_xml, analysis_xml, url) + '%20' + user + '%20' + passw + '\"'
    print("URL:",url)
    print("COMMAND:", command)
    sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = sp.communicate()
    print("SYSOUT:", out.decode())
    print("SYSERR:", err.decode())
    submission_error_messages = list()
    if out:
        root = etree.XML(out)
        root = etree.fromstring(out)
        for messages in root.findall('MESSAGES'):
            for mess in messages.findall('ERROR'):
                submission_error_messages.append('ERROR:' + mess.text)

   
    print("returncode of subprocess:", sp.returncode)
    return submission_error_messages, sp.returncode, out.decode(), err.decode()


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


def terminate(conn, analysis_reporter_stage, analysis_id, submission_id):
    print("Termination:")
    if len(error_list) != 0:
        final_errors = ' '.join(str(v).replace("'", "") for v in submission_error_messages)
        analysis_reporter_stage.set_error(conn, final_errors.replace("'", ""))
        process_report_set_analysis(conn, analysis_id, analysis_reporter_stage.process_id)
        process_report_set_submission(conn, submission_id, analysis_reporter_stage.process_id)

    else:
        analysis_reporter_stage.set_finished(conn)
        process_report_set_analysis(conn, analysis_id, analysis_reporter_stage.process_id)
        process_report_set_submission(conn, submission_id, analysis_reporter_stage.process_id)


def extract_analysis_id(out):
    if re.findall('ANALYSIS accession="(.+)" alias=', out):
        analysis_id = re.findall('ANALYSIS accession="(.+)" alias=', out)
    else:
        #<ERROR>In object(ERZ529314) the file (ERR2187921_analysis_DTU_CGE_summary.tsv)
        # has already been submitted and is waiting to be processed</ERROR>
        if re.findall('ERZ\d{6,7}', out):
            analysis_id = re.findall('ERZ\d{6,7}', out)
        else:
            analysis_id=['']
    return analysis_id[0]


def process_report_set_analysis(conn, analysis_id, process_id):
    """ info contains, process_report_id and analysis_id """
    query = "Update process_report set analysis_id='{}' where process_id='{}'".format(analysis_id, process_id)
    print(query)
    cursor = conn.cursor()
    try:
        if analysis_id:
            cursor.execute(query)
            conn.commit()
            #cursor.close()
        else:
            pass
    except:
        print("Error: can not set analysis_id to {} where process_id={} in process_report table".format(
            analysis_id, process_id), file=sys.stderr)
        message = str(sys.exc_info()[1])
        print("Exception: {}".format(message), file=sys.stderr)
        conn.rollback()
        #cursor.close()


def extract_submission_id(out):
    if re.findall('SUBMISSION accession="(.+)" alias=', out):
        submission_id = re.findall('SUBMISSION accession="(.+)" alias=', out)
    else:
        #<ERROR>In object(ERZ529314) the file (ERR2187921_analysis_DTU_CGE_summary.tsv)
        # has already been submitted and is waiting to be processed</ERROR>
        if re.findall('ERA\d{6,7}', out):
            submission_id = re.findall('ERA\d{6,7}', out)
        else:
            submission_id = ['']
    return submission_id[0]

def process_report_set_submission(conn, submission_id, process_id):
    """ info contains, process_report_id and analysis_id """
    query = "Update process_report set submission_id='{}' where process_id='{}'".format(submission_id, process_id)
    print(query)
    cursor = conn.cursor()
    try:
        if submission_id:
            cursor.execute(query)
            conn.commit()
            cursor.close()
        else:
            pass
    except:
        print("Error: can not set submssion_id to {} where process_id={} in process_report table".format(
            submission_id, process_id), file=sys.stderr)
        message = str(sys.exc_info()[1])
        print("Exception: {}".format(message), file=sys.stderr)
        conn.rollback()
       #cursor.close()


def prepare_and_submit_analysis(conn, default_attributes, analysis_reporter_stage):
    if analysis_reporter_stage.check_started(conn) == False:
        error_list=list()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        print("\n{}:  To be started job: process_id:".format(timestamp), analysis_reporter_stage.process_id, 'collection id:',
              analysis_reporter_stage.selection_id, 'stage name:', analysis_reporter_stage.stage_list)
        analysis_reporter_stage.set_started(conn)
        attributes = default_attributes.get_all_attributes(conn, analysis_reporter_stage.process_id)
        analyst_webin = attributes['analyst_webin']
        passw = get_account_pass(conn, analyst_webin)
        gzip_analysis_file = attributes['gzip_analysis_file']
        tab_analysis_file = attributes['tab_analysis_file']
        tab_analysis_file2 = attributes['tab_analysis_file2']
        tab_analysis_file3 = attributes['tab_analysis_file3']
        tab_analysis_file4 = attributes['tab_analysis_file4']
        print("ATTRIBUTES: {}".format(attributes))
        print('Should upload \n {} and \n{} in ftp.webin but dry at the moment'.format(gzip_analysis_file, tab_analysis_file))

        uploadFileToEna(gzip_analysis_file, analyst_webin, passw)
        uploadFileToEna(tab_analysis_file, analyst_webin, passw)
        if (os.path.isfile(tab_analysis_file2)):
            uploadFileToEna(tab_analysis_file2, analyst_webin, passw)
        if(os.path.isfile(tab_analysis_file3)):
            uploadFileToEna(tab_analysis_file3, analyst_webin, passw)
        if(os.path.isfile(tab_analysis_file4)):
            uploadFileToEna(tab_analysis_file4, analyst_webin, passw)

        analysis_xml = prop.workdir + analysis_reporter_stage.process_id + '/analysis.xml'
        submission_xml = prop.workdir + analysis_reporter_stage.process_id + '/submission.xml'
        create_analysis_xml(conn, analysis_reporter_stage, prop, attributes, analysis_xml)
        #action = 'ADD'
        analysis_xml_name = os.path.basename(analysis_xml)
        create_submission_xml(conn, analysis_reporter_stage, analysis_xml_name, submission_xml, prop.analysis_submission_action)

        if prop.analysis_submission_mode.lower() =='prod':
            try:
                submission_error_messages, returncode, out, err = submitAnalysis(submission_xml, analysis_xml,
                                                                         analyst_webin, passw,
                                                                             prop.analysis_submission_url_prod)
            except:
                message = str(sys.exc_info()[1])
                print("Exception: {}".format(message), file=sys.stderr)

        else:
            try:
                submission_error_messages, returncode, out, err = submitAnalysis(submission_xml, analysis_xml,
                                                                             analyst_webin, passw,
                                                                             prop.analysis_submission_url_dev)
            except:
                message = str(sys.exc_info()[1])
                print("Exception: {}".format(message), file=sys.stderr)
        print('-'*100)
        print("ERR:{}\nOUT:{}\nRETURNCODE:{}\nSubmission_error_messages:{}\nTYPE_OUTPUT:{}\nANALYSIS_ID:{}\n".format(err, out,
                                                                                                                     returncode,submission_error_messages, type(out), extract_analysis_id(out)))
        print('-'*100)
        post_submission_error = post_submission(submission_error_messages, returncode, out, err)
        if post_submission_error != '':
            #pass
            error_list.append(post_submission_error)
        terminate(conn, analysis_reporter_stage, extract_analysis_id(out), extract_submission_id(out))
        error_list = list()
        return True
    else:
        return False


if __name__ == '__main__':
    #get_args()
    #prop = properties(properties_file)
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
        print('-'*100)
        print('-'*100)
        conn = get_connection(prop.dbuser, prop.dbpassword, prop.dbhost, prop.dbname, prop.dbport)
        print('-'*100)
        print("Pipeline_version:{}".format(prop.uantwerp_bacpipe_version))
        print("analysis_submission_url_dev:", prop.analysis_submission_url_dev)
        print("analysis_submission_url_prod:", prop.analysis_submission_url_prod)
        print("analysis_submission_action:", prop.analysis_submission_action)
        print("analysis_submission_mode:", prop.analysis_submission_mode)
        print("DB_NAME: {}".format(prop.dbname))
        print("DB_HOST: {}".format(prop.dbhost))
        print('-'*100)
        analysis_reporter_list = get_list(conn)
        error_list = list()
        """ multiprocessing.cpu_count() - 2"""
        num_cores = multiprocessing.cpu_count()
        try:
            print('-'*100)
            print("Analysis to uploads: {}".format(len(analysis_reporter_list)))
            print('-'*100)
            for analysis_reporter_stage in analysis_reporter_list:
                print(analysis_reporter_stage.process_id)
                print(analysis_reporter_stage.check_started(conn))
                attributes = default_attributes.get_all_attributes(conn, analysis_reporter_stage.process_id)

                if os.path.isfile(attributes['gzip_analysis_file']) and os.path.isfile(attributes['tab_analysis_file']):
                    outcome = prepare_and_submit_analysis(conn, default_attributes, analysis_reporter_stage)
                    print('-'*100)
                    print("Outcome of submission:")
                    print(outcome)
                    print(analysis_reporter_stage.process_id)
                    print('-'*100)
                else:
                    pass
        except:
            print("EXCEPT BLOCK IN __MAIN__")
            message = str(sys.exc_info()[1])
            print(message)
            print(str(sys.exc_info()))
            pass


