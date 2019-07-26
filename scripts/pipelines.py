"""
Pipeline module.
"""
import os
import subprocess
import sys
import tarfile
import zipfile
import shutil
from shutil import copyfile
from bsub import bsub
sys.stdout.flush()

__author__ = 'Nima Pakseresht, Blaise Alako'

class DtuCge:
	'''
	docker run -ti --rm -v /analysis/cbs/databases:/databases -v \
	/analysis/nima/cge-workspace/workspace:/workdir \
	cgetools BAP --wdir /workdir --fq1 /workdir/ERR1698597_1.fastq.gz \
	 --fq2 /workdir/ERR1698597_2.fastq.gz --Asp Illumina --Ast paired
	'''

	def __init__(self, fq1, fq2, database_dir, workdir, sequencing_machine,
				 pair, run_accession, prop, instrument_model, sample_accession):
		"""
		Initialize object variables
		"""
		self.fq1 = fq1
		self.fq2 = fq2
		self.run_accession = run_accession
		self.sample_accession = sample_accession
		self.database_dir = database_dir
		self.workdir = workdir
		self.sequencing_machine = sequencing_machine
		self.pair = pair
		self.instrument_model = instrument_model
		self.lsf = prop.lsf
		self.cgetools = prop.cgetools
		self.rmem = prop.rmem
		self.lmem = prop.lmem
		self.bgroup = prop.bgroup

		error_list = list()
		self.error_list = error_list

	def command_builder_mock(self):
		"""
		Mock command builder for quick prototyping
		"""
		bap = "/usr/src/cgepipeline/cgetools/BAP.py"
		if self.pair == 'True':
			command = "mkdir -p {}  && du -hs /homes/blaise/bin \
			 &&  ".format(self.workdir, self.workdir)

			command = command + " cp -fv /homes/blaise/conda.list {}out.tsv ; mkdir -p {}{}; mkdir -p  {}{}; \
			mkdir -p {}{}; mkdir -p {}{}; mkdir -p {}{}; mkdir -p {}{}; mkdir -p {}{} ; mkdir -p {}{};  \
			cp -fv /homes/blaise/conda.list {}{}/results.txt ;".format(self.workdir, self.workdir, 'Assembler',
																	   self.workdir, 'ContigAnalyzer',
																	   self.workdir, 'KmerFinder',
																	   self.workdir, 'PlasmidFinder',
																	   self.workdir, 'ResFinder',
																	   self.workdir, 'VirulenceFinder',
																	   self.workdir, 'MLST',
																	   self.workdir, 'cgMLSTFinder',
																	   self.workdir, 'cgMLSTFinder')
		else:
			message = ""
			self.error_list.append(message.replace("'", ""))
			command = "singularity exec -B {}:/databases -B {}:/workdir {} {} \
			--wdir /workdir --fq1 /workdir/{} --Asp {} --Ast paired".format(self.database_dir,
																			self.workdir,
																			self.cgetools,
																			bap,
																			self.fq1,
																			self.sequencing_machine)
		return command

	def command_builder(self):
		"""
		Command builder for tool in question
		:return: a mock command for the purpose of quick testing
		"""
		command = ""
		bap = "/usr/src/cgepipeline/cgetools/BAP.py"
		if self.pair == 'True':
			""" Use singularity instead to run cgetools"""

			command = "singularity exec -B {}:/databases -B {}:/workdir {} {} \
			--wdir /workdir --fq1 /workdir/{} --fq2 /workdir/{} --Asp {} --Ast paired".format(self.database_dir,
																							  self.workdir,
																							  self.cgetools,
																							  bap,
																							  self.fq1,
																							  self.fq2,
																							  self.sequencing_machine)
		else:
			command = "singularity exec -B {}:/databases -B {}:/workdir {} {} \
			--wdir /workdir --fq1 /workdir/{} --Asp '{}' --Ast single".format(self.database_dir,
																			  self.workdir,
																			  self.cgetools,
																			  bap,
																			  self.fq1,
																			  self.sequencing_machine) # Make use of the instrument model define above
		return command

	def run(self, command):
		"""
		run the command constructed by the command builder method
		:param command: compare pipeline-tool name to call
		:return: job id if LSF used otherwise none
		"""
		print('*' * 100)
		print("running the command")
		print(self.cgetools)
		print(command)
		print('*' * 100)
		job_id = ''
		processing_id = self.workdir.split('/')[-2]
		if not self.lsf:
			print('*'*100)
			print("NO LSF MODE: \n Running Command: {}".format(command))
			print('*'* 100)
			sub_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			out, err = sub_process.communicate()
			print(out)
			print(err)
			if out:
				print('*' * 100)
				print("standard output of subprocess:")
				print(out.decode())
				print('*' * 100)
				data = out.decode().split('\n')
				i = 0
				for line in data:
					if 'error' in line.lower():
						message = data[i - 1] + '\n' + data[i]
						self.error_list.append(message.replace("'", ""))
					i = i + 1
			if err:
				print('*' * 100)
				print("standard error of subprocess:")
				print("ERROR MESSAGE: {} ".format(err))
				print(err.decode())
				print('*' * 100)

				data = err.decode().split('\n')
				i = 0
				for line in data:
					if 'error' in line.lower():
						message = data[i - 1] + '\n' + data[i]
						self.error_list.append(message.replace("'", ""))
					i = i + 1
			if sub_process.returncode != 0:
				self.error_list.append(err.decode().replace("'", ""))
			print(err, file=sys.stderr)
		elif self.lsf:
			print("LSF option is true... PAIRED_END{} , type_of:{} ".format(self.pair, type(self.pair)))
			print(command)
			if self.pair.lower() == 'true':
				job_id = bsub('core_executor_' + processing_id, R=self.rmem, M=self.lmem, g=self.bgroup, verbose=True)(command)
			else:
				print('*'*100)
				print("PAIRED-END:{}".format(self.pair))
				job_id = bsub('core_executor_' + processing_id, P='singularity', R=self.rmem, M=self.lmem, g=self.bgroup, verbose=True)(command)
		return [job_id]


	def copy_src_into_dest(self, src, dest):
		"""
		copy pipeline intermediate files into a destination directory for the
		purpose of archiving.
		:param src:  Source directory
		:param dest: Destination directory
		:return: None
		"""
		name = os.path.basename(src)
		dest_file = os.path.join(dest, name)
		print("Copying {} to {}".format(src, dest_file))
		try:
			shutil.copytree(src, dest_file)
		except shutil.Error as error:
			message = 'Directory not copied. Error: {}'.format(error)
			self.error_list.append(message.replace("'", ""))
			print(message)
		except OSError as error:
			message = 'Directory not copied. Error: {}'.format(error)
			self.error_list.append(message.replace("'", ""))
			print(message)

	@staticmethod
	def delete_empty_files(folder):
		"""
		Delete empty files from a directory
		:param folder: directory containing empty files
		:return: None
		"""
		print("Deleting Empty files in folder: {}".format(folder))
		for root, dirs, files in os.walk(folder):
			for file in files:
				fullname = os.path.join(root, file)

				if os.path.getsize(fullname) == 0:
					print('To be deleted files:\n', fullname)
					os.remove(fullname)

	@staticmethod
	def make_tar_gzip(src, des):
		"""
		Create and archive and compressed it
		:param src: directory to be archived
		:param des: name of the archive and compressed directory
		:return: None
		"""
		name = os.path.basename(src) + '.tar.gz'
		print("Archiving and compressing:{}".format(name))
		des = os.path.join(des, name)
		with tarfile.open(des, "w:gz") as tar:
			tar.add(src, arcname=os.path.basename(src))

	@staticmethod
	def zip_dir(src):
		"""
		Compress a directory with zip tool
		:param src: directory to compress
		:return:  None
		"""
		filename = os.path.basename(src) + '.zip'
		print("Ziping {}".format(filename))
		zfile = zipfile.ZipFile(filename, "w")
		for dirname, subdirs, files in os.walk(src):
			print(dirname, subdirs, files)
			zfile.write(dirname)
			for filename in files:
				zfile.write(os.path.join(dirname, filename))
		zfile.close()

	@staticmethod
	def del_file(filename):
		"""
		Delete a single file name
		:param filename: file name to delete
		:return:  None
		"""
		if os.path.exists(filename):
			print('*'*100)
			print('Deleting: {} exists and is been deleted....'.format(filename))
			shutil.rmtree(filename, ignore_errors=True)

		# def change_permission(filename):


	def post_process(self):
		"""
		Postprocess analysis result of a pipeline.
		We should account for multiplexing in fastqs. We should add the name of the sample in the final file summary and chuncks that will be
		submitted to the FTP server. This is from the the observation that the same samples from the same processed runs will have similar name
		however their checksum values is different.
		Examples:
		dcc_allison PRJEB2059 ERR023804 (12)--
		dcc_allison PRJEB2059 'ERR028305','ERR028650'
		:return: compressed archived folder of pipeline runs and summary file(s)
		"""

		print('*' * 100)
		print("Doing post process:.........")
		command = 'chmod -R a+rw {}'.format(self.workdir)
		print(command)
		print('*' * 100)
		sub_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		out, err = sub_process.communicate()
		if out:
			self.error_list.append(out.decode().split('\n'))
		if err:
			self.error_list.append(err.decode().split('\n'))

		DtuCge.delete_empty_files(self.workdir)
		# use process_id (new_run_process ) instead of run_id (self.run_accession) to account for problematic duplicate RUNS ids from different datahub
		new_run_process = self.workdir.split('/')[-2]
		all_result_name = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_DTU_CGE_all"

		DtuCge.del_file(all_result_name)
		all_result_name_gzip = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_DTU_CGE_all.tar.gz"
		DtuCge.del_file(all_result_name_gzip)
		tab_result_name = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_DTU_CGE_summary.tsv"
		DtuCge.del_file(tab_result_name)
		""" Handle the cgMLTSFinder resutl.txt tab file ..."""
		tab_result_name2 = self.workdir + new_run_process + "_" + self.sample_accession + "_cgMLSTFinder_analysis_DTU_CGE_results.tsv"
		DtuCge.del_file(tab_result_name2)

		src_tsv_file = self.workdir + 'out.tsv'
		cgmlstfinder_result = self.workdir + 'cgMLSTFinder/results.txt'
		src_tsv_file2 = ''
		if os.path.exists(cgmlstfinder_result):
			print('*'*100)
			print("cgMLSTFinder results:")
			print(cgmlstfinder_result)
			print('*'*100)
			src_tsv_file2 = cgmlstfinder_result

		if not os.path.exists(all_result_name):
			os.makedirs(all_result_name)
		assembler_dir = self.workdir + 'Assembler'
		if os.path.exists(assembler_dir):
			self.copy_src_into_dest(assembler_dir, all_result_name)
		contiganalyzer_dir = self.workdir + 'ContigAnalyzer'
		if os.path.exists(contiganalyzer_dir):
			self.copy_src_into_dest(contiganalyzer_dir, all_result_name)
		kmerfinder_dir = self.workdir + 'KmerFinder'
		if os.path.exists(kmerfinder_dir):
			self.copy_src_into_dest(kmerfinder_dir, all_result_name)
		plasmidfinder_dir = self.workdir + 'PlasmidFinder'
		if os.path.exists(plasmidfinder_dir):
			self.copy_src_into_dest(plasmidfinder_dir, all_result_name)
		resfinder_dir = self.workdir + 'ResFinder'
		if os.path.exists(resfinder_dir):
			self.copy_src_into_dest(resfinder_dir, all_result_name)
		virulencefinder_dir = self.workdir + 'VirulenceFinder'
		if os.path.exists(virulencefinder_dir):
			self.copy_src_into_dest(virulencefinder_dir, all_result_name)
		mlst_dir = self.workdir + 'MLST'
		if os.path.exists(mlst_dir):
			self.copy_src_into_dest(mlst_dir, all_result_name)
		cgmlstfinder_dir = self.workdir + 'cgMLSTFinder'
		if os.path.exists(cgmlstfinder_dir):
			self.copy_src_into_dest(cgmlstfinder_dir, all_result_name)
		salmonellatypefinder_dir = self.workdir + 'SalmonellaTypeFinder'
		if os.path.exists(salmonellatypefinder_dir):
			self.copy_src_into_dest(salmonellatypefinder_dir, all_result_name)

		try:
			DtuCge.make_tar_gzip(all_result_name, self.workdir)
			copyfile(src_tsv_file, tab_result_name)
			if os.path.exists(src_tsv_file2):
				copyfile(src_tsv_file2, tab_result_name2)
		except Exception:
			print('Could not make tar gzip archive, or copy src tsv to tab_result_name')
		print("Post-process finished for {}".format(all_result_name))
		tab_result_names = [tab_result_name]
		if os.path.exists(tab_result_name2):
			tab_result_names.append(tab_result_name2)
		else:
			tab_result_names.append('')
		return all_result_name_gzip, tab_result_names

	def execute(self):
		"""
		Execute pipeline calling on command_builder and run methods
		defined in the same class
		:return: jobs ids or None
		"""
		command = self.command_builder()
		#command = self.command_builder_mock()
		print('*'*100)
		print('DTU command:', command)
		print('*'*100)
		jobids = self.run(command)

		""" Making use of LSF """
		print('*'*100)
		print('DTU bjobs ids:{} '.format(jobids))
		print('*'*100)
		return jobids


