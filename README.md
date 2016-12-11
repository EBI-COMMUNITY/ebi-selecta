# ebi-selecta
## Step one input selection into process_selection
* The selecta rule table need to be filled by a script. The script shall consume a TSV file, containing the follwoing inputs:
    Account_id, tax_id, study_acccession, run_accession, pipeline_name, account_type, analysis_id

* The scripts only insert above information into the table, not all of them required. 

process_selection table is as follow:
'account_id'
'tax_id'
'study_accession'
'run_accession'
'pipeline_name'
'analysis_id'
'selection_id'
'selection_provided_date'
'selection_to_info_start'
'selection_to_info_end'
'selection_to_info_error'

Action 1: Example of project to add to SELECTA is: 
 INSERT INTO process_selection (datahub,study_accession,pipeline_name,public,selection_provided_date,webin) values ('dcc_beethoven','PRJEB13610','DTU_CGE','NO',CURTIME(),'Webin-45433');


## Step two from process_selection to process_attributes and process_stages 


## Step three from process_stages to running the stages

### Satge 1 data_provider
get the list of all processes that data provider hasn't been done.

### Satge 2 core_runner 
get the list of all the processes that data_provider has been done but not core_runner, analysis_reporter and process archival

### Satge 3 analysis_reporter
get the list of all the processes that data_provider and core_runner have been done but not analysis_reporter and process archival

### Satge 4 process_archival
get the list of all the processes that data_provider, core_runner, and analysis_reporter have been done but not process archival
