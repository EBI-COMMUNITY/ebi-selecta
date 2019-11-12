from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from flask_jwt import JWT, jwt_required
from sqlalchemy import create_engine
from json import dumps
from flask_jsonpify import jsonify
import psycopg2
from config import config
import base64

params = config()

app = Flask(__name__)
api = Api(app)



"""
**Definition**
Display the API documentation at the browser
"""
@app.route("/")
def index():
    """Present some documentation"""
    with open(os.path.dirname(app.root_path) + '/README.md', 'r') as markdown_file:
        content = markdown_file.read()
        return markdown.markdown(content)

"""
**Definition**
Retrieve all the registered account information

**Endpoint**
`GET /accounts
**Arguments**
**Response**
- `404 Not Found` if the account is not created
- `204 No Content` on success

"""
class AccountList(Resource):
    """
    {
    "account_id": "dcc_XXXX",
    "email": "",
    "password": "password",
    "account_type": "datahub"
    }
    """

    def get(self):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                select * from account;
                """
                cursor.execute(query)
                cols = list(map(lambda x: x[0], cursor.description))
                if not cursor.rowcount:
                    return {'message': 'No accounts found', 'data': {}}, 404
                result = {'data': [dict(zip(tuple(cols), i)) for i in cursor.fetchall()]}
                return jsonify(result)


"""
**Definition**
Create a new datahub account in the Account table

**Endpoint**
`POST /account
**Arguments**
- `"account_id":string` a dcc_xxx account
- `"email":string` Account email
- `"password":string` Account password
- `"account_type":string` account type, eg: datahub

**Response**
- `404 Not Found` if the account is not created
- `204 No Content` on success

"""
class Account(Resource):
    TABLE_NAME = 'account'

    parser = reqparse.RequestParser()
    parser.add_argument('account_id',
                        type=str,
                        required=True,
                        help="This field is mandatory, it is the datahub account name, eg: dcc_xxx")
    parser.add_argument('account_type',
                        type=str,
                        required=True,
                        help="This field is mandatory, default value is datahub")
    parser.add_argument('email',
                        type=str,
                        required=False,
                        help="main datahub email address, optional")
    parser.add_argument('password',
                        type=str,
                        required=True,
                        help="Password create for the datahub , required to fetch private data from datahub repository")

    def post(self):
        data = Account.parser.parse_args()
        account = {'account_id': data['account_id'],
                   'account_type': data['account_type'],
                   'email': data['email'],
                   'password': data['password']
                   }
        print(account)
        try:
            Account.insert(account)
        except:
            return {"message": "An error occurred when inserting the account information"}
        return jsonify(account)

    @classmethod
    def insert(cls, account):
        psswd = base64.b64encode(bytes(account['password'], "utf-8"))[::-1].decode()
        print("New password:{}-->{}".format(account['password'], psswd))
        account['password'] = psswd
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                INSERT INTO {table} (account_id, account_type, email, password) 
                VALUES((%s), (%s),(%s), (%s))
                """.format(table=cls.TABLE_NAME)
                print(query)
                try:
                    cursor.execute(query, (account['account_id'], account['account_type'],
                                           account['email'], account['password']))
                except psycopg2.DatabaseError as error:
                    print(error)

                conn.commit()


"""
**Definition**
Retrieve List of selections and associated rules

**Endpoint**
`GET /selections/
**Arguments**

**Response**
- `404 Not Found` if the run does not exist
- `204 No Content` on success

"""
class ProcessSelectionList(Resource):
    def get(self):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                select * from process_selection
                """
                cursor.execute(query)
                cols = list(map(lambda x: x[0], cursor.description))
                if not cursor.rowcount:
                    return {'message': 'No Selection(s) found', 'data': {}}, 404
                result = {'data': [dict(zip(tuple(cols), i)) for i in cursor.fetchall()]}
                return jsonify(result)


"""
**Definition**
Retrieve List of processed runs analysis id

**Endpoint**
`GET /analysis/<string:identifier>
**Arguments**
- `"process_id":string` a globally unique identifier for the run
**Response**
- `404 Not Found` if the run does not exist
- `204 No Content` on success

"""

