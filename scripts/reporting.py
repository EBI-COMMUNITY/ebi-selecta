from PipelineAttributes import stages
from mock.mock import self
import time
import sys

__author__ = 'Nima Pakseresht, Blaise Alako'

import cx_Oracle

class Oracle(object):

    def connect(self, username, password, hostname, port, servicename):
        """ Connect to the database. """

        try:
            self.db = cx_Oracle.connect(username, password
                                , hostname + ':' + port + '/' + servicename)
        except cx_Oracle.DatabaseError as e:
            # Log error as appropriate
            raise

        # If the database connection succeeded create the cursor
        # we-re going to use.
        self.cursor = self.db.cursor()

    def disconnect(self):
        """
        Disconnect from the database. If this fails, for instance
        if the connection instance doesn't exist, ignore the exception.
        """

        try:
            self.cursor.close()
            self.db.close()
        except cx_Oracle.DatabaseError:
            pass

    def execute(self, sql, bindvars=None, commit=False):
        """
        Execute whatever SQL statements are passed to the method;
        commit if specified. Do not specify fetchall() in here as
        the SQL statement may not be a select.
        bindvars is a dictionary of variables you pass to execute.
        """

        try:
            self.cursor.execute(sql, bindvars)
        except cx_Oracle.DatabaseError as e:
            # Log error as appropriate
            raise

        # Only commit if it-s necessary.
        if commit:
            self.db.commit()


def get_process_id(id):
    time.sleep(2)
    return id + "-" + str(time.strftime("%d%m%Y%H%M%S"))


def set_started(conn, selection_id):
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


def insert_default_stages(conn, process_id, selection_id):
    stage_list = [stages.data_provider_stage_name, stages.core_executor_stage_name, stages.analysis_reporter_stage_name,
                  stages.process_archival_stage_name]
    print('*' * 100)
    print(process_id, selection_id, stage_list)
    print('*' * 100)
    print(process_id, selection_id, stage_list, file=sys.stdout)
    default_stage = stages(process_id, selection_id, stage_list)
    default_stage.insert_all_into_process_stages(conn)


def process_report_set_started(conn, info):
    """info is a dict with the following:
	    study_id, datahub, run_id,process_id, selection_id, start_time
	"""
    study_accession = info['study_accession']
    run_accession = info['run_accession']
    datahub = info['datahub']
    process_id = info['process_id']
    selection_id = info['selection_id']
    query = "INSERT INTO process_report (study_accession,datahub,run_accession,process_id,selection_id,process_report_start_time) values('{}','{}','{}','{}','{}',now())".format(
        study_accession, datahub, run_accession, process_id, selection_id)
    print('*' * 100)
    print("PROCESS_REPORT QUERY:\n\t{}".format(query), "\n", sep="")
    print('*' * 100)
    cursor = conn.cursor()
    try:
        cursor.execute(query=query)
        conn.commit()
    except:
        print(
            "Error: Can not INSERT study:{} datahub:{} process_id:{} selection_id:{} run:{} in process_report ".format(
                study_accession, datahub, process_id, selection_id, run_accession), file=sys.stderr)
        traceb, message, tb = sys.exc_info()
        error_list.append(message)
        print("Exception: exc_info[0]:{}, exc_info[1]:{} , exc_info[2] ".format(traceb, message, tb), file=sys.stderr)
        conn.rollback()
        cursor.execute('show profiles')
        for row in cursor:
            print(row)



def already_ran_runs (conn, selection_id):
    """ Get previously ran run accessions from the Process
        report table ....
    """
    query ="Select distinct run_accession from process_report where process_report_start_time is not null and selection_id ={}".format(selection_id)
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


class Process_report:
    def __init__(self, select, attr, error_list):
        self.select = select
        self.attr = attr
        self.error_list = error_list
        self.continuity = select.continuity
        self.selection_to_attribute_end = select.selection_to_attribute_end
        self.attr.selection_id = select.selection_id
        self.attr.datahub = select.datahub
        self.attr.pipeline_name = select.pipeline_name
        self.attr.public = select.public
        self.attr.analyst_webin_id = select.analyst_webin_id
        self.attr.process_id = get_process_id(attr.run_accession)


    def log_process_report_info(self, conn):
        self.info = dict()
        self.conn = conn

        """" We need to update process_report with study_id, datahub, run_id,process_id, selection_id, start_time """
        self.info['study_accession'] = self.attr.study_accession
        self.info['datahub'] = self.select.datahub
        self.info['run_accession'] = self.attr.run_accession
        self.info['process_id'] = self.attr.process_id
        self.info['selection_id'] = self.select.selection_id
        print('=' * 100)
        print("Process report info:")
        print(self.info)
        print('=' * 100)

        """ GET_PROCESS_ID takes a run id and append to it the current date and time """
        """ Contiguity is NO """

        self.attr.insert_all_into_process_stages(self.conn)

        """ INSERT_ALL_INTO_PROCESS_STAGE call on INSERT_INTO_PROCESS_STAGE process_stages
            (process_id, selection_id, stage_name)
        """
        insert_default_stages(self.conn, self.attr.process_id, self.attr.selection_id)

        """" calls insert_all_into_process_stages to insert stage_list into process_stages
            stage_list = [stages.data_provider_stage_name, stages.core_executor_stage_name,
            stages.analysis_reporter_stage_name,stages.process_archival_stage_name] 
            Update process_report table 
        """
        """ Update process_report table """
        process_report_set_started(self.conn, self.info)

        if len(self.error_list) != 0:
            self.final_errors = ' '.join(str(v).replace("'", "") for v in self.error_list)
            set_error(self.conn, self.select.selection_id, self.final_errors.replace("'", ""))
        else:
            set_finished(self.conn, self.select.selection_id)
            """"SET_FINISHED: updates process_selection by 
                setting selection_to_attribute_end
            """
        self.error_list = list()
