#!/usr/bin/env python3

import MySQLdb
import pymysql
from PipelineAttributes import stages
from selectadb import properties
from PipelineAttributes import default_attributes
from pipelines import dtu_cge
from pipelines import emc_slim
import os
import sys
import hashlib
import argparse
from bsub import bsub
import re
import itertools

global error_list
error_list = ''

sys.stdout.flush()

def get_args():
    global properties_file
    # Assign description to the help doc
    parser = argparse.ArgumentParser(
        description='Script remove the processed submissions to make free space for incoming submissions.')
    parser.add_argument('-p', '--properties_file', type=str,
                        help='Please provide the properties file that is required by SELECTA system', required=True)
    args = parser.parse_args()
    properties_file = args.properties_file


def get_connection(db_user, db_password, db_host, db_database, db_port):
    conn = MySQLdb.connect(user=db_user, passwd=db_password, host=db_host, db=db_database, port=db_port)
    return conn


def get_list(conn):
    data_provider_stage = 'data_provider'
    core_executor_stage = 'core_executor'
    analysis_reporter_stage = 'analysis_reporter'
    process_archival_stage = 'process_archival'
    query = "select process_id,selection_id from process_stages where stage_start is null and stage_end is null and stage_error is \
           null and stage_name='{}' and process_id not in (select distinct(process_id) from process_stages where \
          (stage_start is not null or stage_end is not null) and stage_name in ('{}','{}')) \
           and process_id in (select distinct(process_id) from process_stages where stage_start is not null and stage_end \
            is not null and stage_name='{}')".format(core_executor_stage,
                                                 analysis_reporter_stage,
                                                  process_archival_stage,
                                                    data_provider_stage)
    """ Original query (stage_error is null for dataprovider: for some reason this column is always fill up when under LSF )
    query = "select process_id,selection_id from process_stages where stage_start is null and stage_end is null and stage_error is \
               null and stage_name='{}' and process_id not in (select distinct(process_id) from process_stages where \
              (stage_start is not null or stage_end is not null) and stage_name in ('{}','{}')) \
               and process_id in (select distinct(process_id) from process_stages where stage_start is not null and stage_end \
                is not null and stage_error is null and stage_name='{}')".format(core_executor_stage,
                                                                                 analysis_reporter_stage,
                                                                                 process_archival_stage,
                                                                            data_provider_stage) """

    print('-' * 100)
    print(query)
    print('-' * 100)
    cursor = conn.cursor()
    cursor.execute(query)
    core_executor_list = list()
    for (process_id, selection_id) in cursor:
        stage = stages(process_id, selection_id, core_executor_stage)
        core_executor_list.append(stage)
    return core_executor_list


def execute(conn, process_id, selection_id, prop):
    pipeline_name = default_attributes.get_attribute_value(conn, 'pipeline_name', process_id)
    print(pipeline_name, process_id)
    if pipeline_name.upper() == 'DTU_CGE':
        execute_dtu_cge(process_id, selection_id, prop)
    elif pipeline_name.upper() == 'EMC_SLIM':
        jobidsorerror = execute_emc_slim(process_id, selection_id, prop)
    return(jobidsorerror)


def update_process_attributes(conn, process_id, attribute_key, attribute_value):
    if process_id != "" and attribute_value != "":
        # query="INSERT INTO process_attributes (process_id,attribute_key,attribute_value) values('%s','%s','%s')"%(process_id,attribute_key,attribute_value)
        query = "update process_attributes set attribute_value='{}' where process_id='{}' and attribute_key='{}'".format(
            attribute_value, process_id, attribute_key)
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            conn.commit()
        except:
            print("Cannot insert:")
            message = str(sys.exc_info()[1])
            error_list.append(message)
            print("Exception: {}".format(message))
            conn.rollback()


