

# SELECTA Registry Service

## Usage

All SELECTA API responses will have the form

```json
{
    "data": "content of the response",
    "message": "Description of what happened"
}
```

Following responses and definitions will only show the expected value of the data field

### List all analysis

**Definition**

`GET /analysis`


**Response**

- `200 OK` on success

```json
[
    {
        "identifier": "ERZ651806",
        "submission_id": "ERA1492718",
        "project_acc": "PRJEB23496",
        "biosample": "SAMEA4527599",
        "run_accession": "ERR2200450",
        "pipeline_name": "EMC_SLIM",
        "datahub": "dcc_beard",
        "Scientific_name": "Wastewater metagenome",
        "provider_center_name": "ERASMUS MC"

    },
    {
        "identifier": "ERZ667923",
        "submission_id": "ERA1539546",
        "project_acc": "PRJEB18998",
        "biosample": "SAMEA80401168",
        "run_accession": "ERR1822677",
        "pipeline_name": "DTU_CGE",
        "datahub": "dcc_bley",
        "Scientific_name": "Salmonella enterica subsp. diarizonae",
        "provider_center_name": "University Hospital Galway"
    }
]
```


### Status of a run

**Definition**

`GET /stage/<identifier>`

**Arguments**

- `"identifier":string` a globally unique identifier for the run accession

Given a run accession return the various SELECTA stages status (stage_start, stage_end dates).

**Response**

- `201 Created` on success


```json
[
    {
        "stage_name": "data_provider",
        "stage_start": "date",
        "stage_end": "date",
        "stage_error": "NULL"


    },
    {
        "stage_name": "core_executor",
        "stage_start": "date",
        "stage_end": "date",
        "stage_error": "NULL"


    },
    {
        "stage_name": "analysis_provider",
        "stage_start": "date",
        "stage_end": "date",
        "stage_error": "NULL"


    },
    {
        "stage_name": "archival",
        "stage_start": "date",
        "stage_end": "date",
        "stage_error": "NULL"


    }
]
```


### Registering a new analysis

**Definition**

`POST /selection`


**Arguments**

- `"study_accession":string` a globally unique identifier for the project
- `"datahub":string` datahub name
- `"pipeline_name":string` pipeline name to process reads in datahub
- `"public":string` YES or NO, status of the data in datahub
- `"webin":string` Webin account
- `"continuity":string` Webin account
- `"process_type":string` Webin account

These arguments populate process_selection.

**Response**

- `201 Created` on success

```json
{
    "study_accession": "PRJEB13610",
    "datahub":"dcc_beethoven",
    "pipeline_name": "DTU_CGE",
    "public": "NO",
    "webin": "Webin-45433",
    "continuity": "Yes",
    "process_type": "study"

}
```

## Lookup run details
**Definition**

`GET /run/<identifier>`


**Arguments**

- `"run_accession":string` a globally unique identifier for the run

**Response**

- `404 Not Found` if the run does not exist
- `200 OK` on success


```json
{
    "provider_center_name": "Centre for Genomic Epidemiology, National Food Institute, Technical University of Denmark (DTU), Denmark",
    "selection_id": "31",
    "datahub": "dcc_bromhead",
    "tax_id": "562",
    "scientific_name": "Escherichia coli",
    "sample_accession": "SAMEA4058441",
    "secondary_sample_acc": "ERS1229551",
    "experiment_accession": "ERX1583496",
    "study_accession": "PRJEB14641",
    "secondary_study_acc": "ERP016296",
    "run_accession": "ERR1512469",
    "pipeline_name": "UAntwerp_bacpipe",
    "gzip_analysis_file": "ERR1512469-16052019133046_SAMEA4058441_analysis_UAntwerp_Bacpipe_all.tar.gz",
    "tab_analysis_file": "ERR1512469-16052019133046/ERR1512469-16052019133046_SAMEA4058441_analysis_UAntwerp_Bacpipe_summary.xlsx",
    "provider_webin_id": "",
    "instrument_platform": "ILLUMINA",
    "fastq_files": "ERR1512469_1.fastq.gz;ERR1512469_2.fastq.gz",
    "fastq1": "ERR1512469_1.fastq.gz",
    "fastq2": "ERR1512469_2.fastq.gz",
    "fastq1_md5": "7811a85c757e74c62701544d8aec9a45",
    "fastq2_md5": "cefdce1be337a72e0af14989ca53c951",
    "public": "NO",
    "analyst_webin": "Webin-45433",
    "tab_analysis_file2": "",
    "tab_analysis_file2_md5": "",
    "pair": "True",
    "gzip_analysis_file_md5": "ad93fb0e38b8c43a40d7c1fa215cc3ad",
    "tab_analysis_file_md5": "df1913d2985d1c1a27ff01a706e6fa0d"
    }

```