class AnalysisList(Resource):
    def get(self):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                select  A.analysis_id, A.submission_id, A.study_accession, A.run_accession,A.datahub,
                B.attribute_value as scientific_name , C.attribute_value as taxonomic_id , D.attribute_value as provider_name,
                E.attribute_value as pipeline_name, F.attribute_value as secondary_acc, G.attribute_value as biosample_id
                from process_report A
                left join process_attributes B on A.process_id=B.process_id and B.attribute_key='scientific_name'
                left join process_attributes C on B.process_id=C.process_id and C.attribute_key='tax_id'
                left join process_attributes D on C.process_id=D.process_id and D.attribute_key='provider_center_name'
                left join process_attributes E on D.process_id=E.process_id and E.attribute_key='pipeline_name'
                left join process_attributes F on E.process_id=F.process_id and F.attribute_key='secondary_sample_acc'
                left join process_attributes G on F.process_id=G.process_id and G.attribute_key='sample_accession'
                where A.process_id in 
                (select process_id from process_report where analysis_id is not null limit 5)
                """
                cursor.execute(query)
                print(query)
                print(dir(cursor))
                cols = list(map(lambda x: x[0], cursor.description))
                print(cols)
                if not cursor.rowcount:
                    return {'message': 'Analysis id not found', 'data': {}}, 404
                result = {'data': [dict(zip(tuple(cols), i)) for i in cursor.fetchall()]}
                return jsonify(result)


"""
**Definition**
Registration of a new datahub in process_selection
, this represents the input to selection stage

**Endpoint**
- POST /input2selection

**Arguments**
- `"study_accession":string` a globally unique identifier for the project
- `"datahub":string` datahub name
- `"pipeline_name":string` pipeline name to process reads in datahub
- `"public":string` YES or NO, status of the data in datahub
- `"webin":string` Webin account
- `"continuity":string` Webin account
- `"process_type":string` Webin account
These arguments populate process_selection.
example input json
{"datahub":"dcc_XXXX",
 "pipeline_name":"Pipeline_XXX",
 "public": "NO",
 "webin": "Webin-45433",
 "continuity": "YES",
 "process_type": "datahub"
}
**Response**
- `404 Not Found` if the run does not exist
- `200 OK` on success
"""
class InputToSelection(Resource):
    TABLE_NAME = 'process_selection'

    parser = reqparse.RequestParser()
    parser.add_argument('datahub',
                        type=str,
                        required=True,
                        help="This field can not be left blank you must provide a datahub name: dcc_XXXX")
    parser.add_argument('study_accession',
                        type=str,
                        required=False,
                        help="This field can be left blank, or input a dcc_XXX valid study acc")
    parser.add_argument('run_accession',
                        type=str,
                        required=False,
                        help="This field can be left blank or input a dcc_XXX valied run accession")

    parser.add_argument('pipeline_name',
                        type=str,
                        required=True,
                        help="This field is mandatory, one of the integraged pipeline, DTU_CGE, EMC_SLIM, BacPipe, RIVM_JOVIAN, EBI-Parasite")
    parser.add_argument('public',
                        type=str,
                        required=True,
                        help="This field is mandatory, and be either NO or YES")
    parser.add_argument('webin',
                        type=str,
                        required=True,
                        help="This field is mandatory, this is the SELECTA submission webin account, currently:Webin-45433")

    parser.add_argument('process_type',
                        type=str,
                        required=True,
                        help="This field must be one of datahub, study, run"
                        )
    parser.add_argument('continuity',
                        type=str,
                        required=True,
                        help="This field must be either YES or NO")

    def post(self):
        data = InputToSelection.parser.parse_args()
        selections = {'datahub': data['datahub'],
                      'study_accession': data['study_accession'],
                      'run_accession': data['run_accession'],
                      'pipeline_name': data['pipeline_name'],
                      'public': data['public'],
                      'webin': data['webin'],
                      'process_type': data['process_type'],
                      'continuity': data['continuity']
                      }
        try:
            InputToSelection.insert(selections)
        except:
            return {"message": "An error occur while inserting selection attributes"}
        return jsonify(selections)

    @classmethod
    def insert(cls, selections):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                INSERT INTO {table} (datahub, study_accession, run_accession, pipeline_name,
                public, selection_provided_date, audit_time, webin, process_type,continuity)
                VALUES((%s), (%s), (%s), (%s), (%s), NOW(), NOW(), (%s), (%s), (%s))
                """.format(table=cls.TABLE_NAME)
                print(query)
                cursor.execute(query,
                               (selections['datahub'], selections['study_accession'], selections['run_accession'],
                                selections['pipeline_name'], selections['public'], selections['webin'],
                                selections['process_type'],
                                selections['continuity']))
                conn.commit()

    @classmethod
    def update(cls, identifier):
        with psycopg2.connect(db) as conn:
            with conn.cursor() as cursor:
                query = """
                Update {table} set selection_to_attribute_start=NULL, selection_to_attribute_end=NULL,
                selection_to_attribute_error=NULL where selection_id=(%s)
                """.format(table=cls.TABLE_NAME)
                print(query)
                cursor.execute(query, (identifier,))
                conn.commit()


