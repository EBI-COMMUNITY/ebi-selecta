import os
import subprocess
import sys
from glob import glob
import tarfile
import zipfile
from shutil import copyfile
import shutil




class dtu_cge:
	
	''' 
	
docker run -ti --rm -v /analysis/cbs/databases:/databases -v /analysis/nima/cge-workspace/workspace:/workdir cgetools BAP --wdir /workdir --fq1 /workdir/ERR1698597_1.fastq.gz  --fq2 /workdir/ERR1698597_2.fastq.gz --Asp Illumina --Ast paired

docker run -ti --rm -v /Users/nimap/Google-Drive/workspace/ebi-selecta/databases/dtu-databases:/databases -v /Users/nimap/Google-Drive/workspace/ebi-selecta/process/ERR1597716-01122016015700:/workdir cgetools BAP --wdir /workdir --fq1 /workdir/ERR1597716_1.fastq.gz --fq2 /workdir/ERR1597716_2.fastq.gz --Asp Illumina --Ast paired

docker run -ti --rm -v /Users/nimap/Google-Drive/workspace/ebi-selecta/databases/dtu-databases:/databases -v /Users/nimap/Google-Drive/workspace/ebi-selecta/process/ERR1597716-01122016100820:/workdir cgetools BAP --wdir /workdir --fq1 /workdir/ERR029449_1.fastq.gz --fq2 /workdir/ERR029449_2.fastq.gz --Asp Illumina --Ast paired


$database_dir: /Users/nimap/Google-Drive/workspace/ebi-selecta/databases/dtu-databases
$workdir: /Users/nimap/Google-Drive/workspace/ebi-selecta/process/ERR1597716-01122016015700
--fq1:/workdir/ERR1597716_1.fastq.gz
--fq2:/workdir/ERR1597716_2.fastq.gz
 docker run -ti --rm -v
 --Asp Illumina 
 --Ast paired
 
	'''
	#global error_list
	#error_list=list()
	
	def __init__(self,fq1,fq2,database_dir,workdir,sequencing_machine, pair,run_accession):
		self.fq1=fq1
		self.fq2=fq2
		self.run_accession=run_accession
		self.database_dir=database_dir
		self.workdir=workdir
		self.sequencing_machine=sequencing_machine
		self.pair=pair
		error_list=list()
		self.error_list=error_list
		
		
	def command_builder(self):
		command=""
		if self.pair=='True':
			command="docker run -ti --rm -v %s:/databases -v %s:/workdir cgetools BAP --wdir /workdir --fq1 /workdir/%s --fq2 /workdir/%s --Asp %s --Ast paired"%(self.database_dir,self.workdir,self.fq1,self.fq2,self.sequencing_machine)
		else:
			message="ERROR:Currently cannot deal with non paired fastq files in dtu_sge object"
			#print "Currently cannot deal with non paired fastq files in dtu_sge object"
			self.error_list.append(message.replace("'",""))
		return command
		
		
	def run(self,command):
		print "running the command"
		print command
		sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		
		out, err = sp.communicate()
		if out:
			print "standard output of subprocess:"
			print out
			data=out.split('\n')
			i=0
			for line in data:
				if 'error' in line.lower(): 
					message=data[i-1]+'\n'+data[i]
					self.error_list.append(message.replace("'",""))
				i=i+1

        if err:
            print "standard error of subprocess:"
            print err
            data=err.split('\n')
            i=0
            for line in data:
                if 'error' in line.lower():
                    message=data[i-1]+'\n'+data[i]
                    self.error_list.append(message.replace("'",""))
                i=i+1
        if sp.returncode!=0:
            self.error_list.append(err.replace("'",""))
        print >> sys.stderr, err
		
		
			

	#@staticmethod	
	def copy_src_into_dest(self,src, dest):
			name=os.path.basename(src)
			dest_file=os.path.join(dest, name)
			try:
				shutil.copytree(src, dest_file)
			except shutil.Error as e:
				message='Directory not copied. Error: %s' %e
				self.error_list.append(message.replace("'",""))
				print(message)
			except OSError as e:
				message='Directory not copied. Error: %s' %e
				self.error_list.append(message.replace("'",""))
				print(message)
			
	@staticmethod	
	def delete_empty_files(folder):
		for root, dirs, files in os.walk(folder):
			for file in files:
				fullname = os.path.join(root, file)
				
				if os.path.getsize(fullname) == 0:
					print 'To be deleted files:\n',fullname
					os.remove(fullname)
					
	@staticmethod	
	def make_tar_gzip(src,des):
		name=os.path.basename(src)+'.tar.gz'
		print "name:",name
		des=os.path.join(des, name)
		with tarfile.open(des, "w:gz") as tar:
			 tar.add(src, arcname=os.path.basename(src))
			 
	@staticmethod
	def zip_dir(src):
		filename=os.path.basename(src)+'.zip'
		print filename
		zf = zipfile.ZipFile(filename, "w")
		for dirname, subdirs, files in os.walk(src):
			print dirname, subdirs, files
			zf.write(dirname)
			for filename in files:
			   zf.write(os.path.join(dirname, filename))
		zf.close()
		
	

		@staticmethod
		def del_file(filename):
			if os.path.exists(filename):
				shutil.rmtree(filename)

		#def change_permission(filename):


	def post_process(self):
		print "doing post process:"
		command='chmod -R ugo+rw %s'%self.workdir
		print command
		self.run(command)
		dtu_cge.delete_empty_files(self.workdir)
		all_result_name=self.workdir+self.run_accession+"_analysis_DTU_CGE_all"
		dtu_cge.del_file(all_result_name)
		all_result_name_gzip=self.workdir+self.run_accession+"_analysis_DTU_CGE_all.tar.gz"
		dtu_cge.del_file(all_result_name_gzip)
		tab_result_name=self.workdir+self.run_accession+"_analysis_DTU_CGE_summary.tsv"
		dtu_cge.del_file(tab_result_name)
		src_tsv_file=self.workdir+'out.tsv'
		print all_result_name
		print tab_result_name
		if not os.path.exists(all_result_name):
			os.makedirs(all_result_name)
	
		self.run(command)	
		Assembler_dir=self.workdir+'Assembler'
		self.copy_src_into_dest(Assembler_dir, all_result_name)
		ContigAnalyzer_dir=self.workdir+'ContigAnalyzer'
		self.copy_src_into_dest(ContigAnalyzer_dir, all_result_name)
		KmerFinder_dir=self.workdir+'KmerFinder'
		self.copy_src_into_dest(KmerFinder_dir, all_result_name)
		PlasmidFinder_dir=self.workdir+'PlasmidFinder'
		if os.path.exists(PlasmidFinder_dir):
			self.copy_src_into_dest(PlasmidFinder_dir, all_result_name)
		ResFinder_dir=self.workdir+'ResFinder'
		if os.path.exists(ResFinder_dir):
			self.copy_src_into_dest(ResFinder_dir, all_result_name)
		VirulenceFinder_dir=self.workdir+'VirulenceFinder'
		if os.path.exists(VirulenceFinder_dir):
			self.copy_src_into_dest(VirulenceFinder_dir, all_result_name)
		
		
		dtu_cge.make_tar_gzip(all_result_name,self.workdir)
		copyfile(src_tsv_file, tab_result_name)
		return all_result_name_gzip,tab_result_name
		

	
	
	def execute(self):

		command=self.command_builder()
		print 'COMMAND:',command
		self.run(command)
		gzip_file,tab_file=self.post_process()
		error_message='\n'.join(self.error_list) 
		return gzip_file,tab_file,error_message
		
	
		


