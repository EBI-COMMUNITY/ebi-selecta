#!/usr/bin/env python3

import pymysql as MySQLdb
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
import subprocess as sp
import time
from joblib import Parallel, delayed
import multiprocessing
import datetime
import itertools
import random
from collections import deque



__author__ = 'Nima Pakseresht, Blaise Alako'


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
    """ Some core_executor takes over 48 hour to complete hence increase of mysql connect_time out variable, set time out to 5 days """
    conn = MySQLdb.connect(user=db_user, passwd=db_password, host=db_host, db=db_database, port=db_port, connect_timeout=432000)
    return conn


def get_list(conn):
    data_provider_stage = 'data_provider'
    core_executor_stage = 'core_executor'
    analysis_reporter_stage = 'analysis_reporter'
    process_archival_stage = 'process_archival'
    """ Currently pulling in chunck of 300 for the purpose of cronjobs runs"""
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
    sequencing_platform = default_attributes.get_attribute_value(conn, 'instrument_platform', process_id)
    print(pipeline_name, process_id)
    if pipeline_name.upper() == 'DTU_CGE':
        jobids, pipeline_content = execute_dtu_cge(process_id, selection_id, prop)
    elif pipeline_name.upper() == 'EMC_SLIM':
        jobids, pipeline_content = execute_emc_slim(process_id, selection_id, prop)
    return  jobids, pipeline_content


def update_process_attributes(conn, process_id, attribute_key, attribute_value):
    print('process_id:{}\nattribute_key:{}\nattribute_value:{}'.format(process_id, attribute_key, attribute_value))
    if process_id != "" and attribute_value != "":
        # query="INSERT INTO process_attributes (process_id,attribute_key,attribute_value) values('%s','%s','%s')"%(process_id,attribute_key,attribute_value)
        query = "update process_attributes set attribute_value='{}' where process_id='{}' and attribute_key='{}'".format(
            attribute_value, process_id, attribute_key)
        print("*"*100)
        print("PROCESS_ATRIBUTE UPDATE:\n{}".format(query))
        print("*"*100)

        cursor = conn.cursor()
        try:
            cursor.execute(query)
            conn.commit()
            cursor.close()

        except:
            print("Cannot insert:")
            message = str(sys.exc_info()[1])
            error_list.append(message)
            print("Exception: {}".format(message))
            conn.rollback()
            cursor.close()



def process_attributes_update(gzip_file, tab_file, process_id, conn, error_message):
    if error_message !='':
        print("Found error:\n{}".format(error_message))
        error_list.append(error_message)
    else:
        gzip_file_md5 = hashlib.md5(open(gzip_file, 'rb').read()).hexdigest()
        tab_file_md5 = hashlib.md5(open(tab_file, 'rb').read()).hexdigest()
        update_process_attributes(conn, process_id, 'gzip_analysis_file', gzip_file)
        update_process_attributes(conn, process_id, 'tab_analysis_file', tab_file)
        update_process_attributes(conn, process_id, 'gzip_analysis_file_md5', gzip_file_md5)
        update_process_attributes(conn, process_id, 'tab_analysis_file_md5', tab_file_md5)
    return error_list


def get_sequencing_machine(instrument_platform):
    if re.findall('(?i)illumina', instrument_platform):
        return "Illumina"
    if re.findall('(?i)454',instrument_platform):
        return "LS454"
    if re.findall('(?i)SOlid',instrument_platform):
        return "ABI SOLiD"
    if re.findall('(?i)Torrent',instrument_platform):
        return "Ion Torrent"