""""
**Definition**
Retrieve metadata associated to a specific run

**Endpoints***
`GET /run/<identifier>`

**Arguments**
- `"run_accession":string` a globally unique identifier for the run

**Response**
- `404 Not Found` if the run does not exist
- `200 OK` on success
"""
class RunInfo(Resource):
    TABLE_NAME = 'process_attributes'

    def get(self, identifier):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                select A.run_accession, A.study_accession, A.analysis_id, A.submission_id, A.datahub, A.study_accession,
                B.pipeline_name from process_report A left join process_selection B on
                A.selection_id=B.selection_id where A.run_accession=(%s);
                """
                cursor.execute(query, (identifier,))
                cols = list(map(lambda x: x[0], cursor.description))
                print(cols)
                if not cursor.rowcount:
                    return {'message': 'Run id {} not found'.format(identifier), 'data': {}}, 404
                result = {'data': [dict(zip(tuple(cols), i)) for i in cursor.fetchall()]}
                return jsonify(result)



"""
**Definition**
Retrieve status of a specific run

**Enpoints***
`GET /runstatus/<string:identifier>

**Arguments**
- `"process_id":string` a globally unique identifier for the run

**Response**
- `404 Not Found` if the run does not exist
- `204 No Content` on success
"""
class RunStatus(Resource):
    def get(self, identifier):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = "SELECT * from process_stages where process_id=(%s)".format(identifier)
                cursor.execute(query, (identifier,))
                print("query:{}\nIdentifier:{}".format(query, identifier))

                cols = list(map(lambda x: x[0], cursor.description))
                print(cols)
                if not cursor.rowcount:
                    return {'message': 'Run id {} not found'.format(identifier), 'data': {}}, 404
                result = {'data': [dict(zip(tuple(cols), i)) for i in cursor.fetchall()]}
                return jsonify(result)


"""
**Definition**
Retrieve partially processed runs

**Endpoints**
`GET /incompleteruns/

**Response**
- `404 Not Found` if the run does not exist
- `204 No Content` on success
"""
class IncompleteRunsList(Resource):
    def get(self):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                select * from process_stages where stage_start is null or stage_end is  null;
                """
                cursor.execute(query)
                cols = list(map(lambda x: x[0], cursor.description))
                print(cols)
                if not cursor.rowcount:
                    return {'message': 'Incomplete Runs not found', 'data': {}}, 404
                result = {'data': [dict(zip(tuple(cols), i)) for i in cursor.fetchall()]}
                return jsonify(result)


"""
**Definition**
Retrieve list of failed runs

**endpoints**
`GET /failedruns/

**Response**
- `404 Not Found` if the run does not exist
- `204 No Content` on success

"""
class FailedRunsList(Resource):

    def get(self):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                select * from process_stages where stage_error is not null;
                """
                cursor.execute(query)
                cols = list(map(lambda x: x[0], cursor.description))
                print(cols)
                if not cursor.rowcount:
                    return {'message': 'No failed runs found', 'data': {}}, 404
                result = {'data': [dict(zip(tuple(cols), i)) for i in cursor.fetchall()]}
                return jsonify(result)



"""
**Definition**
Reset a run status in process_stage table

