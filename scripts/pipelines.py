from macholib.mach_o import SELF_LIBRARY_ORDINAL



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
	
	def __init__(self,fq1,fq2,database_dir,workdir,sequencing_machine, paird):
		self.fq1=fq1
		self.fq2=fq2
		self.database_dir=database_dir
		self.workdir=workdir
		self.sequencing_machine=sequencing_machine
		self.paird=paird
		
		
	def command_builder(self):
		return command
		
	def run(command):
		print "test"
	
	def execute(self):
		command=command_builder()
		run(command)
		post_process()
		print "execute cge"
		
		
	def post_process(self):
		print "doing post process:"
        Assembler
        ContigAnalyzer
        KmerFinder
        PlasmidFinder
        ResFinder
        VirulenceFinder
        out.tsv
        
		
		
		