def execute_dtu_cge(process_id, selection_id, prop):
    fq1 = os.path.basename(default_attributes.get_attribute_value(conn, 'fastq1', process_id))
    fq2 = os.path.basename(default_attributes.get_attribute_value(conn, 'fastq2', process_id))
    pair = default_attributes.get_attribute_value(conn, 'pair', process_id)
    run_accession = default_attributes.get_attribute_value(conn, 'run_accession', process_id)
    database_dir = prop.dtu_cge_databases
    workdir = prop.workdir + process_id + "/"
    print("Test:" + workdir)
    sequencing_machine = 'Illumina'

    cge = dtu_cge(fq1, fq2, database_dir, workdir, sequencing_machine, pair, run_accession)
    print(cge.fq1, cge.fq2, cge.database_dir, cge.workdir, cge.sequencing_machine, cge.pair)
    gzip_file, tab_file, error_message = cge.execute()
    if error_message != '':
        error_list.append(error_message)
    gzip_file_md5 = hashlib.md5(open(gzip_file, 'rb').read()).hexdigest()
    tab_file_md5 = hashlib.md5(open(tab_file, 'rb').read()).hexdigest()
    update_process_attributes(conn, process_id, 'gzip_analysis_file', gzip_file)
    update_process_attributes(conn, process_id, 'tab_analysis_file', tab_file)
    update_process_attributes(conn, process_id, 'gzip_analysis_file_md5', gzip_file_md5)
    update_process_attributes(conn, process_id, 'tab_analysis_file_md5', tab_file_md5)
    return error_list


def execute_emc_slim(process_id, selection_id, prop):
    fq1 = os.path.basename(default_attributes.get_attribute_value(conn, 'fastq1', process_id))
    fq2 = os.path.basename(default_attributes.get_attribute_value(conn, 'fastq2', process_id))
    pair = default_attributes.get_attribute_value(conn, 'pair', process_id)
    run_accession = default_attributes.get_attribute_value(conn, 'run_accession', process_id)
    # TODO:  not sure needed by SLIM
    workdir = prop.workdir + process_id + "/"
    print("Test:" + workdir)
    # TODO: sequencing_machine shall be available in the parameters
    """ Sequencing machine should be named in the properties files."""
    sequencing_machine = prop.seq_machine

    slim = emc_slim(fq1, fq2, prop.emc_slim_property_file, workdir, sequencing_machine, pair, run_accession,
                    prop.emc_slim_program, prop)
    print(slim.fq1, slim.fq2, slim.emc_slim_property_file, slim.workdir, slim.sequencing_machine, slim.pair,
          slim.run_accession, slim.emc_slim_program, prop.lsf, prop.rmem, prop.lmem)

    gzip_file, tab_file, error_message , jobids = slim.execute(prop)

    if not prop.lsf:
        if error_message != '':
            error_list.append(error_message)
        else:
            gzip_file_md5 = hashlib.md5(open(gzip_file, 'rb').read()).hexdigest()
            tab_file_md5 = hashlib.md5(open(tab_file, 'rb').read()).hexdigest()
            update_process_attributes(conn, process_id, 'gzip_analysis_file', gzip_file)
            update_process_attributes(conn, process_id, 'tab_analysis_file', tab_file)
            update_process_attributes(conn, process_id, 'gzip_analysis_file_md5', gzip_file_md5)
            update_process_attributes(conn, process_id, 'tab_analysis_file_md5', tab_file_md5)
        return error_list
    else:
        """ We have LSF option here, what action to take?"""
        print(jobids)
        return jobids

date_time_match_string = '(at|on)\s+[a-zA-Z]+\s+([a-zA-Z]+)\s+([0-9]+)\s+([0-9]{2}):([0-9]{2}):([0-9]{2})\s+([0-9]{4})$'


regexes = {
    'exec_host': re.compile('^Job was executed on host\(s\) <(.*)>, in queue <.*>, as user <.*> in cluster <.*>.$'),
    'working_dir': re.compile('^<(.*)> was used as the working directory.$'),
    'exit_code': re.compile('(^Successfully completed\.$)|(?:^Exited with exit code ([0-9]+)\.$)'),
    'cpu_time': re.compile('^\s+CPU time\s+:\s+([0-9]+\.[0-9]+) sec.$'),
    'max_memory': re.compile('^\s+Max Memory\s+:\s+([0-9]+) MB$'),
    'requested_memory': re.compile('^\s+Total Requested Memory\s+:\s+([0-9]+\.[0-9]+) MB'),
    'max_processes': re.compile('^\s+Max Processes\s+:\s+([0-9]+)$'),
    'max_threads': re.compile('^\s+Max Threads\s+:\s+([0-9]+)$'),
    'start_time': re.compile('^Started ' + date_time_match_string),
    'end_time': re.compile('^Results reported ' + date_time_match_string),
    'stderr': re.compile('stderr')
}


def readoutfile(file, jobid):
    if not os.path.isfile(file):
        bsub.poll(jobid)
    else:
        with open(file) as f:
            lines = f.readlines()
            exitcode= None
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