class EmcSlim:
	"""
	This class handle the EMC_SLIM pipeline parameter, execution and postprocessing.
	"""
	def __init__(self, fq1, fq2, emc_slim_property_file, workdir, sequencing_machine, pair, run_accession,
				 emc_slim_program, prop, instrument_model, sample_accession):
		"""
		Initialise object attributes
		:param fq1: fastq forward reads
		:param fq2: fastq reverse reads
		:param emc_slim_property_file: EMC_SLIM configuration files
		:param workdir: EMC_SLIME working directory
		:param sequencing_machine: Sequencing machine platform
		:param pair: boolean (true or false)
		:param run_accession: ERR/SRR fastq identifier
		:param emc_slim_program: absolute path to EMC_SLIM pipeline program
		:param prop: SELECTA property file
		:param instrument_model: sequencing machine instrument model
		:param sample_accession: run biosample_id
		"""
		self.fq1 = fq1
		self.fq2 = fq2
		self.emc_slim_program = emc_slim_program
		self.emc_slim_property_file = emc_slim_property_file
		self.run_accession = run_accession
		self.sample_accession = sample_accession
		self.workdir = workdir
		self.sequencing_machine = sequencing_machine
		self.instrument_model = instrument_model
		self.pair = pair
		self.lsf = prop.lsf
		self.rmem = prop.rmem
		self.lmem = prop.lmem
		self.bgroup = prop.bgroup
		error_list = list()
		self.error_list = error_list
		print('.'*100)
		print(
			"slim.FASTQ1: {}\nslim.FASTQ2: {}\nslim.property_file: {}\nslim.workdir: {}\nslim.sequence_machine: {}\nslim.pair: {}\nslim.run_accession: {}\nslim.lsf: {} \nslim.program: {}\nslim.rmem: {} \nslim.lmem: {}".format(
				self.fq1,
				self.fq2,
				self.emc_slim_property_file,
				self.workdir,
				self.sequencing_machine,
				self.pair,
				self.run_accession,
				self.lsf,
				self.emc_slim_program,
				self.rmem,
				self.lmem
			))
		print('.' * 100)


	def command_builder_mock(self):
		"""
		Mock command builder for fast prototyping.
		:return:  mock command
		"""
		if self.pair == 'True':
			command = "mkdir -p {} ; ".format(self.workdir, self.workdir)
			command = command + "cp -fv /homes/blaise/conda.list {}{}_analysis_EMC_SLIM_summary.tsv  ; cp -fv /homes/blaise/conda.2cp.gz {}{}_analysis_EMC_SLIM_all.tar.gz ; cp -fv /homes/blaise/conda.list {}out.tsv ; mkdir -p {}{}; mkdir -p  {}{}; mkdir -p {}{}; mkdir -p {}{}; mkdir -p {}{}; mkdir -p {}{}; mkdir -p {}{}  ".format(
				self.workdir, self.run_accession,
				self.workdir, self.run_accession,
				self.workdir, self.workdir, 'Assembler',
				self.workdir, 'ContigAnalyzer',
				self.workdir, 'KmerFinder',
				self.workdir, 'PlasmidFinder',
				self.workdir, 'ResFinder',
				self.workdir, 'VirulenceFinder',
				self.workdir, 'MLST')

		else:
			message = "ERROR:Currently cannot deal with non paired fastq files in dtu_sge object"
			# print "Currently cannot deal with non paired fastq files in dtu_sge object"
			self.error_list.append(message.replace("'", ""))
		return command


	def command_builder(self):
		"""
		Command builder
		:return: command to run
		"""
		new_run_process = self.workdir.split('/')[-2]
		command = ""
		if self.pair == 'True':
			command = "python2 -s {} -fq1 {} -fq2 {} \
			 -name {} -p {} -wkdir {}".format(self.emc_slim_program,
											  self.fq1,
											  self.fq2,
											  new_run_process + "_" + self.sample_accession,
											  self.emc_slim_property_file,
											  self.workdir)
		else:
			command = "python2 -s {} -fq1 {} \
			-name {} -p {} -wkdir {}".format(self.emc_slim_program,
											 self.fq1,
											 new_run_process + "_" + self.sample_accession,
											 self.emc_slim_property_file,
											 self.workdir)
		return command

	def run(self, command):
		"""
		run the command constructed by the command builder method
		:param command: compare pipeline-tool name to call
		:return: job id if LSF used otherwise none
	   """
		print('*' * 100)
		print("IN RUN FUNCTION: running the command:", command)
		print("Requested memory: {}".format(self.rmem))
		print("Memory limits: {}".format(self.lmem))
		print('*' * 100)
		processing_id = self.workdir.split('/')[-2]
		job_id = ''
		if not self.lsf:
			sub_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = sub_process.communicate()

			if out:
				print('*'*100)
				print("standard output of subprocess:\n", out.decode())
				print('*'*100)
				data = out.decode().split('\n')
				i = 0
				for line in data:
					if 'error' in line.lower():
						message = data[i - 1] + '\n' + data[i]
						self.error_list.append(message.replace("'", ""))
					i = i + 1

			if err:
				print('*' * 100)
				print("standard error of subprocess:\n", err.decode())
				print('*' * 100)
				data = err.decode().split('\n')
				i = 0
				for line in data:
					if 'error' in line.lower():
						message = data[i - 1] + '\n' + data[i]
						self.error_list.append(message.replace("'", ""))
					i = i + 1
			#Comment this out after amending A above
			if sub_process.returncode != 0:
				if err:
					self.error_list.append(err.decode().replace("'", ""))
					print(err.decode(), file=sys.stderr)
		else:
			print("LSF option is set to true .....")
			print(command)
			job_id = bsub('core_executor_' + processing_id, R=self.rmem, M=self.lmem, g=self.bgroup, verbose=True)(command)
		return [job_id]

		#
	def post_process(self):
		"""
		Postprocess analysis result of a pipeline.
		We should account for multiplexing in fastqs. We should add the name of the sample in the final file summary and chuncks that will be
		submitted to the FTP server. This is from the the observation that the same samples from the same processed runs will have similar name
		however their checksum values is different.
		Examples:
		dcc_allison PRJEB2059 ERR023804 (12)--
		dcc_allison PRJEB2059 'ERR028305','ERR028650'
		:return: compressed archived folder of pipeline runs and summary file(s)
		"""
		new_run_process = self.workdir.split('/')[-2]
		gzip_file = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_EMC_SLIM_all.tar.gz"
		tab_file = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_EMC_SLIM_summary.tsv"
		if os.path.exists(gzip_file):
			if os.path.getsize(gzip_file) == 0:
				message = "ERROR: gzip file {} is empty".format(gzip_file)
				self.error_list.append(message.replace("'", ""))
				print(message)
		else:
			message = "ERROR: gzip file {} doesn't exist".format(gzip_file)
			self.error_list.append(message.replace("'", ""))
			print('*' * 100)
			print(message)
			print('*' * 100)
		if os.path.exists(tab_file):
			if os.path.getsize(tab_file) == 0:
				message = "ERROR: tab file {} is empty".format(tab_file)
				self.error_list.append(message.replace("'", ""))
				print(message)

		else:
			message = "ERROR: tab file {} doesn't exist".format(tab_file)
			self.error_list.append(message.replace("'", ""))
			print(message)
		tab_files = [tab_file, '']
		return gzip_file, tab_files

	def execute(self):
		"""
		Execute pipeline calling on command_builder and run methods
		defined in the same class
		:return: jobs ids or None
		"""

		command = self.command_builder()
		#command = self.command_builder_mock()
		print('COMMAND:', command)
		jobids = self.run(command)
		print(jobids)

		return jobids

