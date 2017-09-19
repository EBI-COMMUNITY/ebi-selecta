#!/usr/bin/env python3


import argparse
import xml.etree.ElementTree as ET
import time
import hashlib
import ftplib


__author__ = 'Nima Pakseresht'


def get_args():
    
    global runid
    global studyid
    global analysis_temp
    global submission_temp
    global program_name
    global sampleid
    global file_name
    global action
    global analysis_centre
    global submission_centre
    # Assign description to the help doc
    parser = argparse.ArgumentParser(description='Script retrieves schedules from a given server')
    # Add arguments
    parser.add_argument('-anacentre', '--analysis-centre', type=str, help='Run Id of the reads', required=False)
    parser.add_argument('-subcentre', '--submission-centre', type=str, help='Run Id of the reads', required=False)
    parser.add_argument('-run', '--runid', type=str, help='Run Id of the reads', required=True)
    parser.add_argument('-study', '--studyid', type=str, help='Run Id of the reads', required=True)
    parser.add_argument('-analysistemp', '--analysis-temp', type=str, help='Run Id of the reads', required=True)
    parser.add_argument('-subtemp', '--submission-temp', type=str, help='Run Id of the reads', required=True)
    parser.add_argument('-program', '--program-name', type=str, help='Run Id of the reads', required=True)
    parser.add_argument('-sample', '--sampleid', type=str, help='Sample id of the reads', required=True)    #, nargs='+' 
    parser.add_argument('-file', '--file-name', type=str, help='Sample id of the reads', required=True)
    parser.add_argument('-account', '--ENA-account', type=str, help='Sample id of the reads', required=True)
    parser.add_argument('-pass', '--password', type=str, help='Sample id of the reads', required=True)
    parser.add_argument('-action', '--action', type=str, help='The action that need to be taken: assembly,annotation,quality,contamination,submission', required=True, default=None)

    args = parser.parse_args()
    
    if args.analysis_centre is None:
       analysis_centre="EMBL-EBI"
    else:
       analysis_centre=args.analysis_centre

    if args.submission_centre is None:
       submission_centre="EMBL-EBI"
    else:
       submission_centre=args.submission_centre
    runid=args.runid
    studyid=args.studyid
    analysis_temp=args.analysis_temp
    submission_temp=args.submission_temp
    program_name=args.program_name
    sampleid=args.sampleid
    file_name=args.file_name
    action=args.action
    # Match return values from get_arguments()
    # and assign to their respective variables
    
    
def convertAnalysisTemp(tempAnalysisFile):
    with open(tempAnalysisFile, 'r') as template_file:
         content = template_file.read()
    content=content.replace("TODO1:FILENAE-DATE-TIME",getAlias("analysis"))
    content=content.replace("TODO2:DATA-CENTRE-NAME",submission_centre)
    content=content.replace("TODO3:ANALYSIS-CENTRE-NAME",analysis_centre)
    content=content.replace("TODO4:ANALYSIS-DATE-TIME",dateTime)  #2015-12-28T00:00:00
    content=content.replace("TODO5:TITLE-RUNID","ERASMUS Virus Discovery")
    content=content.replace("TODO6:ANALYSIS-DESCRIPTION","ERASMUS Virus Discovery on Read data")
    content=content.replace("TODO7:STUDYID",studyid)
    content=content.replace("TODO8:SAMPLEID",sampleid[0])
    content=content.replace("TODO9:RUNID",runid)
    content=content.replace("TODO10:FILE-TO-SUBMIT",file_name)
    content=content.replace("TODO11:FILE-CHECKSUM", calculateMd5(file_name))
    f = open(analysisXmlFile,"w")
    f.write(content)
    f.close
    print(content)
    
    
def convertSubmissionTemp(tempSubmissionFile):
    with open(tempSubmissionFile, 'r') as template_file:
         content = template_file.read()
    content=content.replace("TODO1:UNIQUE_NAME",getAlias("submission"))
    content=content.replace("TODO2:CENTER_NAME",analysis_centre)
    content=content.replace("TODO3:ACTION","ADD")
    content=content.replace("TODO4:ANALYSIS_FILE",analysisXmlFile)
    f = open(submissionXmlFile,"w")
    f.write(content)
    f.close  
    print(content)

def getDateTime():
    return time.strftime("%Y-%m-%dT%H:%M:%S")
    

def getAlias(type):
    alias=file_name+"-"+type+"-"+getDateTime()
    return alias
    
def calculateMd5(file):
    return  hashlib.md5(open(file, 'rb').read()).hexdigest()
    
    
def uploadFileToEna(file):
    ftp = ftplib.FTP("xx.xx.xx.xx")
    ftp.login("UID", "PSW")
    myfile = open(filename, 'r')
    ftp.storlines('STOR ' + filename, myfile)
    myfile.close()
        
#curl -F "SUBMISSION=@submission.xml"  -F "ANALYSIS=@analysis.xml" "https://www-test.ebi.ac.uk/ena/submit/drop-box/submit/?auth=ENA%20USERNAME%20PASSWORD

if __name__ == '__main__':
    
     global dateTime
     global submissionXmlFile
     global analysisXmlFile
     get_args()
     dateTime=time.strftime("%Y-%m-%dT%H:%M:%S")
     submissionXmlFile=file_name+"-submission.xml"
     analysisXmlFile=file_name+"-analysis.xml"
     convertAnalysisTemp(analysis_temp)
     convertSubmissionTemp(submission_temp)
     uploadFileToEna(file_name)