def execute_dtu_cge(process_id, selection_id, prop):
    fq1 = os.path.basename(default_attributes.get_attribute_value(conn, 'fastq1', process_id))
    fq2 = os.path.basename(default_attributes.get_attribute_value(conn, 'fastq2', process_id))
    pair = default_attributes.get_attribute_value(conn, 'pair', process_id)
    sequencing_platform = default_attributes.get_attribute_value(conn, 'instrument_platform', process_id)
    run_accession = default_attributes.get_attribute_value(conn, 'run_accession', process_id)
    sample_accession = default_attributes.get_attribute_value(conn, 'sample_accession',  process_id)
    database_dir = prop.dtu_cge_databases
    workdir = prop.workdir + process_id + "/"
    print("Test:" + workdir)
    sequencing_machine = get_sequencing_machine(sequencing_platform)

    cge = dtu_cge(fq1, fq2, database_dir, workdir, sequencing_machine, pair, run_accession, prop, sequencing_platform, sample_accession)
    print(cge.fq1, cge.fq2, cge.database_dir, cge.workdir, cge.sequencing_machine, cge.pair, cge.sample_accession)
    #gzip_file, tab_file, error_message , jobids = cge.execute()
    jobids = cge.execute()
    return jobids, cge



def execute_emc_slim(process_id, selection_id, prop):
    fq1 = os.path.basename(default_attributes.get_attribute_value(conn, 'fastq1', process_id))
    fq2 = os.path.basename(default_attributes.get_attribute_value(conn, 'fastq2', process_id))
    pair = default_attributes.get_attribute_value(conn, 'pair', process_id)
    sequencing_platform = default_attributes.get_attribute_value(conn, 'instrument_platform', process_id)
    run_accession = default_attributes.get_attribute_value(conn, 'run_accession', process_id)
    sample_accession = default_attributes.get_attribute_value(conn, 'sample_accession', process_id)
    # TODO:  not sure needed by SLIM
    workdir = prop.workdir + process_id + "/"
    print("Test:" + workdir)
    # TODO: sequencing_machine shall be available in the parameters
    """ Sequencing machine should be named in the metadata file."""
    sequencing_machine = get_sequencing_machine(sequencing_platform)

    slim = emc_slim(fq1, fq2, prop.emc_slim_property_file, workdir, sequencing_machine, pair, run_accession,
                    prop.emc_slim_program, prop, sequencing_platform, sample_accession)
    print(slim.fq1, slim.fq2, slim.emc_slim_property_file, slim.workdir, slim.sequencing_machine, slim.sample_accession, slim.pair,
          slim.run_accession, slim.emc_slim_program, prop.lsf, prop.rmem, prop.lmem)

    jobids = slim.execute()
    return jobids, slim


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


def post_process_lsf_runs(jobid_exe, jobid_pipeline_obj):
    print("All jobs completed")
    subjobids = jobid_exe.keys()
    for jid in subjobids:
        lsf_out = jobid_exe[jid][1][0]
        pipeline_obj = jobid_pipeline_obj[jid]
        newexec = jobid_exe[jid][0]
        process_id = lsf_out.split('_')[-1].split('.')[0]
        if os.path.isfile(lsf_out) and runcomplete(lsf_out):
            print('.' * 100)
            print('Consulting lsf_out: {}'.format(lsf_out))
            print('.' * 100)
            localexitcode = readoutfile(lsf_out, jid)
            if localexitcode != 0:
                error = ''
                with open(lsf_out) as f:
                    error = f.read()
                    print(error)
                final_errors = lsf_out + ' with exit code ' + str(localexitcode) + '\n' + error
                try:
                    newexec.set_error(conn, final_errors)
                except ValueError:
                    pass
            else:

                try:
                    print('-' * 100)
                    print('exit code is not 0: --> {}'.format(localexitcode))
                    print('-' * 100)
                    """Post processing: Bundling the directories in an  archive directory and compressing them"""
                    gzip_file, tab_file = pipeline_obj.post_process()
                    print('-' * 100)
                    print("ERROR list: {}".format(pipeline_obj.error_list))
                    print('-' * 100)
                    error_message = '\n'.join(str(v).strip().replace("'", "").replace("b\'\'", "") for v in pipeline_obj.error_list)
                    print("=" * 100)
                    print("{} PROCESS_ATTRIBUTE_UPDATE".format(process_id))
                    print("GZIP_FILE:{}\nTAB_FILE:{}".format(gzip_file, tab_file))
                    print("Process_id:{}\nError messages: {}".format(process_id, error_message))
                    print(type(error_message))
                    print("=" * 100)
                    process_attributes_update(gzip_file, tab_file, process_id, conn, error_message)
                    newexec.set_finished(conn)
                except ValueError:
                    newexec.set_error(conn, error_message)
        else:
            try:
                final_errors = lsf_out + ' with exit code ' + str(localexitcode)
                newexec.set_error(conn, final_errors)
            except:
                pass




