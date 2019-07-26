#Getting list of to run data_provider 
select process_id,selection_id from process_stages where stage_start is null and stage_end is null and stage_name='data_provider';


#Getting list of to run core_executor 
select process_id,selection_id from process_stages where stage_start is null and stage_end is null and stage_error is null and stage_name='core_executor' and process_id not in (select distinct(process_id) from process_stages where (stage_start is not null or stage_end is not null) and stage_name in ('analysis_reporter','process_archival')) and process_id in (select distinct(process_id) from process_stages where stage_start is not null and stage_end is not null and stage_error is null and stage_name='data_provider');


#Getting list of to run analysis_reporter
select process_id,selection_id from process_stages where stage_start is null and stage_end is null and stage_error is null and stage_name='analysis_reporter' and process_id not in (select distinct(process_id) from process_stages where (stage_start is not null or stage_end is not null) and stage_name='process_archival') and process_id in (select distinct(process_id) from process_stages where stage_start is not null and stage_end is not null and stage_error is null and stage_name='data_provider') and process_id in  (select distinct(process_id) from process_stages where stage_start is not null and stage_end is not null and stage_error is null and stage_name='core_executor');


#Getting list of to run process_archival
select process_id,selection_id from process_stages where stage_start is null and stage_end is null and stage_error is null and stage_name='process_archival' and process_id in (select distinct(a.process_id) from process_stages a,process_stages b, process_stages c  where a.stage_start is not null and a.stage_end is not null and a.stage_error is null and a.stage_name='data_provider' and b.stage_start is not null and b.stage_end is not null and b.stage_error is null and b.stage_name='core_executor' and c.stage_start is not null and c.stage_end is not null and c.stage_error is null and c.stage_name='analysis_reporter' and a.process_id=b.process_id and b.process_id= c.process_id);

#Example of updating and remove the error to compelete a stage and carry on with other stages
update process_stages set stage_end=CURTIME(), stage_error=null where stage_error like 'Waiting for PlasmidFinder%';

