# ebi-selecta improvements

## Installation and deployment
* use Terraform to create the VM for selecta
* Put all the installation code in ansible
* put the whole SELECTA in Docker
* put the whole SELECTA in Kubernetes
* continuous integration
* Continous Deployment
* TDD 



## Functionality and code update
* add unit test to the code
* Analysis shall be updatable: to do that the analysis accession need to be recorded after analysis submission. This need to be recorded in process_attribute as analysis_result_id. Add a column ‘’process” to The process_selection table and only select the new jobs based on ‘Yes’ and ‘No’ in this. The default is Yes. If it is NO so means no action. If it is YES there are three options, 1:when the process hasn’t been already Started, do as how it does it now. If the process selection has started, leave it as it is. If the process has been finished, create a new selection object with all the info from the original selection id and also add the analysis_result_id  to the selection_attributes of new selection entries. And turn the YES to NO (This needs to be done safely in a transaction way for whole of it.) 

* plan for different analysis categorisation. Currently everything is based on run.
* Input_to_selection needs to be done.
* Metadata need to be captured from data portal

## Consideration todo list
* Consider adding Django for SELECTA management
* Consider using PostgreSQL instead of MySQL
* Consider installing SELECTA in AWS
* Consider running it in hadoop system 
* Consider Spark
* RESTful Api
* Consider using rabbitq and celery (python based) scheduler
* Consider using messaging service.


2) plan for different analysis categorisation. Currently everything is based on run.
3) Consider using hadoop system 
4) Consider using no-sql databases
5) Consider adding overall status for each analysis
6) It requires job scheduler to schedule the jobs
11) Analysis reporter needs to report the sample accession
12) How to report the core pipeline and database version
13) update the core pipeline and databases 
14) How to re-run the same analysis and update the result of analysis.
15) review the messaging service.
16) there is bug related to cases where there are multiple samples per run
