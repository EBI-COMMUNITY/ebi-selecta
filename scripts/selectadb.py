from mock.mock import self


class selection:
    def __init__(self, selection_id, datahub, tax_id, study_accession, run_accession, pipeline_name, analysis_id,
                 public, analyst_webin_id):
        self.selection_id = selection_id
        self.datahub = datahub
        self.tax_id = tax_id
        self.study_accession = study_accession
        self.run_accession = run_accession
        self.pipeline_name = pipeline_name
        self.analysis_id = analysis_id
        self.public = public
        self.analyst_webin_id = analyst_webin_id



class properties:

    def __init__(self, property_file):
        with open(property_file) as f:
            lines = f.readlines()
            print('~' * 50)
            print(type(lines))
            print('~' * 50)
            workdir_provided = False
            workdir_input_provided = False
            archivedir_provided = False
            dbuser_provided = False
            dbpassword_provided = False
            dbhost_provided = False
            dbname_provided = False
            dbport_provided = False
            lsf_provided = False
            rmem_provided = False
            lmem_provided = False
            dtu_cge_databases_provided = False
            emc_slim_program_provided = False
            emc_slim_property_file_provided = False
            analysis_submission_mode_provided = False
            analysis_submission_action_provided = False
            analysis_submission_url_provided = False
            max_core_job_provided = False

            for l in lines:
                print("*" * 100)
                print(l)
                print("*" * 100)
                pair = l.strip().split(":",1)
                if pair[0].lower() == 'workdir':
                    self.workdir = pair[1]
                    workdir_provided = True
                elif pair[0].lower() == 'max_core_job':
                    self.max_core_job = int(pair[1])
                    max_core_job_provided = True
                elif pair[0].lower() == 'workdir_input':
                    self.workdir_input = pair[1]
                    workdir_input_provided = True
                elif pair[0].lower() == 'archivedir':
                    self.archivedir = pair[1]
                    archivedir_provided = True
                elif pair[0].lower() == 'dbuser':
                    self.dbuser = pair[1]
                    dbuser_provided = True
                elif pair[0].lower() == 'dbpassword':
                    self.dbpassword = pair[1]
                    dbpassword_provided = True
                elif pair[0].lower() == 'dbhost':
                    self.dbhost = pair[1]
                    dbhost_provided = True
                elif pair[0].lower() == 'dbname':
                    self.dbname = pair[1]
                    dbname_provided = True
                elif pair[0].lower() == 'dbport':
                    self.dbport = int(pair[1])
                    dbport_provided = True
                elif pair[0].lower() == 'lsf':
                    if pair[1].lower() == 'yes':
                        self.lsf = True
                    elif pair[1].lower() =='no':
                        self.lsf = False
                    lsf_provided = True
                elif pair[0].lower() == 'rmem':
                    self.rmem= pair[1]
                    rmem_provided = True
                elif pair[0].lower() =='lmem':
                    self.lmem=pair[1]
                    lmem_provided = True
                elif pair[0].lower() =='seqmachine':
                    self.seq_machine = pair[1]
                    seq_machine_provided = True
                elif pair[0].lower() == 'emc_slim_program':
                    self.emc_slim_program = pair[1]
                    emc_slim_program_provided = True
                elif pair[0].lower() == 'emc_slim_property_file':
                    self.emc_slim_property_file = pair[1]
                    emc_slim_property_file_provided = True
                elif pair[0].lower() == 'dtu_cge_databases':
                    self.dtu_cge_databases = pair[1]
                    dtu_cge_databases_provided = True
                elif pair[0].lower() == 'analysis_submission_mode':
                    self.analysis_submission_mode = pair[1]
                    analysis_submission_mode_provided = True
                elif pair[0].lower() == 'analysis_submission_action':
                    self.analysis_submission_action = pair[1]
                    analysis_submission_action_provided = True
                elif pair[0].lower() == 'analysis_submission_url':
                    self.analysis_submission_url = pair[1]
                    analysis_submission_url_provided = True


            if not workdir_provided:
                self.workdir = ''
            if not max_core_job_provided:
                self.max_core_job = 10
            if not workdir_input_provided:
                self.workdir_input = ''
            if not archivedir_provided:
                self.archivedir = ''
            if not dbuser_provided:
                self.dbuser_provided = ''
            if not dbpassword_provided:
                self.dbpassword_provided = ''
            if not dbhost_provided:
                self.dbhost = ''
            if not dbname_provided:
                self.dbname = ''
            if not dbport_provided:
                self.dbport = 3306
            if not lsf_provided:
                self.lsf = ''
            if not seq_machine_provided:
                self.seq_machine = ''
            if not rmem_provided:
                self.rmem=''
            if not lmem_provided:
                self.lmem=''
            if not emc_slim_program_provided:
                self.emc_slim_program = ''
            if not emc_slim_property_file_provided:
                self.emc_slim_property_file = ''
            if not analysis_submission_mode_provided:
                self.analysis_submission_mode = ''
            if not dtu_cge_databases_provided:
                self.dtu_cge_databases = ''
            if not analysis_submission_action_provided:
                self.analysis_submission_action = ''
            if not analysis_submission_url_provided:
                self.analysis_submission_url = ''
