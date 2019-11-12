#!/usr/bin/env python3
"""
Data_provider script: Given list of not started process_id in
SELECTADB_PRODUCTION.process_stages fetch corresponding fastqs
from the Pathogen portal
"""
import re
import os
import base64
import sys
import argparse
import subprocess
import pymysql as MySQLdb
from selectadb import properties
from PipelineAttributes import default_attributes
from PipelineAttributes import stages
import psycopg2

from bsub import bsub

error_list = []


__author__ = 'Nima Pakseresht, Blaise Alako'



def get_args():
    """
    Process property file and return various attribute
    :return: various attribute of runs
    """
    global properties_file
    # Assign description to the help doc
    parser = argparse.ArgumentParser(
        description='Script remove the processed submissions \
         to make free space for incoming submissions.')
    parser.add_argument('-p', '--properties_file', type=str,
                        help='Please provide the properties file \
                        that is required by SELECTA system', required=True)
    parser.add_argument('--db_live',
                        help='Check whether PostGresDB is live and accepting\
    								connection', action='store_true')

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

def get_connection(db_user, db_password, db_host, db_database, db_port):
    """
    Connect to MySQL database
    :param db_user: user name
    :param db_password: passwd
    :param db_host: PostGreSQL host server
    :param db_database: DB name
    :param db_port:  connection port on remote server
    :return: connection handle
    """
    conn = psycopg2.connect(host=db_host, database=db_database, user=db_user, password=db_password,  port=db_port)

    return conn


def get_list(conn):
    """
    Get the list of process_id to process
    :param conn:  mysql connection
    :return: list of process_ids
    """
    stage_name = 'data_provider'
    query = "select process_id,selection_id from process_stages where \
     stage_start is null and stage_end is null and stage_name='{}'".format(stage_name)
    cursor = conn.cursor()
    cursor.execute(query)
    data_provider_list = list()
    for (process_id, selection_id) in cursor:
        stage = stages(process_id, selection_id, stage_name)
        data_provider_list.append(stage)

    return data_provider_list


def get_file_names(conn, process_id):
    """
    Get the fastq file names from process_attributes table
    :param conn:  mysql connection
    :param process_id:
    :return: fastq files
    """
    value = default_attributes.get_attribute_value(conn, 'fastq_files', process_id)
    files = list()
    if ";" in value:
        files = value.split(";")
    else:
        files.append(value)

    return files


def get_datahub_names(conn, process_id):
    """
    Extract the datahub name from SELECTADB_PRODUCTION
    :param conn: PostGreSQL connection
    :param process_id: process_id
    :return: datahub names
    """
    value = default_attributes.get_attribute_value(conn, 'datahub', process_id)
    return value


