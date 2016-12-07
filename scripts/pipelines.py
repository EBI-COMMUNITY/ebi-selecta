import os
import subprocess
from Finder.Containers_and_folders import folder
import os
from glob import glob
import tarfile
import zipfile
from shutil import copyfile
import shutil
from CodeWarrior.Standard_Suite import files




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
	
	def __init__(self,fq1,fq2,database_dir,workdir,sequencing_machine, pair,run_accession):
		self.fq1=fq1
		self.fq2=fq2
		self.run_accession=run_accession
		self.database_dir=database_dir
		self.workdir=workdir
		self.sequencing_machine=sequencing_machine
		self.pair=pair
		
		
	def command_builder(self):
		#docker run -ti --rm -v /Users/nimap/Google-Drive/workspace/ebi-selecta/databases/dtu-databases:/databases -v /Users/nimap/Google-Drive/workspace/ebi-selecta/process/ERR1597716-01122016100820:/workdir cgetools BAP --wdir /workdir --fq1 /workdir/ERR029449_1.fastq.gz --fq2 /workdir/ERR029449_2.fastq.gz --Asp Illumina --Ast paired
		command=""
		if self.pair=='True':
			#docker run -ti --rm -v %s:/databases -v %s:/workdir cgetools BAP --wdir /workdir --fq1 /workdir/%s --fq2 /workdir/%s --Asp %s --Ast paired
			command="docker run -ti --rm -v %s:/databases -v %s:/workdir cgetools BAP --wdir /workdir --fq1 /workdir/%s --fq2 /workdir/%s --Asp %s --Ast paired"%(self.database_dir,self.workdir,self.fq1,self.fq2,self.sequencing_machine)
		else:
			print "Currently cannot deal with non paired fastq files in dtu_sge object"
		return command
		
	def run(self,command):
		print "running the command"
		#os.system(command)
		p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		#print "stderr:",p.stderr.readlines()
		#print "stdout:",p.stdout.readlines()
		
		for line in p.stdout.readlines():
			print line
			
	#def delete_empty_files(self,folder):
	'''
	def copytree(src, dst, symlinks=False, ignore=None):
	if not os.path.exists(dst):
		os.makedirs(dst)
	for item in os.listdir(src):
		s = os.path.join(src, item)
		d = os.path.join(dst, item)
		if os.path.isdir(s):
			copytree(s, d, symlinks, ignore)
		else:
			if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
				shutil.copy2(s, d)
	'''
	@staticmethod	
	def copy_src_into_dest(src, dest):
		#for src in files:
			name=os.path.basename(src)
			dest_file=os.path.join(dest, name)
			try:
				shutil.copytree(src, dest_file)
			# Directories are the same
			except shutil.Error as e:
				print('Directory not copied. Error: %s' % e)
			# Any error saying that the directory doesn't exist
			except OSError as e:
				print('Directory not copied. Error: %s' % e)
			
	@staticmethod	
	def delete_empty_files(folder):
		for root, dirs, files in os.walk(folder):
			for file in files:
				fullname = os.path.join(root, file)
				#print fullname
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
		
	
	def post_process(self):
		print "doing post process:"
		dtu_cge.delete_empty_files(self.workdir)
		all_result_name=self.workdir+self.run_accession+"_analysis_DTU_CGE_all"
		all_result_name_gzip=self.workdir+self.run_accession+"_analysis_DTU_CGE_all.tar.gz"
		tab_result_name=self.workdir+self.run_accession+"_analysis_DTU_CGE_summarry.tsv"
		src_tsv_file=self.workdir+'out.tsv'
		print all_result_name
		print tab_result_name
		if not os.path.exists(all_result_name):
			os.makedirs(all_result_name)
		
		Assembler_dir=self.workdir+'Assembler'
		dtu_cge.copy_src_into_dest(Assembler_dir, all_result_name)
		ContigAnalyzer_dir=self.workdir+'ContigAnalyzer'
		dtu_cge.copy_src_into_dest(ContigAnalyzer_dir, all_result_name)
		KmerFinder_dir=self.workdir+'KmerFinder'
		dtu_cge.copy_src_into_dest(KmerFinder_dir, all_result_name)
		PlasmidFinder_dir=self.workdir+'PlasmidFinder'
		dtu_cge.copy_src_into_dest(PlasmidFinder_dir, all_result_name)
		ResFinder_dir=self.workdir+'ResFinder'
		dtu_cge.copy_src_into_dest(ResFinder_dir, all_result_name)
		VirulenceFinder_dir=self.workdir+'VirulenceFinder'
		dtu_cge.copy_src_into_dest(VirulenceFinder_dir, all_result_name)
		
		
		dtu_cge.make_tar_gzip(all_result_name,self.workdir)
		copyfile(src_tsv_file, tab_result_name)
		return all_result_name_gzip,tab_result_name
		

	
	
	def execute(self):
		command=self.command_builder()
		#self.run(command)
		gzip_file,tab_file=self.post_process()
		return gzip_file,tab_file
		
	
		
		
		
		