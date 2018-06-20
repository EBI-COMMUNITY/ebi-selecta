import os
import subprocess
import sys
from glob import glob
import tarfile
import zipfile
from shutil import copyfile
import shutil
sys.stdout.flush()
#from farmpy import *
from bsub import bsub
import re

__author__ = 'Nima Pakseresht, Blaise Alako'

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

    def __init__(self, fq1, fq2, database_dir, workdir, sequencing_machine, pair, run_accession,prop, instrument_model, sample_accession):
        self.fq1 = fq1
        self.fq2 = fq2
        self.run_accession = run_accession
        self.sample_accession = sample_accession
        self.database_dir = database_dir
        self.workdir = workdir
        self.sequencing_machine = sequencing_machine
        self.pair = pair
        self.instrument_model=instrument_model
        self.lsf = prop.lsf
        self.cgetools = prop.cgetools
        self.rmem = prop.rmem
        self.lmem = prop.lmem
        self.bgroup = prop.bgroup

        error_list = list()
        self.error_list = error_list

    def command_builder_mock(self):
        if self.pair == 'True':
            command = "mkdir -p {}  && du -hs /hps/nobackup/nucleotide/blaise/selecta/development/process/SRR1002804-19042018120902 &&  ".format(self.workdir, self.workdir)

            command = command + " cp -fv /homes/blaise/conda.list {}out.tsv ; mkdir -p {}{}; mkdir -p  {}{}; mkdir -p {}{}; mkdir -p {}{}; mkdir -p {}{}; mkdir -p {}{}; mkdir -p {}{}  ".format( self.workdir, self.workdir, 'Assembler',
                                                                               self.workdir, 'ContigAnalyzer',
                                                                               self.workdir, 'KmerFinder',
                                                                               self.workdir,'PlasmidFinder',
                                                                               self.workdir, 'ResFinder',
                                                                               self.workdir,'VirulenceFinder',
                                                                               self.workdir,'MLST')

        else:
            message = ""
            self.error_list.append(message.replace("'", ""))
            command = "singularity exec -B {}:/databases -B {}:/workdir {} {} --wdir /workdir --fq1 /workdir/{} --Asp {} --Ast paired".format(
                self.database_dir, self.workdir, self.cgetools, BAP, self.fq1, self.sequencing_machine)
        return command


    def command_builder(self):
        command = ""
        BAP = "/usr/src/cgepipeline/cgetools/BAP.py"
        if self.pair == 'True':
            """ Use singularity instead to run cgetools"""

            command = "singularity exec -B {}:/databases -B {}:/workdir {} {} --wdir /workdir --fq1 /workdir/{} --fq2 /workdir/{} --Asp {} --Ast paired".format(self.database_dir, self.workdir, self.cgetools, BAP, self.fq1, self.fq2, self.sequencing_machine)
        else:
            command = "singularity exec -B {}:/databases -B {}:/workdir {} {} --wdir /workdir --fq1 /workdir/{} --Asp '{}' --Ast single".format(self.database_dir, self.workdir, self.cgetools, BAP, self.fq1, self.sequencing_machine) # Make use of the instrument model define above
        return command

    def run(self, command):
        print('*' * 100)
        print("running the command")
        print(self.cgetools)
        print(command)
        print('*' * 100)
        job_id=''
        processing_id = self.workdir.split('/')[-2]
        if not self.lsf:
            print('*'*100)
            print("NO LSF MODE: \n Running Command: {}".format(command))
            print('*'* 100)
            sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = sp.communicate()
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
            if sp.returncode != 0:
                self.error_list.append(err.decode().replace("'", ""))
            print(err, file=sys.stderr)
        elif self.lsf:
            print("LSF option is true... ")
            print(command)
            job_id = bsub('core_executor_' + processing_id, R=self.rmem, M=self.lmem, g=self.bgroup, verbose=True)(command)
        return [job_id]


    # @staticmethod
    def copy_src_into_dest(self, src, dest):
        name = os.path.basename(src)
        dest_file = os.path.join(dest, name)
        print("Copying {} to {}".format(src, dest_file))
        try:
            shutil.copytree(src, dest_file)
        except shutil.Error as e:
            message = 'Directory not copied. Error: {}'.format(e)
            self.error_list.append(message.replace("'", ""))
            print(message)
        except OSError as e:
            message = 'Directory not copied. Error: {}'.format(e)
            self.error_list.append(message.replace("'", ""))
            print(message)

    @staticmethod
    def delete_empty_files(folder):
        print("Deleting folder: {}".format(folder))
        for root, dirs, files in os.walk(folder):
            for file in files:
                fullname = os.path.join(root, file)

                if os.path.getsize(fullname) == 0:
                    print('To be deleted files:\n', fullname)
                    os.remove(fullname)

    @staticmethod
    def make_tar_gzip(src, des):
        name = os.path.basename(src) + '.tar.gz'
        print("Archiving and compressing:{}".format(name))
        des = os.path.join(des, name)
        with tarfile.open(des, "w:gz") as tar:
            tar.add(src, arcname=os.path.basename(src))

    @staticmethod
    def zip_dir(src):
        filename = os.path.basename(src) + '.zip'
        print("Ziping {}".format(filename))
        zf = zipfile.ZipFile(filename, "w")
        for dirname, subdirs, files in os.walk(src):
            print(dirname, subdirs, files)
            zf.write(dirname)
            for filename in files:
                zf.write(os.path.join(dirname, filename))
        zf.close()

    @staticmethod
    def del_file(filename):
        if os.path.exists(filename):
            print('*'*100)
            print('Deleting: {} exist and is been deleted....'.format(filename))
            shutil.rmtree(filename, ignore_errors=True)

        # def change_permission(filename):


    def post_process(self):
        '''
        We should account for multiplexing in fastqs. We should add the name of the sample in the final file summary and chuncks that will be
        submitted to the FTP server. This is from the the observation that the same samples from the same processed runs will have similar name
        however their checksum values is different.
        Examples:
            dcc_allison PRJEB2059 ERR023804 (12)--
            dcc_allison PRJEB2059 'ERR028305','ERR028650'
        '''
        print('*' * 100)
        print("Doing post process:.........")
        command = 'chmod -R a+rw {}'.format(self.workdir)
        print(command)
        print('*' * 100)
        sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = sp.communicate()
        if out:
            self.error_list.append(out.decode().split('\n'))
        if err:
            self.error_list.append(err.decode().split('\n'))

        dtu_cge.delete_empty_files(self.workdir)

        all_result_name = self.workdir + self.run_accession + "_" + self.sample_accession + "_analysis_DTU_CGE_all"

        dtu_cge.del_file(all_result_name)
        all_result_name_gzip = self.workdir + self.run_accession + "_" + self.sample_accession + "_analysis_DTU_CGE_all.tar.gz"
        dtu_cge.del_file(all_result_name_gzip)
        tab_result_name = self.workdir + self.run_accession + "_" + self.sample_accession + "_analysis_DTU_CGE_summary.tsv"
        dtu_cge.del_file(tab_result_name)
        src_tsv_file = self.workdir + 'out.tsv'
        if not os.path.exists(all_result_name):
            os.makedirs(all_result_name)
        Assembler_dir = self.workdir + 'Assembler'
        if os.path.exists(Assembler_dir):
            self.copy_src_into_dest(Assembler_dir, all_result_name)
        ContigAnalyzer_dir = self.workdir + 'ContigAnalyzer'
        if os.path.exists(ContigAnalyzer_dir):
            self.copy_src_into_dest(ContigAnalyzer_dir, all_result_name)
        KmerFinder_dir = self.workdir + 'KmerFinder'
        if os.path.exists(KmerFinder_dir):
            self.copy_src_into_dest(KmerFinder_dir, all_result_name)
        PlasmidFinder_dir = self.workdir + 'PlasmidFinder'
        if os.path.exists(PlasmidFinder_dir):
            self.copy_src_into_dest(PlasmidFinder_dir, all_result_name)
        ResFinder_dir = self.workdir + 'ResFinder'
        if os.path.exists(ResFinder_dir):
            self.copy_src_into_dest(ResFinder_dir, all_result_name)
        VirulenceFinder_dir = self.workdir + 'VirulenceFinder'
        if os.path.exists(VirulenceFinder_dir):
            self.copy_src_into_dest(VirulenceFinder_dir, all_result_name)
        MLST_dir = self.workdir + 'MLST'
        if os.path.exists(MLST_dir):
            self.copy_src_into_dest(MLST_dir, all_result_name)

        cgMLSTFinder_dir = self.workdir + 'cgMLSTFinder'
        if os.path.exists(cgMLSTFinder_dir):
            self.copy_src_into_dest(cgMLSTFinder_dir, all_result_name)
        SalmonellaTypeFinder_dir = self.workdir + 'SalmonellaTypeFinder'
        if os.path.exists(SalmonellaTypeFinder_dir):
            self.copy_src_into_dest(SalmonellaTypeFinder_dir, all_result_name)

        try:
            dtu_cge.make_tar_gzip(all_result_name, self.workdir)
            copyfile(src_tsv_file, tab_result_name)
        except Exception:
            print('Could not make tar gzip archive, or copy src tsv to tab_result_name')
        print("Post-process finished for {}".format(all_result_name))
        return all_result_name_gzip, tab_result_name

    def execute(self):
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