class UAntwerpBacpipe:
	"""
	This class handle the UAntwerp_Bacpipe pipeline parameter, execution and postprocessing.
	"""
	def make_tar_gzip(self, src, des):
		"""
		Create and archive and compressed it
		:param src: directory to be archived
		:param des: name of the archive and compressed directory
		:return: None
		"""
		print('*'*100)
		print("SRC DIR:\n{}\nDestination:\n{}".format(src, src + '.tar.gz'))
		print('*'*100)
		name = os.path.basename(src) + '.tar.gz'
		print("Archiving and compressing:{}".format(name))
		des = os.path.join(des, name)
		with tarfile.open(des, "w:gz") as tar:
			tar.add(src, arcname=os.path.basename(src))

	def copy_src_into_dest(self, src, dest):
		"""
		copy pipeline intermediate files into a destination directory for the
		purpose of archiving.
		:param src:  Source directory
		:param dest: Destination directory
		:return: None
		"""
		name = os.path.basename(src)
		dest_file = os.path.join(dest, name)
		print("Copying {} to {}".format(src, dest_file))
		try:
			shutil.copytree(src, dest_file)
		except shutil.Error as error:
			message = 'Directory not copied. Error: {}'.format(error)
			self.error_list.append(message.replace("'", ""))
			print(message)
		except OSError as error:
			message = 'Directory not copied. Error: {}'.format(error)
			self.error_list.append(message.replace("'", ""))
			print(message)

	config = {
		'directories': {
			'reads': '',
			'output': ''
		},
		'trim_galore': {
			'deactivate': 'no',
			'reads_type': 'paired',
			'quality_threshold': 25
		},
		'spades': {
			'deactivate': 'no',
			'Mode': 'paired',
			'kmer': 77
		},
		'mlst_typing': {
			'deactivate': 'no',
			'organism': 'lsalivarius'
		},
		'plasmids_finder': {
			'deactivate': 'no',
			'plasmids_database': 'gram_positive',
			'identity_threshold': 95
		},
		'resfinder': {
			'deactivate': 'no',
			'identity_threshold': 95,
			'resistance_database': 'aminoglycoside,beta-lactamase,colistin,fosfomycin,fusidicacid,macrolide,nitroimidazole,oxazolidinone,phenicol,quinolone,rifampicin,sulphonamide,tetracycline,trimethoprim,glycopeptide',
			'min_length': 0.6
		},
		'cardSearch': {
			'deactivate': 'no'
		},
		'emmTyping': {
			'deactivate': 'no'
		},
		'virulencefinder': {
			'deactivate': 'no',
			'identity_threshold': 95,
			'virulence_database': 'virulence_ecoli'
		},
		'parSNP': {
			'deactivate': 'yes',
			'parSNP_reference': '',
			'parSNP_reference_fsa': ''
		},
		'VirDBSearch': {
			'deactivate': 'no'
		},
		'prokka': {
			'deactivate': 'no',
			'prokka_path': '/hps/nobackup/nucleotide/blaise/selecta/python/anaconda2/bin/prokka'
		},
		'Output': {
			'deactivate': 'no'
		},
		'Resfams': {
			'deactivate': 'no'
		},
		'bacpipe': {
			'bacpipe_path': '/hps/nobackup/nucleotide/blaise/selecta/tools/bacpipe'
		}
	}

	def __init__(self,  workdir, yamlconfig, prop, sample_accession, pair):
		"""

		:workdir
		:yamlconfig
		"""
		self.workdir = workdir
		self.yamlconfig = yamlconfig
		self.bacpipe = prop.uantwerp_bacpipe_program
		self.processor_ = prop.nproc
		self.lsf = prop.lsf
		if pair == 'True':
			self.pair = True
		else:
			self.pair = False
		self.sample_accession = sample_accession
		error_list = list()
		self.error_list = error_list
		# Added from here missing params
		self.rmem = prop.rmem
		self.lmem = prop.lmem
		self.bgroup = prop.bgroup

	def command_builder(self):
		"""
		pass
		:return: python ./Pipeline_blaise.py --config configure.yaml --os unix --processors 20
		"""
		command = "python2 {} --config {} --os unix --processors {}".format(self.bacpipe, self.yamlconfig, self.processor_ )
		return command

	def command_builder_mock(self):
		"""
		pass
		:return:
		"""
		""" /hps/nobackup/nucleotide/blaise/selecta/development_blaise/bacpipe_mock/*  """
		command = "cp -r /hps/nobackup/nucleotide/blaise/selecta/development_blaise/bacpipe_mock/* {}".format(self.workdir)
		print('*' * 100)
		print(command)
		print('*' * 100)
		return command

	def run(self, command):
		"""
		pass
		:return:
		"""
		processing_id = self.workdir.split('/')[-2]
		job_id = ''
		if not self.lsf:
			sub_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = sub_process.communicate()

			if out:
				print('*' * 100)
				print("standard output of subprocess:\n", out.decode())
				print('*' * 100)
				data = out.decode().split('\n')
				i = 0
				for line in data:
					if 'error' in line.lower():
						message = data[i - 1] + '\n' + data[i]
						self.error_list.append(message.replace("'", ""))
					i = i + 1

			if err:
				print('*' * 100)
				print("standard error of subprocess:\n", err.decode())
				print('*' * 100)
				data = err.decode().split('\n')
				i = 0
				for line in data:
					if 'error' in line.lower():
						message = data[i - 1] + '\n' + data[i]
						self.error_list.append(message.replace("'", ""))
					i = i + 1
			# Comment this out after amending A above
			if sub_process.returncode != 0:
				if err:
					self.error_list.append(err.decode().replace("'", ""))
					print(err.decode(), file=sys.stderr)
		else:
			print("LSF option is set to true .....")
			print(command)
			job_id = bsub('core_executor_' + processing_id, R=self.rmem, M=self.lmem, g=self.bgroup, verbose=True)(
				command)
		return [job_id]


	def post_process(self):
		"""
		pass
		:return:
		"""
		tab_result_names=[]
		print('*' * 100)
		print("Doing post process:.........")
		print("Workind directory:\n{}".format(self.workdir))
		command = 'chmod -R a+rw {}'.format(self.workdir)
		print(command)
		print('*' * 100)
		sub_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		out, err = sub_process.communicate()
		if out:
			self.error_list.append(out.decode().split('\n'))
		if err:
			self.error_list.append(err.decode().split('\n'))
		new_run_process = self.workdir.split('/')[-2]
		all_result_name = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_UAntwerp_Bacpipe_all"
		all_result_name_gzip = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_UAntwerp_Bacpipe_all.tar.gz"
		tab_result_name = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_UAntwerp_Bacpipe_summary.xlsx"

		xls_basename = self.workdir.split('/')[-2].split('-')[-2]
		xls_basename = xls_basename + '_1' if self.pair else xls_basename

		src_tsv_file = self.workdir + 'Summary/' + xls_basename + '.xlsx'
		virulencefinder_result =  self.workdir + 'virulencefinder_output.txt'
		resfinder_result = self.workdir + 'resfinder_output.txt'
		resfams_result = self.workdir + 'resfams_output.txt'
		plasmids_finder_result = self.workdir + 'plasmids_finder_output.txt'
		mlst_result = self.workdir + 'mlst_output.txt'
		emm_result = self.workdir + 'emm_output.txt'
		cardsearch_result = self.workdir + 'cardSearch_output.txt'
		virdbsearch_result = self.workdir + 'VirDBSearch_output.txt'
		print('*' * 100)
		print("xls_basename:{}\nxls_file:{}\nvirulencefinder_result:{}\nresfinder_result:{}\n"
			  "resfams_result:{}\nplasmids_finder_result:{}\nmlst_result:{}\nemm_result:{}\n"
			  "cardsearch_result:{}\ncardsearch_result:{}\nvirdbsearch_result:{}\n".format(xls_basename,
																						   src_tsv_file,
																						   virulencefinder_result,
																						   resfinder_result,
																						   resfams_result,
																						   plasmids_finder_result,
																						   mlst_result,
																						   emm_result,
																						   cardsearch_result,
																						   cardsearch_result,
																						   virdbsearch_result))
		print('*' * 100)


		try:
			if not os.path.exists(all_result_name):
				os.makedirs(all_result_name)
			bacpipe_process_dir = self.workdir + xls_basename
			genome_assemblies = self.workdir + 'genome_assemblies'
			bacpipe_summary_dir = self.workdir + 'Summary'

			print('*'*100)
			print("Bacpipe process_dir:\n{}".format(bacpipe_process_dir))
			print("All result name:\n{}".format(all_result_name))
			print("All result name zip:\n{}".format(all_result_name_gzip))
			print("Genome assemblies folder:\n{}".format(genome_assemblies))
			print("bacpipe_summary_dir folder:\n{}".format(bacpipe_summary_dir))
			print("src_tsv_file folder:\n{}".format(src_tsv_file))
			print("virulencefinder_result folder:\n{}".format(virulencefinder_result))
			print("resfinder_result folder:\n{}".format(resfinder_result))
			print("resfams_result folder:\n{}".format(resfams_result))
			print("plasmids_finder_result folder:\n{}".format(plasmids_finder_result))
			print("mlst_result folder:\n{}".format(mlst_result))
			print("emm_result folder:\n{}".format(emm_result))
			print("cardsearch_result folder:\n{}".format(cardsearch_result))
			print("virdbsearch_result folder:\n{}".format(virdbsearch_result))
			print("tab_result_name folder:\n{}".format(tab_result_name))
			print('*'*100)

			if os.path.exists(bacpipe_process_dir):
				print("Copying {} {}".format(bacpipe_process_dir, all_result_name))
				self.copy_src_into_dest(bacpipe_process_dir, all_result_name)
			if os.path.exists(genome_assemblies):
				self.copy_src_into_dest(genome_assemblies, all_result_name)
			if os.path.exists(bacpipe_summary_dir):
				print("Copying {} {}".format(bacpipe_summary_dir, all_result_name))
				self.copy_src_into_dest(bacpipe_summary_dir, all_result_name)
			if os.path.exists(src_tsv_file):
				#shutil.copy(source, target)
				shutil.copy(src_tsv_file, all_result_name)
			if os.path.exists(virulencefinder_result):
				shutil.copy(virulencefinder_result, all_result_name)
			if os.path.exists(resfinder_result):
				shutil.copy(resfinder_result, all_result_name)
			if os.path.exists(resfams_result):
				shutil.copy(resfams_result, all_result_name)
			if os.path.exists(plasmids_finder_result):
				shutil.copy(plasmids_finder_result, all_result_name)
			if os.path.exists(mlst_result):
				shutil.copy(mlst_result, all_result_name)
			if os.path.exists(emm_result):
				shutil.copy(emm_result, all_result_name)
			if os.path.exists(cardsearch_result):
				shutil.copy(cardsearch_result, all_result_name)
			if os.path.exists(virdbsearch_result):
				shutil.copy(virdbsearch_result, all_result_name)
			if os.path.exists(src_tsv_file):
				shutil.copy(src_tsv_file, tab_result_name)
				shutil.copy(tab_result_name, all_result_name)

			self.make_tar_gzip(all_result_name, self.workdir)
			print('-'*100)
			print("Copying {} <---> {}".format(src_tsv_file, tab_result_name))
			print("GZIP  {} in {}".format(all_result_name, self.workdir))
			print('-'*100)
		except Exception as e:
			print(e)
			print('Could not make tar gzip archive, or copy src tsv to tab_result_name')
		finally:
			tab_result_names = [tab_result_name]
			tab_result_names.append('')
		return all_result_name_gzip, tab_result_names



	def execute(self):
		"""
		pass
		:return:
		"""
		command = self.command_builder()
		#command = self.command_builder_mock()
		print('*' * 100)
		print('Bacpipe  command:', command)
		print('*' * 100)
		jobids = self.run(command)

		""" Making use of LSF """
		print('*' * 100)
		print('Bacpipe bjobs ids:{} '.format(jobids))
		print('*' * 100)
		return jobids