def create_processing_dir(directory):
    """
    Create a processing directory
    :param directory: directory name
    :return: None
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_datahub_account_password(conn, account_id):
    """
    Fetch datahub credential from SELECTADB_PRODUCTION
    :param conn: PostGreSQL Connection
    :param account_id: datahub account id
    :return: datahub decode password
    """
    query = "select password from account where account_id='{}'".format(account_id)
    cursor = conn.cursor()
    cursor.execute(query)
    for password in cursor:
        passw = password[0]
        print('*' * 100)
        print(base64.b64decode(passw[::-1]).decode())
        print('*' * 100)
    return base64.b64decode(passw[::-1]).decode()


def download_datahub_file(account_name, password, files, outdir, process_id, lsf, dryrun=True):
    """
    Fetch datahub metadata from the Pathogen portal given datahub credentials
    :param account_name: datahub name
    :param password:  datahub password
    :param files: datahub metadata file
    :param outdir: directory where to store the metadata file, define in configuration file
    :param process_id: process_id of the runs
    :param lsf:  Boolean (run through LSF or not)
    :param dryrun: dry run
    :return:  LSF job ids or empty string
    """
    jobids = []
    for file in files:
        outputfile = outdir + '/' + os.path.basename(file)
        print(file)
        """ For some reason the data folder is empty, fastqs are now in vol1 folder :( ftp.dcc-private.ebi.ac.uk/vol1/"""
        url = "ftp://{}:{}@ftp.dcc-private.ebi.ac.uk/vol1/{}".format(account_name, password, file)
        command = "wget -t 2 {} -O {}".format(url, outputfile)
        print('*' * 100)
        print(command)
        print('*' * 100)
        if not dryrun:
            if not lsf:

                sub_process = subprocess.Popen(command,
                                               shell=True,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE)
                out, err = sub_process.communicate()
                if out:
                    print("standard output of subprocess:")
                    print(out)
                if err:
                    print("standard error of subprocess:")
                    print(err)
                if sub_process.returncode != 0:
                    error_list.append(err)
                    print(err, end="", file=sys.stderr)
            else:
                print("LSF value is YES, still need implementation at the moment...")
                print('*' * 100)
                print("Running: ", command)
                print('*' * 100)
                try:
                    job_id = bsub('data_provider_' + process_id,
                                  g='/SELECTA',
                                  verbose=True)(command)
                    jobids.append(job_id)
                except:
                    message = str(sys.exc_info()[1])
                    error_list.append(message)

    return jobids

regexes = {
    'exit_code': re.compile('(^Successfully completed\.$)|(?:^Exited with exit code ([0-9]+)\.$)')
}


def readoutfile(file, jobid):
    """
    parse lsf log (.out, .err) file
    :param file: lsf log file (.out)
    :param jobid: lsf job id
    :return: exitcode of lsf job
    """
    if not os.path.isfile(file):
        bsub.poll(jobid)
    else:
        with open(file) as myfile:
            lines = myfile.readlines()
            exitcode = None
            for line in lines:
                hits = regexes['exit_code'].search(line)
                if hits is None:
                    pass
                elif hits.group(1) is not None:
                    exitcode = 0
                elif hits.group(2) is not None:
                    exitcode = int(hits.group(2))
            print("Final exit code is ", exitcode)
            print(type(exitcode))

    return exitcode



def main():
    """
    Main call to the data_provider scripts.
    :return: None
    """
    #
    options = process_arguments(sys.argv[1:])
    properties_file = options.properties_file
    prop = properties(properties_file)

    error_list = list()
    #get_args()
    #prop = properties(properties_file)
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
        #print(prop)
        conn = get_connection(prop.dbuser, prop.dbpassword, prop.dbhost, prop.dbname, prop.dbport)
        data_provider_list = get_list(conn)
        print(data_provider_list)
        process_jobids = {}
        for data_provider_stage in data_provider_list:
            print(data_provider_stage.process_id,
                  data_provider_stage.selection_id,
                  data_provider_stage.stage_list)
            if not data_provider_stage.check_started(conn):
                print("\nTo be started job: process_id:{}\
                 collection id: {} dataprovider id: {} ".format(data_provider_stage.process_id,
                                                                data_provider_stage.selection_id,
                                                                data_provider_stage.stage_list))
                data_provider_stage.set_started(conn)
                process_dir = prop.workdir + data_provider_stage.process_id
                print("Creating process directory:{}".format(process_dir))
                create_processing_dir(process_dir)
                account_name = get_datahub_names(conn, data_provider_stage.process_id)
                print("account to be processed:{}".format(account_name))
                files = get_file_names(conn, data_provider_stage.process_id)
                print("Files to be downloaded:{}".format(files))
                pass_word = get_datahub_account_password(conn, account_name)
                process_id = data_provider_stage.process_id
                jobids = download_datahub_file(account_name,
                                               pass_word,
                                               files,
                                               process_dir,
                                               process_id,
                                               lsf,
                                               dryrun=False)
                """
                We should be able to capture the .err and .out lsf output into the
                database. Maybe define a a generic lsf_stat class, that will match in
                .out the "Successfully completed" string if true set length of error_list to 0
                other wise logs the full path to the .out file in database
                """
                if not lsf:
                    #if len(error_list) != 0:
                    if len(error_list):
                        final_errors = '\n'.join(str(v).replace("'", "") for v in error_list)
                        data_provider_stage.set_error(conn, final_errors)
                    else:
                        data_provider_stage.set_finished(conn)
                elif lsf:
                    err = [os.getcwd() + '/data_provider_' + process_id + '.' + y for y in [x + '.err' for x in jobids]]
                    out = [os.getcwd() + '/data_provider_' + process_id + '.' + y for y in [x + '.out' for x in jobids]]
                    final_errors = '\n'.join(str(v).replace("'", "") for v in out)
                    print(final_errors)
                    process_jobids[process_id] = out
            error_list = list()
            if lsf:
                print(process_jobids)
        """
        We should check for the content of lsmyfile.out file and store the 
        full path of the error and out file in DB
        """
        if lsf:
            for data_provider_stage in data_provider_list:
                process_id = data_provider_stage.process_id
                for lsf_out in process_jobids[process_id]:
                    print('*'*100)
                    print(lsf_out)
                    print('*'*100)
                    jobid = lsf_out.split('.')[-2]
                    bsub.poll(jobid)
                    if os.path.isfile(lsf_out):
                        print("Processing lsmyfile.out for: jobid {}".format(jobid))
                        print("Processing: {}".format(lsf_out))
                        print('*' * 100)
                        localexitcode = readoutfile(lsf_out, jobid)
                        print(localexitcode)
                        if localexitcode != 0:
                            final_errors = lsf_out + ' with exit code ' + str(localexitcode)
                            data_provider_stage.set_error(conn, final_errors)
                        else:
                            data_provider_stage.set_finished(conn)
                        print('*' * 100)
                    else:
                        print("Awaiting completion of: jobid {}".format(jobid))
                        print("Processing: {}".format(lsf_out))
                        print('*' * 100)
                        #bsub.poll(jobid)
                        if os.path.isfile(lsf_out):
                            localexitcode = readoutfile(lsf_out, jobid)
                            print(localexitcode)
                            if localexitcode != 0:
                                final_errors = lsf_out + ' with exit code ' + str(localexitcode)
                                data_provider_stage.set_error(conn, final_errors)
                            else:
                                data_provider_stage.set_finished(conn)
                        else:
                            bsub.poll(jobid)

        conn.close()


if __name__ == '__main__':
    main()