def post_process_lsf(jobid_exe, jobid_pipeline_obj, jobid):
    lsf_out = jobid_exe[jobid][1][0]
    pipeline_obj = jobid_pipeline_obj[jobid]
    newexec = jobid_exe[jobid][0]
    process_id = lsf_out.split('_')[-1].split('.')[0]
    #bsub.poll(jid)
    if os.path.isfile(lsf_out):
        print('.' * 100)
        print('Consulting lsf_out: {}'.format(lsf_out))
        print('.' * 100)
        localexitcode = readoutfile(lsf_out, jobid)
        if localexitcode != 0:
            error = ''
            with open(lsf_out) as f:
                error=f.read()
            final_errors = lsf_out + ' with exit code ' + str(localexitcode) + '\n' + error
            newexec.set_error(conn, final_errors)
        else:
            print('.' * 100)
            print('exit code is not 0: --> {}'.format(localexitcode))
            print('.' * 100)
            """Post processing: Bundling the directories in an  archive directory and compressing them"""
            try:
                gzip_file, tab_file = pipeline_obj.post_process()
                print('.' * 100)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                print("{}: GZIP_FILE:{}\nTAB_FILE:{}".format(timestamp, gzip_file, tab_file))
                print('.' * 100)
                error_message = '\n'.join(str(v).replace("'", "") for v in pipeline_obj.error_list)
                process_attributes_update(gzip_file, tab_file, process_id, conn, error_message)
                newexec.set_finished(conn)
            except (MySQLdb.Error, MySQLdb.Warning) as e:
                try:
                    newexec.set_error(conn, e)
                except IndexError:
                    print("MySQL Error: {}".format(str(e)))
            return True

    else:
        try:
            final_errors = lsf_out
            newexec.set_error(conn, final_errors)
        except MySQLdb.Error as e:
            try:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                print("{}: MySQL Error: {} : {}".format(timestamp, e.args[0], e.args[1]))
            except IndexError:
                print("{}: MySQL Error: {}".format(timestamp, str(e)))
        return False

def get_process_id (jobid_exe, jobid):
    return jobid_exe[jobid][1][0].split('_')[-1].split('.')[0]


