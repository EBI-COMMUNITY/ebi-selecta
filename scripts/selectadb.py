

class selection:

	def __init__(self, selection_id, datahub,tax_id,study_accession,run_accession,pipeline_name,analysis_id,public,analyst_webin_id):
		self.selection_id = selection_id
		self.datahub = datahub
		self.tax_id = tax_id
		self.study_accession=study_accession
		self.run_accession=run_accession
		self.pipeline_name=pipeline_name
		self.analysis_id=analysis_id
		self.public=public
		self.analyst_webin_id=analyst_webin_id
		
        
        
		
class properties:
	
	def __init__(self, property_file):
		with open(property_file) as f:
			 lines = f.readlines()
		
		workdir_provided=False
		workdir_input_provided=False
                archivedir_provided=False
		dbuser_provided=False
		dbpassword_provided=False
		dbhost_provided=False
		dbname_provided=False
		dtu_cge_databases_provided=False
        emc_slim_program_provided=False
        emc_slim_property_file_provided=False
        analysis_submission_mode_provided=False
        analysis_submission_action_provided=False
        analysis_submission_url_provided=False
	        
		
		for l in lines:
			pair=l.strip().split(":")
			if pair[0].lower()=='workdir':
				self.workdir=pair[1]
				workdir_provided=True
                        elif pair[0].lower()=='workdir_input':
                                self.workdir_input=pair[1]
                                workdir_input_provided=True
			elif pair[0].lower()=='archivedir':
				self.archivedir=pair[1]
				archivedir_provided=True
			elif pair[0].lower()=='dbuser':
				self.dbuser=pair[1]
				dbuser_provided=True
			elif pair[0].lower()=='dbpassword':
				self.dbpassword=pair[1]
				dbpassword_provided=True
			elif pair[0].lower()=='dbhost':
				self.dbhost=pair[1]
				dbhost_provided=True
			elif pair[0].lower()=='dbname':
				self.dbname=pair[1]
				dbname_provided=True
            elif pair[0].lower()=='emc_slim_program':
                self.emc_slim_program=pair[1]
                emc_slim_program_provided=True
            elif pair[0].lower()=='emc_slim_property_file':
                self.emc_slim_property_file=pair[1]
                emc_slim_property_file_provided=True
			elif pair[0].lower()=='dtu_cge_databases':
				self.dtu_cge_databases=pair[1]
				dtu_cge_databases_provided=True
            elif pair[0].lower()=='analysis_submission_mode':
				self.analysis_submission_mode=pair[1]
				analysis_submission_mode_provided=True
            elif pair[0].lower()=='analysis_submission_action':
                self.analysis_submission_action=pair[1]
                analysis_submission_action_provided=True
            elif pair[0].lower()=='dtu_cge_databases':
                self.analysis_submission_url=pair[1]
                analysis_submission_url_provided=True
				
		
		if workdir_provided==False:
			self.workdir=''
                if workdir_input_provided==False:
                        self.workdir_input=''
		if archivedir_provided==False:
		   self.archivedir=''
		if dbuser_provided==False:
		   self.dbuser_provided=''
		if dbpassword_provided==False:
		   self.dbpassword_provided=''
		if dbhost_provided==False:
		   self.dbhost=''
		if dbname_provided==False:
		   self.dbname=''
        if emc_slim_program_provided==False:
           self.emc_slim_program=''
        if emc_slim_property_file_provided==False:
           self.emc_slim_property_file=''
		if analysis_submission_mode_provided==False:
		   self.analysis_submission_mode=''
        if dtu_cge_databases_provided==False:
           self.dtu_cge_databases=''
        if analysis_submission_action_provided==False:
           self.analysis_submission_action=''
        if analysis_submission_url_provided==False:
           self.analysis_submission_url=''


		
		
		
		
		
		
		
		
		
		
		
		