def runcomplete (file):
    with open(file) as f:
        lines = f.readlines()
        found = False
        for line in lines:
            hit = regexes['stderr'].search(line)
            if hit is None:
                pass
            else:
                found=True
        return found



if __name__ == '__main__':
    error_list = list()
    get_args()
    prop = properties(properties_file)
    lsf = prop.lsf
    # prop=properties('../resources/properties.txt')
    conn = get_connection(prop.dbuser, prop.dbpassword, prop.dbhost, prop.dbname, prop.dbport)
    core_executor_list = get_list(conn)
    print('.' * 100)
    print(type(core_executor_list))
    print(core_executor_list)
    print('.' * 100)
    max_number_of_core = prop.max_core_job
    index = 0
    process_jobids={}
    jobs_ids = []
    print('.'*100)
    print(len([exe.process_id for exe in core_executor_list]))
    print([(exe.process_id, exe.selection_id) for exe in core_executor_list])
    print('.'*100)
    for exe in core_executor_list:
        print(hash(exe))
        print(exe)
        print(exe.process_id)
        print(exe.selection_id)
        pass
        if index < max_number_of_core:
            if exe.check_started(conn) == False:
                index = index + 1
                exe.set_started(conn)
                if not lsf:
                    print("NO LSF so running locally the execution")
                    execute(conn, exe.process_id, exe.selection_id, prop)
                    if len(error_list) != 0:
                        final_errors = '\n'.join(str(v).replace("'", "") for v in error_list)
                        exe.set_error(conn, final_errors)
                    else:
                        exe.set_finished(conn)
                else:
                    """ LSF execution ...."""
                    print('*'*50)
                    print("Running {} in cluster ".format(exe.process_id))
                    print('*' * 50)

                    print("This should run under LSF .... ")
                    jobids = execute(conn, exe.process_id, exe.selection_id, prop)
                    jobs_ids.append(jobids[0])
                    print('*' * 50)
                    print("Jobids for  {} are {} in cluster ".format(exe.process_id, jobids))
                    print('*' * 50)

                    err = [os.getcwd() + '/core_executor_' + exe.process_id + '.' + y for y in [x + '.err' for x in jobids]]
                    out = [os.getcwd() + '/core_executor_' + exe.process_id + '.' + y for y in [x + '.out' for x in jobids]]
                    #final_errors = '\n'.join(str(v).replace("'", "") for v in list(itertools.chain(err, out)))
                    final_errors = '\n'.join(str(v).replace("'", "") for v in  out)
                    print(final_errors)
                    process_jobids[exe.process_id] = out
            error_list = list()
        else:
            break
    print('.'*100)
    print(process_jobids)
    print(jobs_ids)
    print("All bsub command summited, crawling the .out file for running status for purpose of DB logging")
    print('.' * 100)
    if lsf:
        while len(jobs_ids) > 0:
            for process_id in process_jobids.keys():
                lsf_out = process_jobids[process_id][0]
                print(':'*100)
                print("process_id:{}\nLsf_out:{}\n".format(process_id, lsf_out))
                print(':'*100)
                jobid = lsf_out.split('.')[-2]
                if os.path.isfile(lsf_out) and runcomplete(lsf_out):
                    print('.' * 100)
                    print('LSF_OUT: {}'.format(lsf_out))
                    print('.' * 100)
                    localexitcode = readoutfile(lsf_out, jobid)
                    if localexitcode != 0:
                        error = ''
                        with open(lsf_out) as f:
                            error = f.read()
                            print(error)
                        final_errors = lsf_out + ' with exit code ' + str(localexitcode) #+ '\n' + error
                        exe.set_error(conn, final_errors)
                    else:
                        print('.' * 100)
                        print('exit code is not 0: --> {}'.format(localexitcode))
                        print('.' * 100)
                        exe.set_finished(conn)
                    try:
                        print('*' * 100)
                        print("Romoving process id:{} from the core_executor_list".format(exe.process_id))
                        print(len(core_executor_list))
                        print('*' * 100)
                        jobs_ids.remove(jobid)
                    except ValueError:
                        pass

                else:
                    print('*' * 100)
                    print("Awaiting jobid:{} to complete".format(jobid))
                    bsub.poll(jobid)
                    print("LSF_OUT: {} does not exit or is empty".format(lsf_out))
                    print('*' * 100)
                    # pass