class RivmJovian:
	"""
	To document...
	"""
	def __init__(self, fq1, fq2, workdir,
				 pair, run_accession, prop, sample_accession):
		"""
		pass
		:param fastq1:
		:param fastq2:
		Initialize object variables
		"""
		self.fq1 = fq1
		self.fq2 = fq2
		self.run_accession = run_accession
		self.sample_accession = sample_accession
		self.workdir = workdir
		self.pair = pair
		self.prop = prop
		self.lsf = prop.lsf
		self.rivm_jovian_base = prop.rivm_jovian_base
		self.rmem = prop.rmem
		self.lmem = prop.lmem
		self.bgroup = prop.bgroup
		self.jovian_profile = prop.rivm_jovian_profile
		self.jovian_location = prop.rivm_jovian_base
		error_list = list()
		self.error_list = error_list

	def copy_src_into_dest(self, src, dest):
		"""
		copy pipeline intermediate files into a destination directory for the
		purpose of archiving.
		:param src:  Source directory
		:param dest: Destination directory
		:return: None
		"""
		name = os.path.basename(src)
		dest_file = os.path.join(dest, name)
		print("Copying {} to {}".format(src, dest_file))
		try:
			shutil.copytree(src, dest_file)
		except shutil.Error as error:
			message = 'Directory not copied. Error: {}'.format(error)
			self.error_list.append(message.replace("'", ""))
			print(message)
		except OSError as error:
			message = 'Directory not copied. Error: {}'.format(error)
			self.error_list.append(message.replace("'", ""))
			print(message)


	def jovian_init(self):
		"""
		:return: a directory with:
		1 - bin folder copied therein
		2- A simling to profile, envs, snakefile
		3- Creation of fastq directory where fastqs file are moved
		"""
		copy_profile= "cp -rv {}/profile {}".format(self.jovian_location, self.workdir)
		copy_jovian = "cp -v {}/jovian {}".format(self.jovian_location, self.workdir)
		copy_envs = "cp -rv {}/envs {}".format(self.jovian_location, self.workdir)
		copy_snakefile = "cp -v {}/Snakefile {}".format(self.jovian_location, self.workdir)
		copy_files = "cp -rv {}/files {}".format(self.jovian_location, self.workdir)
		copy_bin = "cp -rv {}/bin {}".format(self.jovian_location, self.workdir)
		copy_call = "cp -v {}/jovian_bash.sh {}".format(self.jovian_location, self.workdir)
		copy_git = "cp -rv {}/.git {}".format(self.jovian_location, self.workdir)
		command = copy_profile + " && " + \
		          copy_jovian + " && " + \
		          copy_envs + " && " + \
		          copy_snakefile + " && " + \
		          copy_files + " && " + \
		          copy_bin + " && " + \
		          copy_call + " && " + \
		          copy_git
		fastq_dir = self.workdir + "fastqs"
		if not os.path.exists(fastq_dir):
			os.makedirs(fastq_dir)
		if os.path.exists(self.workdir + self.fq1):
			shutil.move(self.workdir + self.fq1, fastq_dir + '/' + self.fq1)
		if os.path.exists(self.workdir + self.fq2):
			shutil.move(self.workdir + self.fq2, fastq_dir + '/' + self.fq2)
		try:
			sub_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = sub_process.communicate()
		except:
			pass

	def command_builder(self):
		"""
		pass
		:return:
		change into process_id dir prior jovian run
		"""
		command = "cd {} && ./jovian_bash.sh ".format(self.workdir)
		return command

	def command_builder_mock(self):
		"""
		pass
		:return:
		"""
		copy_result = "cp -rv /hps/nobackup/nucleotide/blaise/selecta/tools/jovian/mock_run/{} {}".format('results', self.workdir) # ,'data','logs','files',
		copy_data = "cp -rv /hps/nobackup/nucleotide/blaise/selecta/tools/jovian/mock_run/{} {}".format('data', self.workdir)
		copy_logs = "cp -rv /hps/nobackup/nucleotide/blaise/selecta/tools/jovian/mock_run/{} {}".format('logs', self.workdir)
		command = copy_result + " && " + copy_data + " && " + copy_logs
		print('*' * 100)
		print(command)
		print('*' * 100)
		copy_profile = "{}/profile".format(self.workdir)
		link_jovian = "{}/jovian".format(self.workdir)
		link_envs = "{}/envs".format(self.workdir)
		link_snakefile = "{}/Snakefile".format(self.workdir)
		link_files = "{}/files".format(self.workdir)
		copy_bin = "{}/bin".format(self.workdir)
		copy_call = "{}/jovian_bash.sh".format(self.workdir)
		link_git = "{}/.git".format(self.workdir)

		if not (os.path.exists(copy_profile)  and os.path.exists(link_jovian)  \
		        and os.path.exists(link_envs) and os.path.exists(link_snakefile) \
		        and os.path.exists(link_files) and os.path.exists(copy_bin) \
				and os.path.exists(copy_call) and os.path.exists(link_git)) :
			self.jovian_init()

		return command


	def post_process(self):
		print('*' * 100)
		print("\nProcessing in {}:.........".format(self.workdir))
		command = 'chmod -R a+rw {}'.format(self.workdir)
		print(command)
		print('*' * 100)
		sub_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		out, err = sub_process.communicate()
		if out:
			self.error_list.append(out.decode().split('\n'))
		if err:
			self.error_list.append(err.decode().split('\n'))

		DtuCge.delete_empty_files(self.workdir)
		# use process_id (new_run_process ) instead of run_id (self.run_accession) to account for problematic duplicate RUNS ids from different datahub
		new_run_process = self.workdir.split('/')[-2]
		all_result_name = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_Rivm_Jovian_all"
		DtuCge.del_file(all_result_name)
		all_result_name_gzip = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_Rivm_Jovian_all.tar.gz"
		DtuCge.del_file(all_result_name_gzip)
		""" Summary files
		all_virusHost.tsv
		all_taxClassified.tsv
		all_taxUnclassified.tsv
		all_filtered_SNPs.tsv
		"""
		tab_result_name = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_Rivm_Jovian_virusHost.tsv"
		tab_result_name2 = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_Rivm_Jovian_taxClassified.tsv"
		tab_result_name3 = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_Rivm_Jovian_taxUnclassified.tsv"
		tab_result_name4 = self.workdir + new_run_process + "_" + self.sample_accession + "_analysis_Rivm_Jovian_filteredSNPs.tsv"
		DtuCge.del_file(tab_result_name)
		DtuCge.del_file(tab_result_name2)
		DtuCge.del_file(tab_result_name3)
		DtuCge.del_file(tab_result_name4)

		all_virusHost,all_taxClassified,all_taxUnclassified,all_filtered_SNPs ='','','',''
		if os.path.exists(self.workdir + 'results/all_virusHost.tsv'):
			all_virusHost = self.workdir + 'results/all_virusHost.tsv'
		if os.path.exists(self.workdir + 'results/all_taxClassified.tsv'):
			all_taxClassified = self.workdir + 'results/all_taxClassified.tsv'
		if os.path.exists(self.workdir + 'results/all_taxUnclassified.tsv'):
			all_taxUnclassified = self.workdir + 'results/all_taxUnclassified.tsv'
		if os.path.exists(self.workdir + 'results/all_filtered_SNPs.tsv'):
			all_filtered_SNPs = self.workdir + 'results/all_filtered_SNPs.tsv'
		if not os.path.exists(all_result_name):
			os.makedirs(all_result_name)
		results_dir = self.workdir + 'results'

		if os.path.exists(results_dir):
			self.copy_src_into_dest(results_dir, all_result_name)
		data_dir = self.workdir + 'data'
		if os.path.exists(data_dir):
			self.copy_src_into_dest(data_dir, all_result_name)
		logs_dir = self.workdir + 'logs'
		if os.path.exists(logs_dir):
			self.copy_src_into_dest(logs_dir, all_result_name)

		try:
			"""Archive Jovian analysis"""
			DtuCge.make_tar_gzip(all_result_name, self.workdir)
			if os.path.exists(all_virusHost):
				copyfile(all_virusHost, tab_result_name)
			if os.path.exists(all_taxClassified):
				copyfile(all_taxClassified, tab_result_name2)
			if os.path.exists(all_taxUnclassified):
				copyfile(all_taxUnclassified, tab_result_name3)
			if os.path.exists(all_filtered_SNPs):
				copyfile(all_filtered_SNPs, tab_result_name4)
		except Exception:
			print('Could not make tar gzip archive, or copy src tsv to tab_result_name')
		print("Post-process finished for {}".format(all_result_name))
		tab_result_names = []
		if os.path.exists(tab_result_name):
			tab_result_names.append(tab_result_name)
		if os.path.exists(tab_result_name2):
			tab_result_names.append(tab_result_name2)
		if os.path.exists(tab_result_name3):
			tab_result_names.append(tab_result_name3)
		if os.path.exists(tab_result_name4):
			tab_result_names.append(tab_result_name4)
		else:
			tab_result_names.append('')
		return all_result_name_gzip, tab_result_names

	def run(self, command):
		"""
		pass
		:return:
		"""
		processing_id = self.workdir.split('/')[-2]
		job_id = ''

		if not self.lsf:
			sub_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = sub_process.communicate()

			if out:
				print('*' * 100)
				print("standard output of subprocess:\n", out.decode())
				print('*' * 100)
				data = out.decode().split('\n')
				i = 0
				for line in data:
					if 'error' in line.lower():
						message = data[i - 1] + '\n' + data[i]
						self.error_list.append(message.replace("'", ""))
					i = i + 1

			if err:
				print('*' * 100)
				print("standard error of subprocess:\n", err.decode())
				print('*' * 100)
				data = err.decode().split('\n')
				i = 0
				for line in data:
					if 'error' in line.lower():
						message = data[i - 1] + '\n' + data[i]
						self.error_list.append(message.replace("'", ""))
					i = i + 1
			# Comment this out after amending A above
			if sub_process.returncode != 0:
				if err:
					self.error_list.append(err.decode().replace("'", ""))
					print(err.decode(), file=sys.stderr)
		else:
			print("LSF option is set to true .....")
			print(command)
			job_id = bsub('core_executor_' + processing_id, R=self.rmem, M=self.lmem, g=self.bgroup, verbose=True)(
				command)
		return [job_id]


	def execute(self):
		"""
		pass
		:return:
		"""
		command = self.command_builder()
		#command = self.command_builder_mock()

		self.jovian_init()


		""" Make sure we are in the processing directory b4 jovian run """
		jobids = self.run(command)
		print('*' * 100)
		print('Jovian bjobs ids:{} '.format(jobids))
		print('Jovian  command:', command)
		print('*' * 100)
		return jobids


class FliRiems:
	"""
	To document ...
	"""

	def __init__(self, fastq1, fastq2):
		"""
		Pass
		:param fastq1:
		:param fastq2:
		"""
		self.fastq1 = fastq1
		self.fastq2 = fastq2


	def command_builder(self):
		"""
		Pass
		:return:
		"""
		pass

	def command_builder_mock(self):
		"""
		Pass
		:return:
		"""
		pass

	def run(self):
		"""
		Pass
		:return:
		"""
		pass

	def post_process(self):
		"""
		Pass
		:return:
		"""
		pass

	def run(self):
		"""
		Pass
		:return:
		"""
		pass