## Reset a run status in process_stage table

**Definition**

`Update /process/<identifier>`


***Arguments***

- `"process_id":string` a globally unique identifier for the run
- `"stage_name":string` stage name to reset one of (data_provider, core_executor, analysis_reporter)

**Response**

- `404 Not Found` if the run does not exist
- `204 No Content` on success

```json
{
    "stage_name": "data_provider",
    "stage_start": "NULL",
    "stage_end": "NULL",
    "stage_error": "NULL"
}
```


### List all project

**Definition**

`GET /project/<identifier>`


**Arguments**

- `"identifier":string` a globally unique identifier for the run accession

Given a study accession returns the associated datahub, analysis id, submission id and run accession.


**Response**

- `200 OK` on success

```json
[
    {
        "study_accession": "PRJEB2822",
        "datahub": "dcc_beethoven" ,
        "run_accession": "ERR233406",
        "process_id": "ERR233406-25042019111808",
        "selection_id": 10,
        "analysis": "ERZ894563",
        "process_report_start_time": "2019-04-25 11:18:08.230211+01",
        "process_report_end_time": "2019-04-28 23:12:32.309399+01",
        "process_report_id": 790,
        "submission_id": "ERA1870016"
    },
    {
        "study_accession": "PRJEB2822",
        "datahub": "dcc_beethoven" ,
        "run_accession": "ERR233406",
        "process_id": "ERR233406-25042019111808",
        "selection_id": 10,
        "analysis": "ERZ894563",
        "process_report_start_time": "2019-04-25 11:18:08.230211+01",
        "process_report_end_time": "2019-04-28 23:12:32.309399+01",
        "process_report_id": 790,
        "submission_id": "ERA1870016"
    }

]

```


### List information about a datahub

**Definition**

`GET /datahub/<identifier>`


**Arguments**

- `"identifier":string` a globally unique identifier for the run accession

Given a datahub return the associated project, analysis id, submission id and run accession.

**Response**

- `200 OK` on success

```json
[
    {
        "datahub": "dcc_beethoven" ,
        "study_accession": "PRJEB2822",
        "run_accession": "ERR233406",
        "process_id": "ERR233406-25042019111808",
        "selection_id": 10,
        "analysis": "ERZ894563",
        "process_report_start_time": "2019-04-25 11:18:08.230211+01",
        "process_report_end_time": "2019-04-28 23:12:32.309399+01",
        "process_report_id": 790,
        "submission_id": "ERA1870016"
    },
    {
        "datahub": "dcc_beethoven" ,
        "study_accession": "PRJEB2822",
        "run_accession": "ERR233406",
        "process_id": "ERR233406-25042019111808",
        "selection_id": 10,
        "analysis": "ERZ894563",
        "process_report_start_time": "2019-04-25 11:18:08.230211+01",
        "process_report_end_time": "2019-04-28 23:12:32.309399+01",
        "process_report_id": 790,
        "submission_id": "ERA1870016"
    }
]

```