**Endpoints**
`Update /resetstage/

**Arguments**
- `"process_id":string` a globally unique identifier for the run
- `"stage_name":string` stage name to reset one of (data_provider, core_executor, analysis_reporter)

**Response**
- `404 Not Found` if the run does not exist
- `204 No Content` on success

"""
class StageReset(Resource):
    TABLE_NAME = 'process_stages'

    parser = reqparse.RequestParser()
    parser.add_argument('stage_name',
                        required=True,
                        type=str,
                        help='This field is mandatory, value one of the following: '
                             'core_executor, analysis_reporter, process_archival')
    parser.add_argument('process_id',
                        required=True,
                        type=str,
                        help="This field is mandatory, value represent "
                             "the process_id of a sample. [ES]RRXXXX_XXXXX")

    def post(self):
        data = StageReset.parser.parse_args()
        stage_info = {'process_id': data['process_id'],
                      'stage_name': data['stage_name']}
        try:
            StageReset.update(stage_info)
        except:
            return {"message": "Can not update process stages for {}".format(stage_info)}, 404
        return jsonify(stage_info)

    @classmethod
    def update(cls, stage_info):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                UPDATE {table} set stage_start=NULL, stage_end=NULL, stage_error=NULL where process_id=(%s) and stage_name=(%s)
                """.format(table=cls.TABLE_NAME)
                print(query)
                cursor.execute(query, (stage_info['process_id'], stage_info['stage_name']))
                conn.commit()


"""
**Definition**
List all project or studies

**Endpoints**
`GET /studies/`

**Arguments**
- `"identifier":string` a globally unique identifier for the run accession
Given a study accession returns the associated datahub, analysis id, submission id and run accession.

**Response**
- `200 OK` on success
"""
class StudyList(Resource):
    TABLE_NAME = 'process_report'

    def get(self):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                select A.study_accession, A.datahub, A.run_accession, A.analysis_id, A.submission_id,
                B.pipeline_name from process_report A left join process_selection B on A.selection_id=B.selection_id;
                """
                cursor.execute(query)
                cols = list(map(lambda x: x[0], cursor.description))
                print(cols)
                if not cursor.rowcount:
                    return {'message': 'Run id {} not found'.format(identifier), 'data': {}}, 404
                result = {'data': [dict(zip(tuple(cols), i)) for i in cursor.fetchall()]}
                return jsonify(result)


"""
**Definition**
Retrieve all runs and analysis id under a project umbrella

**Endpoints**
`GET /study/<string:identifier>`

**Arguments**
- `"identifier":string` a globally unique identifier for the study or project accession
Given a study accession returns the associated datahub, analysis id, submission id and run accession.

**Response**
- `200 OK` on success
"""
class Study(Resource):
    TABLE_NAME = 'process_report'

    parser = reqparse.RequestParser()
    parser.add_argument('study_acc',
                        type=str,
                        required=True,
                        help='This is the study accession number, must be provided')

    def get(self, identifier):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                select A.study_accession, A.datahub, A.run_accession, A.analysis_id, A.submission_id, 
                B.pipeline_name , C.attribute_value from process_report A 
                left join process_selection B on A.selection_id=B.selection_id
                left join process_attributes C on A.process_id=C.process_id and C.attribute_key='sample_accession'
                where  A.study_accession='PRJEB23496' and A.analysis_id is not null
                """
                cursor.execute(query, (identifier,))
                cols = list(map(lambda x: x[0], cursor.description))
                if not cursor.rowcount:
                    return {'message': 'study accession {} not found'.format(identifier), 'data': {}}, 404
                result = {'data': [dict(zip(tuple(cols), i)) for i in cursor.fetchall()]}
                return jsonify(result)


"""
**Definition**
List information about a datahub

**arguments**
`GET /datahubs/`
`GET /datahub/<identifier>`

**Arguments**
- `"identifier":string` a globally unique identifier for the run accession
Given a datahub return the associated project, analysis id, submission id and run accession.

**Response**
- `200 OK` on success
"""
class DatahubList(Resource):
    TABLE_NAME = 'process_report'

    def get(self):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                select  A.datahub, A.study_accession, A.run_accession, A.analysis_id, A.submission_id,
                B.pipeline_name from process_report A left join process_selection B on A.selection_id=B.selection_id
                """
                cursor.execute(query)
                cols = list(map(lambda x: x[0], cursor.description))
                print(cols)
                if not cursor.rowcount:
                    return {'message': 'No datahub not found'.format(identifier), 'data': {}}, 404
                result = {'data': [dict(zip(tuple(cols), i)) for i in cursor.fetchall()]}
                return jsonify(result)

"""
**Definition**
Details about a datahub

**arguments**
`GET /datahub/<identifier>`

**Arguments**
- `"identifier":string` a globally unique identifier for the run accession
Given a datahub return the associated project, analysis id, submission id and run accession.

**Response**
- `200 OK` on success
"""
class Datahub(Resource):
    TABLE_NAME = 'process_report'

    parser = reqparse.RequestParser()
    parser.add_argument('study_acc',
                        type=str,
                        required=True,
                        help='This is the study accession number, must be provided')

    def get(self, identifier):
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cursor:
                query = """
                select A.study_accession, A.datahub, A.run_accession, A.analysis_id, A.submission_id, 
                B.pipeline_name , C.attribute_value from process_report A 
                left join process_selection B on A.selection_id=B.selection_id
                left join process_attributes C on A.process_id=C.process_id and C.attribute_key='sample_accession'
                where  A.datahub=(%s) and A.analysis_id is not null
                """
                cursor.execute(query, (identifier,))
                cols = list(map(lambda x: x[0], cursor.description))
                if not cursor.rowcount:
                    return {'message': 'Datahub  {} not found'.format(identifier), 'data': {}}, 404
                result = {'data': [dict(zip(tuple(cols), i)) for i in cursor.fetchall()]}
                return jsonify(result)


api.add_resource(AccountList, '/accounts')
api.add_resource(Account, '/account')
api.add_resource(InputToSelection, '/input2selection')
api.add_resource(ProcessSelectionList, '/selections')
api.add_resource(RunStatus, '/runstatus/<string:identifier>')
api.add_resource(AnalysisList, '/analysis')
api.add_resource(RunInfo, '/runinfo/<string:identifier>')
api.add_resource(StudyList, '/studies')
api.add_resource(Study, '/study/<string:identifier>')
api.add_resource(DatahubList, '/datahubs')
api.add_resource(Datahub, '/datahub/<string:identifier>')
api.add_resource(IncompleteRunsList, '/incompleteruns')
api.add_resource(FailedRunsList, '/failedruns')
api.add_resource(StageReset, '/resetstage')
