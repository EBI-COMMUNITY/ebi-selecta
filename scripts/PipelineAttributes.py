
import sys
import time

class default_attributes:
	
	global selection_id_key
	global process_id_key
	global datahub_key
	global tax_id_key
	global scientific_name_key
	global sample_accession_key
	global secondary_sample_acc_key
	global experiment_accession_key
	global study_accession_key
	global secondary_study_acc_key
	global run_accession_key
	global pipeline_name_key
	global provider_center_name_key
	global provider_webin_id_key
	global fastq_files_key
	global fastq_md5_key
	global public_key
	global analyst_webin_id_key
	
	selection_id_key='selection_id'
	process_id_key='process_id'
	datahub_key='datahub'
	tax_id_key='tax_id'
	scientific_name_key='scientific_name'
	sample_accession_key='sample_accession'
	secondary_sample_acc_key='secondary_sample_acc'
	experiment_accession_key='experiment_accession'
	study_accession_key='study_accession'
	secondary_study_acc_key='secondary_study_acc'
	run_accession_key='run_accession'
	pipeline_name_key='pipeline_name'
	provider_center_name_key='provider_center_name'
	provider_webin_id_key='provider_webin_id'
	fastq_files_key='fastq_files'
	fastq_md5_key='fastq_md5'
	public_key='public'
	analyst_webin_id_key='analyst_webin'
	

	def __init__(self,process_id,selection_id, datahub,tax_id,scientific_name,sample_accession,secondary_sample_acc,experiment_accession,study_accession,secondary_study_acc,run_accession,pipeline_name,provider_center_name,provider_webin_id,fastq_files,fastq_md5,public,analyst_webin_id):
		self.process_id=process_id
		self.selection_id = selection_id
		self.datahub = datahub
		self.tax_id = tax_id
		self.scientific_name=scientific_name
		self.sample_accession=sample_accession
		self.secondary_sample_acc=secondary_sample_acc
		self.experiment_accession=experiment_accession
		self.study_accession=study_accession
		self.secondary_study_acc=secondary_study_acc
		self.run_accession=run_accession
		self.pipeline_name=pipeline_name
		self.provider_center_name=provider_center_name
		self.provider_webin_id=provider_webin_id
		self.fastq_files=fastq_files
		self.fastq_md5=fastq_md5
		self.public=public
		self.analyst_webin_id=analyst_webin_id


	def __str__(self):
		return 'selection_id:'+str(self.selection_id)+'\n'+'datahub:'+self.datahub+'\n'+'tax_id:'+str(self.tax_id)+'\n'+'scientific_name:'+self.scientific_name+'\n'+'sample_accession:'+self.sample_accession+'\n'+'secondary_sample_acc:'+self.secondary_sample_acc+'\n'+'experiment_accession:'+self.experiment_accession+'\n'+'study_accession:'+self.study_accession+'\n'+'secondary_study_acc:'+self.secondary_study_acc+'\n'+'run_accession:'+self.run_accession+'\n'+'pipeline_name:'+self.pipeline_name+'\n'+'provider_center_name:'+self.provider_center_name+'\n'+'provider_webin_id:'+self.provider_webin_id+'\n'+'fastq_files:'+self.fastq_files+'\n'+'fastq_md5:'+self.fastq_md5+'\n'+'public:'+self.public+'\n'+'analyst_webin_id:'+self.analyst_webin_id
		

   
	def insert_into_process_attributes(self,conn,process_id,attribute_key,attribute_value):
		
		if process_id!="" and attribute_value!="":
			query="INSERT INTO process_attributes (process_id,attribute_key,attribute_value) values('%s','%s','%s')"%(process_id,attribute_key,attribute_value)
			cursor = conn.cursor()
			
			try:
				cursor.execute(query)
				#time.sleep(1)
				conn.commit()
		 
			except:
				print "Cannot insert:"
				message=str(sys.exc_info()[1])
				print "Exception: %s"%message
				conn.rollback()
			
	def insert_all_into_process_attributes(self,conn):

		self.insert_into_process_attributes(conn,self.process_id,selection_id_key,self.selection_id)
		self.insert_into_process_attributes(conn,self.process_id,datahub_key,self.datahub)
		self.insert_into_process_attributes(conn,self.process_id,tax_id_key,self.tax_id)
		self.insert_into_process_attributes(conn,self.process_id,scientific_name_key,self.scientific_name)
		self.insert_into_process_attributes(conn,self.process_id,sample_accession_key,self.sample_accession)
		self.insert_into_process_attributes(conn,self.process_id,secondary_sample_acc_key,self.secondary_sample_acc)
		self.insert_into_process_attributes(conn,self.process_id,experiment_accession_key,self.experiment_accession)
		self.insert_into_process_attributes(conn,self.process_id,study_accession_key,self.study_accession)
		self.insert_into_process_attributes(conn,self.process_id,secondary_study_acc_key,self.secondary_study_acc)
		self.insert_into_process_attributes(conn,self.process_id,run_accession_key,self.run_accession)
		self.insert_into_process_attributes(conn,self.process_id,pipeline_name_key,self.pipeline_name)
		self.insert_into_process_attributes(conn,self.process_id,provider_center_name_key,self.provider_center_name)
		self.insert_into_process_attributes(conn,self.process_id,provider_webin_id_key,self.provider_webin_id)
		self.insert_into_process_attributes(conn,self.process_id,fastq_files_key,self.fastq_files)
		self.insert_into_process_attributes(conn,self.process_id,fastq_md5_key,self.fastq_md5)
		self.insert_into_process_attributes(conn,self.process_id,public_key,self.public)
		self.insert_into_process_attributes(conn,self.process_id,analyst_webin_id_key,self.analyst_webin_id)
		
		
class stages:
	global selection_id_key
	global process_id_key
	global stage_name_key
	
		
	selection_id_key='selection_id'
	process_id_key='process_id'
	stage_name_key='stage_name'
	
	data_provider_stage_name='data_provider'
	core_executor_stage_name='core_executor'
	analysis_reporter_stage_name='analysis_reporter'
	process_archival_stage_name='process_archival'
	
	
	def __init__(self,process_id,selection_id,stage_list):
		self.process_id=process_id
		self.selection_id = selection_id
		self.stage_list=stage_list
		
	def insert_into_process_stages(self,conn,process_id,selection_id,stage_name):
		
		#if process_id!="" and selection_id!="" and stage_name!="":
			print "insert_into_process_stages:",process_id,selection_id,stage_name
			query="INSERT INTO process_stages (process_id,selection_id,stage_name) values('%s','%s','%s')"%(process_id,selection_id,stage_name)
			cursor = conn.cursor()
			
			try:
				cursor.execute(query)
				conn.commit()
		 
			except:
				print "Cannot insert:"
				message=str(sys.exc_info()[1])
				print "Exception: %s"%message
				conn.rollback()
		
		
	def insert_all_into_process_attributes(self,conn):
		
		for stage in self.stage_list:
			self.insert_into_process_stages(conn,self.process_id,self.selection_id,stage)
   
