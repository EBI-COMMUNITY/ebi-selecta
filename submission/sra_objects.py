from lxml import etree
import lxml.builder 
from django.template.defaultfilters import title

#sudo pip install --upgrade setuptools
#wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python
#sudo pip install lxml

class analysis_pathogen_analysis:
	
	
	def __init__(self,alias,analysis_centre,submission_centre,run_accession,study_accession,pipeline_name,analysis_date,analysis_files,title,description,analysis_xml_file):
		self.alias=alias
		self.analysis_xml_file=analysis_xml_file
		self.analysis_centre=analysis_centre
		self.submission_centre=submission_centre
		self.run_accession=run_accession
		self.study_accession=study_accession
		self.pipeline_name=pipeline_name
		self.analysis_date=analysis_date
		self.analysis_files=analysis_files
		self.title=title
		self.description=description
		
	
	def build_analysis(self):
		analysis_set = etree.Element('ANALYSIS_SET')
		analysis_xml = etree.ElementTree(analysis_set)
		analysisElt = etree.SubElement(analysis_set, 'ANALYSIS', alias=self.alias , center_name=self.submission_centre, analysis_center=self.analysis_centre ,analysis_date=self.analysis_date)
		title = etree.SubElement(analysisElt, 'TITLE')
		title.text = self.title
		description = etree.SubElement(analysisElt, 'DESCRIPTION')
		description.text = self.description
		studyrefElt = etree.SubElement(analysisElt, 'STUDY_REF', accession=self.study_accession)
		runrefElt = etree.SubElement(analysisElt, 'RUN_REF', accession=self.run_accession)
		analysis_type = etree.SubElement(analysisElt, 'ANALYSIS_TYPE')
		type = etree.SubElement(analysis_type, 'PATHOGEN_ANALYSIS')
		files = etree.SubElement(analysisElt, 'FILES')
		file1Elt = etree.SubElement(files,'FILE', filename=self.analysis_files[0].file_name,filetype=self.analysis_files[0].file_type,checksum_method="MD5", checksum=self.analysis_files[0].file_md5)
		file2Elt = etree.SubElement(files,'FILE', filename=self.analysis_files[1].file_name,filetype=self.analysis_files[1].file_type,checksum_method="MD5", checksum=self.analysis_files[1].file_md5)
		print lxml.etree.tostring(analysis_xml, pretty_print=True,xml_declaration = True, encoding='UTF-8')
		analysis_xml.write(self.analysis_xml_file,pretty_print=True,xml_declaration = True, encoding='UTF-8')
		
		


class submission:
	
	
	def __init__(self,analysis_centre,uniqu_name):
		self.analysis_centre=analysis_centre
		self.uniqu_name=uniqu_name
	
	
	
	
class analysis_file:

	def __init__(self,file_name,file_type,file_md5):
		self.file_name=file_name
		self.file_type=file_type
		self.file_md5=file_md5