class emc_slim:
    def __init__(self, fq1, fq2, emc_slim_property_file, workdir, sequencing_machine, pair, run_accession,
                 emc_slim_program, prop, instrument_model, sample_accession):
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
        command = ""
        if self.pair == 'True':
            command = "python2 -s {} -fq1 {} -fq2 {} -name {} -p {} -wkdir {}".format(self.emc_slim_program,
                                                                                  self.fq1,
                                                                                  self.fq2,
                                                                                  self.run_accession,
                                                                                  self.emc_slim_property_file,
                                                                                  self.workdir)

        else:
            command = "python2 -s {} -fq1 {} -name {} -p {} -wkdir {}".format(self.emc_slim_program,
                                                                          self.fq1,
                                                                          self.run_accession,
                                                                          self.emc_slim_property_file,
                                                                          self.workdir)


        return command

    def run(self, command):
        print('*' * 100)
        print("IN RUN FUNCTION: running the command:", command)
        print("Requested memory: {}".format(self.rmem))
        print("Memory limits: {}".format(self.lmem))
        print('*' * 100)
        processing_id = self.workdir.split('/')[-2]
        job_id=''
        if not self.lsf:
            sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = sp.communicate()

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
            if sp.returncode != 0:
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
        gzip_file = self.workdir + self.run_accession + "_analysis_EMC_SLIM_all.tar.gz"
        tab_file = self.workdir + self.run_accession + "_" + self.sample_accession + "_analysis_EMC_SLIM_summary.tsv"
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
        return gzip_file, tab_file

    def execute(self):
        command = self.command_builder()
        #command = self.command_builder_mock()
        print('COMMAND:', command)
        jobids =self.run(command)
        print(jobids)
        return(jobids)