if __name__ == '__main__':
    error_list = list()
    get_args()
    prop = properties(properties_file)
    lsf = prop.lsf
    # prop=properties('../resources/properties.txt')
    conn = get_connection(prop.dbuser, prop.dbpassword, prop.dbhost, prop.dbname, prop.dbport)
    core_executor_list = get_list(conn)
    #print('.' * 100)
    #print(type(core_executor_list))
    #print(core_executor_list)
    #print('.' * 100)
    max_number_of_core = prop.max_core_job
    index = 0
    process_jobids={}
    jobid_pipeline_obj={}
    jobid_exe ={}
    jobs_ids = []
    #print('.'*100)
    #print(len([exe.process_id for exe in core_executor_list]))
    #print([(exe.process_id, exe.selection_id) for exe in core_executor_list])
    #print('.'*100)
    for exe in core_executor_list:
        #print(hash(exe))
        #print(exe)
        #print(exe.process_id)
        #print(exe.selection_id)
        #pass
        #if index < max_number_of_core:
        if exe.check_started(conn) == False:
            index = index + 1
            exe.set_started(conn)
            if not lsf:
                print("NO LSF so running locally the execution")
                jobids,pipeline_content = execute(conn, exe.process_id, exe.selection_id, prop)
                gzip_file, tab_file,pjobid = pipeline_content.post_process()
                error_message = '\n'.join(str(v).replace("'", "") for v in pipeline_content.error_list)
                process_attributes_update(gzip_file, tab_file,exe.process_id, conn, error_message)

                print('_'*100)
                print("JOBID: {}\nCONTENT_OBJECT:{}\n".format(jobids, pipeline_content))
                print('_'*100)
                if len(error_list) != 0:
                    final_errors = '\n'.join(str(v).replace("'", "") for v in error_list)
                    exe.set_error(conn, final_errors)
                else:
                    exe.set_finished(conn)
            else:
                """ LSF execution ...."""
                jobids , pipeline_content = execute(conn, exe.process_id, exe.selection_id, prop)
                jobs_ids.append(jobids[0])
                print('_' * 50)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                print("{}: Running {} in YODA-cluster with job id: {} added to a pool of {} jobids:\n{} ".format(timestamp , exe.process_id, jobids, len(jobs_ids), jobs_ids))
                print('_' * 50)
                err = [os.getcwd() + '/core_executor_' + exe.process_id + '.' + y for y in [x + '.err' for x in jobids]]
                out = [os.getcwd() + '/core_executor_' + exe.process_id + '.' + y for y in [x + '.out' for x in jobids]]
                #final_errors = '\n'.join(str(v).replace("'", "") for v in list(itertools.chain(err, out)))
                final_errors = '\n'.join(str(v).replace("'", "") for v in err)
                print(final_errors)
                process_jobids[exe.process_id] = out
                print('.'*100)
                print("JOB ids: {} is of type {}".format(jobids, type(jobids)))
                print("process jobids dict: {}".format(process_jobids))
                print("PIPELINE OBJECT: {}".format(pipeline_content))
                print('.'*100)
                jobid_pipeline_obj[jobids[0]]= pipeline_content
                jobid_exe[jobids[0]] = exe, out
                print("PIPELINE OBJECT DICT: {}".format(jobid_pipeline_obj))
        error_list = list()

    if lsf:
        print('.'*100)
        print("All bsub command summited, crawling the .out file for running status for purpose of DB logging")
        print('.' * 100)
        subjobids = list(jobid_exe.keys())

        """
        subjobids.sort()
        subjobids.reverse()
        print('-'*100)
        print("Awaiting following LSF jobs to complete:\n{}".format(subjobids))
        print('-'*100)
        while(len(subjobids)>0):
            jobid = subjobids.pop()
            print('_'*100)
            print("Waiting for lsf job id:{} to complete".format(jobid))
            bsub.poll(jobid)
            post_process_lsf(jobid_exe, jobid_pipeline_obj, jobid)
            print("Post processed job id:{} Done ....\nRemaining jobid list to be processed:\n{}".format(jobid, subjobids))
            print('_'*100)
        """

        submitted_jobs = frozenset(subjobids)
        sleep_time = 1
        num_cores = multiprocessing.cpu_count()

        while len(submitted_jobs) > 0:
            time.sleep(sleep_time)
            if sleep_time < 100:
                sleep_time += 0.25
            try:
                queue_jobs = [x.split()[0] for x in sp.check_output(["bjobs"], shell=True).rstrip().decode().split("\n")[1:]]
                done_jobs = submitted_jobs.difference(queue_jobs)
            except Exception:
                print("No done jobs found..... and following error encounter:\n {}".format(str(sys.exc_info()[1])))
            if len(done_jobs) > 0:
                print('*' * 100)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                print("{} : {} jobs completed post-processing them".format(timestamp, len(done_jobs)))
                """ Take advantage of multiple core to speed up postprocessing ..., batch_size=10"""
                try:
                    results = Parallel(n_jobs=num_cores, verbose=100, max_nbytes=None, batch_size=25)(delayed(post_process_lsf)(jobid_exe, jobid_pipeline_obj, jid) for jid in done_jobs)

                except Exception:
                    process_ids = Parallel(n_jobs=num_cores, verbose=100, max_nbytes=None, batch_size=25)(delayed(get_process_id)(jobid_exe, jid) for jid in done_jobs)
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    print("{}: Post processing failed for {} with following error {}".format(timestamp, process_ids, str(sys.exc_info()[1])))
                print("{} out of {} job ids Completed...".format(len(done_jobs), len(submitted_jobs)))
                print("Parallel post-processing was {}".format(results))
                submitted_jobs = {x for x in submitted_jobs if x not in done_jobs}
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                print("{}: Remaining {} job ids".format(timestamp, len(submitted_jobs)))
                print('-'*100)
