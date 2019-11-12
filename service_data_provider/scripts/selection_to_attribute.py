#!/usr/bin/env python3
"""
This scripts initiate the SELECTA workflow.
Given selection in process_selection table with start date null
and selection error null, it populate process_stages , process_attributes
process_report with appropriate runs metadata
"""
import os
import sys
import time
import subprocess
import traceback
import argparse
import base64
import textwrap
from selectadb import selection
from selectadb import properties
from PipelineAttributes import default_attributes
from PipelineAttributes import stages
from reporting import Process_report
import bsub
import psycopg2

error_list = list()
ruler = '*' * 100

__author__ = 'Nima Pakseresht, Blaise Alako'



def get_args():
	"""
	Process property file and return various attribute
	:return: various attribute of runs
	"""
	#global properties_file
	# Assign description to the help doc
	parser = argparse.ArgumentParser(
		description='Populate various table with metadata for each datahub\
		 to be processed from the process_selection table.')
	parser.add_argument('-p', '--properties_file', type=str,
						help='Please provide the properties \
						file that is required by SELECTA system', metavar='',
						required=True)

	args = parser.parse_args()

	print("*" * 100)
	print(args.properties_file)
	print("*" * 100)
	properties_file = args.properties_file
	return properties_file


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
	Connect to PostGreSQL database
	:param db_user: user name
	:param db_password: passwd
	:param db_host: PostGreSQL host server
	:param db_database: DB name
	:param db_port:  connection port on remote server
	:return: connection handle
	"""
	conn = psycopg2.connect(host=db_host, database=db_database, user=db_user, password=db_password,  port=db_port)
	return conn


def get_datahub_accounts(conn):
	"""
	Extract the datahub name from SELECTADB_PRODUCTION
	:param conn: PostGreSQL connection
	:param process_id: process_id
	:return: datahub names
	"""
	account_type = 'datahub'
	query = "select account_id,password from account where account_type='{}'".format(account_type)
	print(ruler, "\nGetting account credentials from account table:\n\t{}".format(query), "\n", ruler, sep="")
	cursor = conn.cursor()
	cursor.execute(query)
	account = dict()
	accounts = list()
	for (account_id, password) in cursor:
		print("Encoded ACCOUNT_ID:{}  PASSWORD:{}".format(account_id, password))
		print("Decoded ACCOUNT_ID:{}  PASSWORD:{}".format(account_id,
														  base64.b64decode(password[::-1]).decode()))
		print('-'*100)
		account['account_id'] = account_id
		account['password'] = base64.b64decode(password[::-1]).decode()
		""" Previously the above read account['password'] = base64.b64decode(password[::-1])
		returning password prepended with key b'' for binary
		base64 has two main functions that acts on byte oriented data
		b64encode and  b64decode  """
		accounts.append(account)
		account = dict()
	return accounts


""" TODO: Updat it to use process instead of sys """
def download_datahub_metadatafile(account, workdir):
	"""
	Fetch datahub metadata from the Pathogen portal given datahub credentials
	:param account: datahub name
	:param workdir:  working directory
	:return:  datahub Metadata file
	"""
	error_list = list()
	datahub = account['account_id']
	password = account['password']
	inputfile = datahub.replace('dcc_', '') + "_run_metadata_*.tsv"
	outputfile = workdir + datahub.replace("dcc_", "") + '_run_metadata.tsv'
	url = "ftp://{}:{}@ftp.dcc-private.ebi.ac.uk/meta/{}/reports/{}".format(datahub,
																			password,
																			datahub,
																			inputfile)
	command = "wget -t 2 {} -O {}".format(url, outputfile)

	if os.path.isfile(outputfile):
		os.remove(outputfile)
	sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = sp.communicate()
	if out:
		print("standard output of subprocess: {} ".format(out), end="", file=sys.stdout)
	if err:
		print("standard error of subprocess: {} ".format(err), end="", file=sys.stderr)
	if sp.returncode != 0:
		error_list.append(err)
		print(err, end="", file=sys.stderr)
		""" print(s, end="", file=depend)  """
	print("returncode of subprocess: {}".format(sp.returncode), file=sys.stdout)
	return outputfile


def fetch_datahub_metadatafile(account, workdir, lsf):
	"""
	Fetch datahub metadata file via pathogen portal
	curl -o output.txt -X GET --header 'Accept: application/json' -u
	dcc_beethoven:xxxx 'https://www.ebi.ac.uk/ena/portal/api/search?
	result=read_run&dataPortal=pathogen&dccDataOnly=true&fields=tax_id,
	scientific_name,sample_accession,secondary_sample_accession,experiment_accession,
	study_accession,secondary_study_accession,run_accession,center_name,fastq_ftp,
	fastq_md5&sortFields=scientific_name,sample_accession&limit=0'
	:param account: datahub account
	:param workdir: working directory
	:param lsf: bo0lean
	:return: Metadata file
	"""
	print("In fetch_datahub_metadatafile")
	error_list = list()
	datahub = account['account_id']
	password = account['password']
	#inputfile = datahub.replace('dcc_', '') + "_run_metadata_*.tsv"
	outputfile = workdir + datahub.replace("dcc_", "") + '_run_metadata.tsv'
	retrieved_fields = (
		"fields=tax_id,scientific_name,sample_accession,secondary_sample_accession,experiment_accession,"
		"study_accession,secondary_study_accession,run_accession,center_name,instrument_platform,fastq_ftp,"
		"fastq_md5&sortFields=scientific_name,sample_accession&limit=0' -k")
	correct_ftp_path = " && perl -p -i -e '~s/ftp\.sra\.ebi\.ac\.uk\/vol1\/|ftp\.dcc\-private\.ebi\.ac\.uk\/vol1\///g' {} ".format(outputfile)

	"""
	Below correct_ftp_path reflect a quick hack to be able to process dcc_bromhead ... 
	Should resume to the above for normal mode of action.....
	correct_ftp_path = " && egrep -v -e 'SAMEA104423915|SAMEA4058395|SAMEA4058397|SAMEA4058405|SAMEA4058441'" \
					   "'SELECTA_REMOVE' \
					   {} >{}.tmp && mv {}.tmp {} && \
						perl -p -i -e '~s/ftp\.sra\.ebi\.ac\.uk\/vol1\///g' {} ".format(outputfile,
																						outputfile,
																						outputfile,
																						outputfile,
																						outputfile)
	"""

	base_command = ("curl -o {} -X GET --header 'Accept:\
	 application/json' -u {}:{} ").format(outputfile,
										  datahub,
										  password)
	base_command = base_command + (" 'https://www.ebi.ac.uk/ena/portal/api/search?")
	base_command = base_command + ("result=read_run&dataPortal=pathogen&dccDataOnly=true&")

	command = base_command + retrieved_fields + correct_ftp_path

	if os.path.isfile(outputfile):
		os.remove(outputfile)
	if not lsf:
		print(ruler)
		print("FETCHMETADATA COMMAND:\n\t", command)
		print("LSF VALUE=", lsf)
		print(ruler)
		sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = sp.communicate()
		if out:
			print(ruler, "\nstandard output of subprocess: {}".format(out), file=sys.stdout)
		if err:
			print(ruler, "\nstandard error of subprocess: {}".format(err), file=sys.stderr)
		if sp.returncode != 0:
			error_list.append(err)
			print(err, end="", file=sys.stderr)
		print(ruler, "\nreturncode of subprocess:{}".format(sp.returncode), file=sys.stdout)
	else:
		print("LSF value is YES, still need implementation at the moment ...")
		print("Working dir: {}".format(workdir))
		print(ruler)
		print("Running: ", command)
		print(ruler)
		try:
			job_id = bsub.bsub("selection_2_attribute", verbose=True)(command)  # , R="rusage[mem=1]")
			bsub.bsub.poll(job_id)
		except:
			message = str(sys.exc_info()[1])
			error_list.append(message)
			print(ruler, "ERROR MESSAGE:\n{}".format(message), "\n", ruler)
	if lsf:
		return [outputfile, job_id]
	else:
		return [outputfile, None]


def get_selection_to_attributes_account(conn):
	"""
	Get_selection_to_attribute_account:
	Get those selection_id from process_selection where start_date is null
	:param conn:
	:return: selection_ids
	"""
	#query = "select distinct datahub from process_selection where public='NO' and selection_to_attribute_start is NULL"
	#query = "select distinct datahub from process_selection where selection_to_attribute_start IS NULL;"
	query = "SELECT DISTINCT datahub from process_selection WHERE selection_to_attribute_start IS NULL and public='NO'"
	""" update process_selection set selection_to_attribute_start=NULL where selection_id in (12,13,14) """
	print(ruler, "\nGetting datahub info from process_selection:\n\t{}".format(query), "\n", ruler, sep="")
	selections = list()
	rows = list()
	cursor = conn.cursor()
	try:
		cursor.execute(query)
		rows = cursor.fetchall()
		print("ROWS:{}".format(rows))
	except:
		print(sys.exc_info())
	for datahub in rows:
		print("Datahub:{}".format(datahub))
		selections.append(datahub[0])
	cursor.close()
	return selections


def get_selection_info_old(conn, datahub):
	"""
	Obselete.....
	:param conn: connection
	:param datahub: datahub
	:return: selection_ids
	"""
	query = ("select selection_id,tax_id,study_accession,run_accession,pipeline_name,analysis_id,public,webin,\
	continuity from process_selection where datahub = '{}' and public = 'NO'\
	 and selection_to_attribute_start is NULL").format(datahub)

	print(ruler, "\nGET_SELECTION_INFO query:\n\t{}".format(query), "\n", ruler, sep="")
	cursor = conn.cursor()
	cursor.execute(query)
	selection_all = list()
	for (selection_id, tax_id, study_accession, run_accession, pipeline_name, analysis_id, public, webin, process_type,
		 continuity) in cursor:
		selectatb = selection(selection_id, datahub, tax_id, study_accession, run_accession, pipeline_name, analysis_id,
							  public, webin, process_type, continuity)
		selection_all.append(selectatb)
	return selection_all


def get_selection_info(conn, datahub):
	"""
	get_selection_info:
	Fetch from process_selection those selection_id without start date and not public
	:param conn: PostGreSQL connection
	:param datahub: Datahub
	:return: all selection ids satisfying the description above
	"""
	query = ("select selection_id,tax_id,study_accession,run_accession,pipeline_name,analysis_id,public,"
			 "selection_to_attribute_end, webin, process_type, continuity from process_selection where \
			 datahub = '{}' and public = 'NO' and selection_to_attribute_start is NULL").format(datahub)

	print(ruler, "\nGET_SELECTION_INFO query:\n\t{}".format(query), "\n", ruler, sep="")
	cursor = conn.cursor()
	cursor.execute(query)
	selection_all = list()
	for (selection_id, tax_id, study_accession, run_accession, pipeline_name, analysis_id, public,
		 selection_to_attribute_end, webin, process_type, continuity) in cursor:
		""" Continuity is NO Exclude selection with selection_to_attribute_end """

		print(ruler, "\nCONTINUITY:\n{}".format(continuity), "\n", ruler, sep="")

		if continuity.lower() == 'no' and selection_to_attribute_end is not None:
			continue
		""" When continuity is YES, we need access to run_id to filter run
		that need to be pushed into Process_stage and Process_report table, this should be handle in the 
		Process_report Class
		"""
		selectatb = selection(selection_id, datahub, tax_id, study_accession, run_accession, pipeline_name, analysis_id,
							  public, selection_to_attribute_end, webin, process_type, continuity)
		selection_all.append(selectatb)
	return selection_all


def log_error(message, message_type, log_file):
	"""
	log_error: log any encounter error into fil
	:param message: Error found
	:param message_type: message type (ERROR, WARNING, INFO)
	:param log_file: log file
	:return: None
	"""

	file = open(log_file, "w")
	if message_type == 'error':
		sys.stderr.write('ERROR: ' + message + '\n')
		file.write('ERROR: ' + message + '\n')
	elif message_type == 'warnning':
		sys.stdout.write('WARNNING: ' + message + '\n')
		file.write('WARNNING: ' + message + '\n')
	elif message_type == 'info':
		sys.stdout.write(message + '\n')
		file.write(message + '\n')
	else:
		print("wrong message type")
	file.close()


def get_default_attributes(tsv_file):
	"""
	get_default_attributes:
	parse datahub metadata file for runs details
	Read the header line of the tsv for purpose of labelling columns
	:param tsv_file: metadata file
	:return: A default_attribute object
	"""
	error_list = list()
	with open(tsv_file) as fname:
		lines = fname.readlines()
	values = lines[0].strip().split("\t")
	print(values)
	header_len = len(values)
	tax_id_index = values.index("tax_id")
	scientific_name_index = values.index("scientific_name")
	sample_accession_index = values.index("sample_accession")
	secondary_sample_acc_index = values.index("secondary_sample_accession")
	experiment_accession_index = values.index("experiment_accession")
	study_accession_index = values.index("study_accession")
	secondary_study_acc_index = values.index("secondary_study_accession")
	run_accession_index = values.index("run_accession")
	center_name_index = values.index("center_name")
	instrument_model_index = values.index('instrument_platform')
	fastq_files_index = values.index("fastq_ftp")
	fastq_md5_index = values.index("fastq_md5")

	""" Now skip the header line  and fetch column contents  """

	attributes_all = list()
	i = 1
	for line in lines:
		val = line.strip().split("\t")
		if i > 1:
			if len(val) != header_len:
				message = "\nLine number:{} has wrong number of column : {} vs {} \n".format(i, len(val), header_len)
				print(message)
				error_list.append("ERROR:{} {}".format(message, val))
				log_error(message, 'error', log_file)
			else:
				selection_id = ''
				process_id = ''
				datahub = ''
				tax_id = val[tax_id_index]
				scientific_name = val[scientific_name_index]
				sample_accession = val[sample_accession_index]
				secondary_sample_acc = val[secondary_sample_acc_index]
				experiment_accession = val[experiment_accession_index]
				study_accession = val[study_accession_index]
				secondary_study_acc = val[secondary_study_acc_index]
				run_accession = val[run_accession_index]
				pipeline_name = ''
				provider_center_name = val[center_name_index]
				provider_webin_id = ''  # val[provider_webin_id_index]
				instrument_model = val[instrument_model_index]
				fastq_files = val[fastq_files_index]
				fastq_md5 = val[fastq_md5_index]
				public = ''
				analyst_webin_id = ''
				attr = default_attributes(process_id, selection_id, datahub, tax_id, scientific_name,
										  sample_accession, secondary_sample_acc, experiment_accession,
										  study_accession, secondary_study_acc, run_accession, pipeline_name,
										  provider_center_name, provider_webin_id, instrument_model, fastq_files, fastq_md5,
										  public, analyst_webin_id)

				attributes_all.append(attr)
		i += 1
	return attributes_all


def get_list_of_study(selections):
	"""
	get_list_of_study: list of studies per metadata files
	:param selections:  default_attributes object
	:return: list of studies
	"""
	studies = list()
	for select in selections:
		studies.append(select.study_accession)
	return studies


def get_process_id(id):
	"""
	get_process_id: generate a string of dmYHMS
	:param id: process_id
	:return: unique name of string and dateyeartime
	"""
	return id + "-" + str(time.strftime("%d%m%Y%H%M%S"))


def insert_default_stages(conn, process_id, selection_id):
	"""
	insert_default_stages: Populate process_stages with various
	pipeline stages: data_provider, core_executor, analysis_reporter
	process_archival with start, end time and errors
	:param conn: PostGreSQL connection
	:param process_id: process id
	:param selection_id: selection id
	:return: None
	"""
	stage_list = [stages.data_provider_stage_name, stages.core_executor_stage_name, stages.analysis_reporter_stage_name,
				  stages.process_archival_stage_name]
	print(ruler)
	print(process_id, selection_id, stage_list)
	print(ruler)
	print(process_id, selection_id, stage_list, file=sys.stdout)
	default_stage = stages(process_id, selection_id, stage_list)
	default_stage.insert_all_into_process_stages(conn)


def set_started(conn, selection_id):
	error_list = list()
	query = "update process_selection set selection_to_attribute_start=NOW() where selection_id={}".format(selection_id)
	cursor = conn.cursor()
	try:
		cursor.execute(query)
		conn.commit()
	except:
		print("ERROR: Cannot update process_stages set stage_start=NOW():", file=sys.stderr)
		message = str(sys.exc_info()[1])
		error_list.append(message)
		print("Exception: {}".format(message), file=sys.stderr)
		conn.rollback()


def set_finished(conn, selection_id):
	"""
	set_finished: Update process_selection table, set end time to curtime()
	:param conn: PostGreSQL connection
	:param selection_id: selection id
	:return: None
	"""
	error_list = list()
	query = "update process_selection set selection_to_attribute_end=NOW() where selection_id={}".format(selection_id)
	cursor = conn.cursor()
	try:
		cursor.execute(query)
		conn.commit()
	except:
		print("ERROR: Cannot update process_stages set stage_end=NOW():", file=sys.stderr)
		message = str(sys.exc_info()[1])
		error_list.append(message)
		print("Exception: {}".format(message), file=sys.stderr)
		conn.rollback()


def process_report_set_started(conn, info):
	"""
	process_report_set_started: Populate process_report table
	with various attributes: study_accession,datahub,run_accession,process_id,
	selection_id,process_report_start_time
	:param conn: PostGreSQL connection
	:param info: info is a dict with the following:
		study_id, datahub, run_id,process_id, selection_id, start_time
	:return: None
	"""
	error_list = list()
	study_accession = info['study_accession']
	run_accession = info['run_accession']
	datahub = info['datahub']
	process_id = info['process_id']
	selection_id = info['selection_id']
	query = "INSERT INTO process_report (study_accession,datahub,run_accession,process_id,\
	selection_id,process_report_start_time) values('{}','{}','{}','{}','{}',now())".format(study_accession,
																						   datahub,
																						   run_accession,
																						   process_id,
																						   selection_id)
	print(ruler)
	print("PROCESS_REPORT QUERY:\n\t{}".format(query), "\n", sep="")
	print(ruler)
	cursor = conn.cursor()
	try:
		cursor.execute(query=query)
		conn.commit()
	except:
		print(
			"Error: Can not INSERT study:{} datahub:{} process_id:{} selection_id:{} run:{} in process_report ".format(study_accession,
																													   datahub,
																													   process_id,
																													   selection_id,
																													   run_accession), file=sys.stderr)
		traceb, message, trace_back = sys.exc_info()
		error_list.append(message)
		print("Exception: exc_info[0]:{}, exc_info[1]:{} , exc_info[2]{} ".format(traceb, message, trace_back), file=sys.stderr)
		conn.rollback()
		cursor.execute('show profiles')
		for row in cursor:
			print(row)


def process_report_set_finished(conn, process_report_id):
	"""
	process_report_set_finished: Populate process_report table
	with finish time this is called by process_archival script.
	:param con: PostGreSQL connection
	:param process_report_id:  process_report id
	:return: None
	"""
	error_list = list()
	query = "update process_report set process_report_end_time=NOW()\
	 where process_report_id={}".format(process_report_id)
	cursor = conn.cursor()
	try:
		cursor.execute(query)
		conn.commit()
		return True
	except:
		print("ERROR: can not set process_report_end_time to NOW():", file=sys.stderr)
		message = str(sys.exc_info()[1])
		error_list.append(message)
		print("Exception: {}".format(message), file=sys.stderr)
		conn.rollback()
		return False



def set_error(conn, selection_id, error):
	"""
	set_error:
	Upate process_selection table with any error that occur while populating process_stage,
	process_attributes, process_report table with information from the datahub metadata file
	:param conn: PostGreSQL connection
	:param selection_id: selection_id (process_selection table native)
	:param error: Any error encounter during selection_to_attributes runs ...
	:return: None
	"""
	error = error[:500]
	error_list = list()
	query = "update process_selection set selection_to_attribute_error='{}' where selection_id='{}'".format(error,
																										  selection_id)
	print('=' * 100)
	print(textwrap.fill(query, 100))
	print(error)
	print(query)
	print("LENGTH OF ERROR:", len(error))
	print('=' * 100)
	cursor = conn.cursor()
	try:
		cursor.execute(query)
		conn.commit()
		return True
	except (Exception, psycopg2.DatabaseError) as db_err:
		print(db_err)
		print("PostGreSQL ERROR AND WARNING {}".format(db_err), file=sys.stderr)
		print("Error: Cannot{}".format(query), file=sys.stderr)
		message = str(sys.exc_info()[1])
		error_list.append(message)
		print("Exception: {}".format(message), file=sys.stderr)
		conn.rollback()
		return False


def check_started(conn, selection_id):
	"""
	check_started: Fetch entries from process_selection with null start
	date.
	:param conn: PostGreSQL connection
	:param selection_id: selection_id
	:return: Boolean (True/False)
	"""
	query = "select selection_id from process_selection where selection_to_attribute_start is null"
	print(ruler, "\nCHECK_STARTED function query:\n\t{}".format(query), "\n", ruler, sep="")
	cursor = conn.cursor()
	cursor.execute(query)
	selection_id_all = list()
	for row in cursor:
		selection_id_all.append(row[0])
	if selection_id in selection_id_all:
		"""Not started"""
		return False
	else:
		"""Started"""
		return True


def is_processing_type(conn, selection_id):
	"""
	is_processing_type: what is type of processing will be carried out.
	datahub -> study -> runs
	:param conn: PostGreSQL connection
	:param selection_id: selection_id
	:return: datahub or study or runs
	"""
	query = "select distinct process_type from process_selection where selection_id='{}'".format(selection_id)
	cursor = conn.cursor()
	process_type = list()
	cursor.execute(query)
	process_type = cursor.fetchall()[0][0]
	print(ruler, "\nIs the processing type:\n{}\n Process type is: {}".format(query,
																			  process_type), "\n", ruler, sep="")
	return process_type


def already_ran_runs(conn, selection_id, processing_type):
	"""
	already_ran_runs: Get previously ran runs accession from the
	Process_report table.
	:param conn: PostGreSQL connection
	:param selection_id: selection_id
	:param processing_type:  processing type (datahub, study, run)
	:return: ran run accessions.
	"""
	error_list = list()
	if processing_type.lower() == 'run':
		query = "Select distinct run_accession from process_report where process_report_start_time is not null and  process_report_end_time is null and selection_id ={}".format(
			selection_id)
	else:
		query = "Select distinct run_accession from process_report where process_report_start_time is not null and selection_id ={}".format(selection_id)
	print(query)
	cursor = conn.cursor()
	try:
		cursor.execute(query)
		ran_accessions = [run[0] for run in cursor]
	except:
		message = str(sys.exc_info()[1])
		error_list.append(message)
		print("Exception: {}".format(message), file=sys.stderr)
		conn.rollback()
	return ran_accessions


def exclude_processed_run(select, attributes_all, already_ran_run_accs):
	"""
	exclude_processed_run: exclude those runs that have been processed.
	This is actionable when the continuity is set to Yes in process_selection
	table
	:param select: an object from the attr list of objects
	:param attributes_all: a list of attribute objects
	:param already_ran_run_accs: already processed runs
	:return: list of runs to exclude from the analysis
	"""
	type_run_accs = set()
	print('/' * 100)
	print("PROCESS_TYPE:{} -> Selection_id {} ,\
	already_run:{} Against:{}".format(select.process_type,
									  select.selection_id,
									  len(already_ran_run_accs),
									  len([attr.run_accession for attr in attributes_all])))
	print(select.process_type)
	print('/' * 100)
	if select.process_type.lower() == 'study':
		type_run_accs = set([attr.run_accession for attr in attributes_all if select.study_accession.strip() == attr.study_accession.strip()])
		print('|'*100)
		print(type(type_run_accs))
		print("Length type run :{}".format(len(type_run_accs)))
		print('|'*100)
	elif select.process_type.lower() == 'datahub':
		type_run_accs = set([attr.run_accession for attr in attributes_all])
		print('/'*100)
		print("PROCESS_TYPE:{}".format(select.process_type))
		print('/'*100)
	elif select.process_type.lower() == 'run':
		type_run_accs = set([attr.run_accession for attr in attributes_all if attr.run_accession.strip() == select.run_accession.strip()])

	type_to_run_accs = list(type_run_accs.difference(set(already_ran_run_accs)))
	type_attributes_all = list()
	print('-' * 100)
	print('Processing type is {} and continuity is {}'.format(select.process_type, select.continuity))
	print("{} Runs accessions from metadatafile...".format(len(type_run_accs)))
	print("{} Runs already processed...".format(len(already_ran_run_accs)))
	print("{} Runs accession that will be processed this time...".format(len(type_to_run_accs)))
	print(type_to_run_accs)
	print('_' * 100)
	for attr in attributes_all:
		if attr.run_accession in type_to_run_accs:
			type_attributes_all.append(attr)
	attributes_all = type_attributes_all
	return attributes_all


def main():
	"""
	Main call to the data_provider scripts.
	:return: None
	"""
	# properties_file = get_args()
	options = process_arguments(sys.argv[1:])
	properties_file = options.properties_file
	prop = properties(properties_file)
	""" From class SelectaDB Return a propertie object """
	if (options.db_live):
		try:
			print('-'*100)
			print("PostGres DB is live and accepting connection")
			conn = get_connection(prop.dbuser, prop.dbpassword, prop.dbhost, prop.dbname, prop.dbport)
			print('-' * 100)
		except:
			print(sys.exc_info())
	else:
		conn = get_connection(prop.dbuser, prop.dbpassword, prop.dbhost, prop.dbname, prop.dbport)
		""" From PostGreSQL return a connection object to localhost """
		workdir = prop.workdir_input
		lsf = prop.lsf
		error_list = list()
		accounts = get_datahub_accounts(conn)
		""" Accounts is list of dictionaries of users accounts and passwords """
		selections = get_selection_to_attributes_account(conn)
		print('-' * 100)
		print("SELECTION_LIST: {}".format(selections))
		print('-' * 100)

		"""Selections is a list of datahub account, eg: dcc_allison """
		global log_file
		log_file = 'log.txt'
		final_errors = ''
		for account in accounts:
			print('-' * 100)
			print('Looping in account lists {}'.format(account))
			print(selections)
			print('-' * 100)
			account_id = account['account_id']
			if account_id in selections and account_id != 'dcc_fake':
				outputfile, job = fetch_datahub_metadatafile(account, workdir, lsf)
				"""Get metadata per datahub accounts"""
				localinfo = "account {} has the corresponding metadatafile {} ".format(account, outputfile)
				print(ruler)
				print(localinfo)
				print(ruler)
				""" GET_SELECTION_INFO return a SELECTADB.class.SELECTION object
				this object is made up of selection_id, tax_id, study_acc, run_acc,
				pipeline_name, analysis_id, public, webin, datahub(eg:dcc_allison).
				These are fetched from process_selection table
				"""
				selection_all = get_selection_info(conn, account_id)
				""" """
				print('-' * 100)
				print('\n'.join(map(str, [a.__dict__ for a in selection_all])))
				print('-' * 100)

				if os.stat(outputfile).st_size == 0:
					for select in selection_all:
						print('File size is zero .....')
						message = "Failed to download the metadata file {} from account {}".format(outputfile, account_id)
						log_error(message, 'error', log_file)
						error_list.append(message)
						print(outputfile, select.selection_id, select.pipeline_name, select.datahub, select.study_accession,
							  file=sys.stdout)
						final_errors = ' '.join(str(v).replace("'", "") for v in error_list)
						final_errors.replace("'", "")
						# TODO: change it in a way if it doesn't find the metadata file, just log it into log file and clear the
						# start column to be able to re-run it again
						print(ruler)
						print(textwrap.fill(final_errors, 250))
						print("SELECION_ID: {} ".format(select.selection_id))
						print(ruler)
						set_error(conn, select.selection_id, final_errors)
				else:
					print('Metadata found with following id:{}'.format(account_id), file=sys.stdout)
					try:
						attributes_all = get_default_attributes(outputfile)
						print('_' * 100)
						print("Processing datahub :{}\nInitial attribute_all length {}".format(account_id, len(attributes_all)))
						print('_' * 100)
						all_run_accs = []
						""" GET_DEFAULT_ATTRIBUTE, extract from the metadata tab delimited file the following information:
						tax_id	scientific_name	sample_accession	secondary_sample_accession	experiment_accession
						study_accession	secondary_study_accession	run_accession	center_name instrument_model fastq_ftp fastq_md5
						attributes_all is a list containing all the data for a given dcc_user, with process_id,selection_id,datahub set to ''
						since the latter are missing from the metadata file.
						"""
					except:
						# TODO in case the study exist, we shouldn't through database error and just log it and clear the
						# satrt column to be able to re-run it again
						print("ERROR: Cannot process {} file".format(outputfile), file=sys.stderr)
						# message="Exception: "+str(sys.exc_info()[1])
						exc_type, exc_value, exc_traceback = sys.exc_info()
						err_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
						message = '\n'.join(err_lines)
						print("message:{}".format(message))
						error_list.append(message)
						error_list.append("ERROR: Cannot process {} file".format(outputfile))
						print("Exception: {}".format(message), file=sys.stderr)

					for select in selection_all:
						""" selection_all= selection_id, tax_id, study_acc, run_acc,
							pipeline_name, analysis_id, public, webin, selection_to_attribute_end, process_type, continuity, datahub(eg:dcc_allison).
							These are fetch from process_selection.
							What is the processing type:
						"""
						print('-' * 100)
						print("Processing Selection_id:{}\nwith process_type:{}\nand continuity:{}".format(select.selection_id, select.process_type, select.continuity))
						print('-' * 100)
						processing_type = select.process_type
						continuity = select.continuity
						selection_to_attribute_end = select.selection_to_attribute_end
						if not error_list:
							print("\n\nThe processing of the metadata with project:{} datahub:{} had zero errors:\n".format(select.study_accession,
																															select.datahub))

							try:
								if not check_started(conn, select.selection_id):
									""""
									Check_started : return true or false for selection_process_start
									ie Is selection_id from process_selection has (selection_to_attribute_start null)
									"""
									set_started(conn, select.selection_id)
									""""
									set_started: set selection_to_attribute_start to now() for selection_id in process_selection
									Here we have to make use of the continuity value in select object to proceed further
									"""
									#study_to_run_acc = list()
									#datahub_to_run_acc = list()
									#run_to_run_acc = list()

									if continuity.lower() == "yes":
										"""
										update the process_stage and process_report table for
										subset of run_id not already processed
										"""
										print("CONTINUITY YES met")
										already_ran_run_accs = already_ran_runs(conn, select.selection_id, processing_type)
										print("Already ran runs: {}".format(len(already_ran_run_accs)))
										""" Excluded already processed runs if any """
										print([attr.run_accession for attr in attributes_all][1:10])
										attributes_all = exclude_processed_run(select, attributes_all,
																			   already_ran_run_accs)
										print('*'*100)
										print([attr.run_accession for attr in attributes_all][1:10])
										print('*'*100)
										print('*' * 100)
										print("New attribute_all length {}".format(len(attributes_all)))
										print(attributes_all)
										print('*' * 100)

									for attr in attributes_all:
										""" Select runs under study_id in process selection """
										if processing_type.lower() == 'study' and \
														select.study_accession.strip() == attr.study_accession.strip():
											report_process = Process_report(select, attr, error_list)
											report_process.log_process_report_info(conn)
										elif processing_type.lower() == 'run' and \
														select.run_accession.strip() == attr.run_accession.strip():
											print("*"*100)
											print(processing_type)
											print("*"*100)
											all_run_accs = [attr.run_accession for attr in attributes_all if select.run_accession.strip() == attr.run_accession.strip()]

											""" Select specific run id for processing """
											report_process = Process_report(select, attr, error_list)
											report_process.log_process_report_info(conn)
										elif processing_type.lower() == 'datahub':
											all_run_accs = [attr.run_accession for attr in attributes_all]
											""" Select all runs under the dcc_hub account for processing """
											report_process = Process_report(select, attr, error_list)
											report_process.log_process_report_info(conn)

							except:
								print("ERROR: Cannot process selection_id {}".format(select.selection_id), file=sys.stderr)
								#message = str(sys.exc_info()[1])
								message = str(sys.exc_info())
								error_list.append(message)
								print("Exception: {}".format(message), file=sys.stderr)
								final_errors = ' '.join(str(v).replace("'", "") for v in error_list)
								print('*' * 100)
								print(final_errors)
								print('*' * 100)
								set_error(conn, select.selection_id, final_errors.replace("'", ""))
								error_list = list()

						else:
							final_errors = ' '.join(str(v).replace("'", "") for v in error_list)
							print("ERRORs: {}".format(final_errors), file=sys.stderr)
							set_error(conn, select.selection_id, final_errors.replace("'", ""))
						print('-' * 100)
						""" Amend various SELECTA table with metadata from each SELECTION_ID"""

						print('SELECT From SELECTION_ALL next Loop')
					error_list = list()
		conn.close()

if __name__ == '__main__':
	main()
