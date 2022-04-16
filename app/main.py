from clickhouse_driver import Client
from datetime import datetime
import json
import pandas as pd
from kafka import KafkaProducer
from kafka.errors import KafkaError

producer = KafkaProducer(bootstrap_servers=['localhost:9090'])

def connection(): # create clickhouse connection
    connect = Client(host='localhost', password='your clickhouse password')
    try:
        connect.execute("select now();")
        return connect
    except:
        False

with open('config.json', 'r') as f: # when running local, remove the app/ path
    config = json.load(f)

# responsible for validatind the return payload
class Validation(object):

    def __init__(self, json_data):
        self.json_data = json_data
    
    def validate_json(self): # check if it's a valid json format
        try:
            json.loads(self.json_data)
            return True
        except ValueError:
            return False

    def validate_mandatory_fields(self): # check if the parameters has all mandatory fields
        if self.validate_json():
            missing_fields = []
            data = json.loads(self.json_data)
            mandatory_fields = config['mandatory_fields']
            for field in mandatory_fields: # iterate over the mandatory fields list
                try:
                    value = data[field] # try to get the mandatory field inside the proviced json file
                    print(f'Mandatory field {field} here!')
                except:
                    print(f'Mandatory field {field} not here!')
                    missing_fields.append(field) # if there is one missing field, append to the list and return the error to the user

            return missing_fields

    def validate_time(self): # check if the time column is in the correct format
        if self.validate_json() and len(self.validate_mandatory_fields()) == 0:
            data = json.loads(self.json_data)
            try:
                datetime.fromisoformat(data['time']).strftime("%Y-%m-%dT00:00:00")
                return True
            except ValueError:
                print('Incorrect time format.')
                return False

    def overall_validation(self): # run all validations and return if any errors were found
        errors_list = []
        json_validator = self.validate_json()
        fields_validation = self.validate_mandatory_fields()
        time_validator = self.validate_time()
        if not json_validator:
            errors_list.append("Incorrect json format. ")
            return errors_list
        if json_validator and len(fields_validation) > 0:
            errors_list.append("Missing fields: {} ".format(fields_validation))
        if json_validator and len(fields_validation) == 0:
            if not time_validator:
                errors_list.append("Incorrect date format. ")
        return errors_list
    
# responsible for inserting in kafka queue and reading from clickhouse
class ClickHouseOperations(object):
    def __init__(self, value):
        self.value = value
        
    # recieves the json and insert in the clickhouse database
    def insert(self):
        if connection():
            errors_list = Validation(self.value).overall_validation()
            if len(errors_list) == 0: # if no errors has been founded, proceed with the ingestion
                KafkaProducer(self.value).produce_to_kafka()
                value = 'Event captured!'
                return value
            else:
                return errors_list.pop(0)
        else:
            return 'Unable to connect to clickhouse database.'

    def read(self): # run the query in clickhouse database to model data
        if connection():
            if self.value:
                filter_str = "where {} ".format(self.value) # add filter if exists
            else:
                filter_str = ''
            query_str = "with solved as ( select distinct time, site_id, count(*) as solved from im_challenge.api_captcha_data_vw where type = 'solved' group by time, site_id ), unsolved as ( select distinct time, site_id, count(*) as serve from im_challenge.api_captcha_data_vw where type = 'serve' group by time, site_id ), unification as ( select distinct a.time as time, a.site_id as site_id, b.solved, c.serve from im_challenge.api_captcha_data_vw a LEFT JOIN solved b on a.time = b.time and a.site_id = b.site_id LEFT JOIN unsolved c on a.time = c.time and a.site_id = c.site_id ) select distinct time, site_id, sum(b.solved) as solved, sum(c.serve) as serve from unification {} group by time, site_id".format(filter_str)
            results = connection().execute(query_str)
            if results:
                df = pd.DataFrame(results, columns=config['final_schema'])
                dictt = df.to_dict(orient='records')
                json_data = json.dumps(dictt)
            else:
                json_data = 'No records matched the filtering.'

            return json_data
        else:
            return 'Unable to connect to clickhouse database.'
        
# responsible for sending the payload to kafka
class KafkaProducer(object):

    def __init__(self, value):
        self.value = value

    def produce_to_kafka(self): 
        future = producer.send('im_challenge', bytes(self.value, encoding="ascii"))
        try:
            record_metadata = future.get(timeout=10)
        except KafkaError:
            print('Error while sending message.')
            pass