class emc_slim:
	
	
	
	def __init__(self,fq1,fq2,emc_slim_property_file,workdir,sequencing_machine, pair,run_accession,emc_slim_program):
		self.fq1=fq1
		self.fq2=fq2
		#self.run_accession=run_accession
                self.emc_slim_program=emc_slim_program
		self.emc_slim_property_file=emc_slim_property_file
                self.run_accession=run_accession
		self.workdir=workdir
		self.sequencing_machine=sequencing_machine
		self.pair=pair
		error_list=list()
		self.error_list=error_list
		
		
	def command_builder(self):
		command=""
		if self.pair=='True':
			command="python %s -fq1 %s -fq2 %s -name %s -p %s -wkdir %s"%(self.emc_slim_program,self.fq1,self.fq2,self.run_accession,self.emc_slim_property_file,self.workdir)
                        #print "COMMAND:",command 
		else:
			message="ERROR:Currently cannot deal with non paired fastq files in dtu_sge object"
			#print "Currently cannot deal with non paired fastq files in dtu_sge object"
			self.error_list.append(message.replace("'",""))
		return command
		
		
	def run(self,command):
		print "running the command"
		print command
		sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		
		out, err = sp.communicate()
		if out:
			print "standard output of subprocess:"
			print out
			data=out.split('\n')
			i=0
			for line in data:
				if 'error' in line.lower(): 
					message=data[i-1]+'\n'+data[i]
					self.error_list.append(message.replace("'",""))
				i=i+1

        if err:
            print "standard error of subprocess:"
            print err
            data=err.split('\n')
            i=0
            for line in data:
                if 'error' in line.lower():
                    message=data[i-1]+'\n'+data[i]
                    self.error_list.append(message.replace("'",""))
                i=i+1
        if sp.returncode!=0:
            self.error_list.append(err.replace("'",""))
        print >> sys.stderr, err
	
	
	def post_process(self):
		gzip_file=self.workdir+self.run_accession+"_analysis_EMC_SLIM_all.tar.gz"
		tab_file=self.workdir+self.run_accession+"_analysis_EMC_SLIM_summary.tsv"
		if os.path.exists(gzip_file):
			if os.path.getsize(gzip_file)==0:
				message="ERROR: gzip file %s is empty"%gzip_file
				self.error_list.append(message.replace("'",""))
				print message
		else:
			message="ERROR: gzip file %s doesn't exist"%gzip_file
			self.error_list.append(message.replace("'",""))
			print message
		if os.path.exists(tab_file):
			if os.path.getsize(tab_file)==0:
				message="ERROR: gzip file %s is empty"%tab_file
				self.error_list.append(message.replace("'",""))
				print message
			
		else:
			message="ERROR: gzip file %s doesn't exist"%tab_file
			self.error_list.append(message.replace("'",""))
			print message
			
		return gzip_file,tab_file
			
		
		
	
	def execute(self):

		command=self.command_builder()
		print 'COMMAND:',command
		self.run(command)
		gzip_file,tab_file=self.post_process()
		error_message='\n'.join(self.error_list) 
		return gzip_file,tab_file,error_message
		
