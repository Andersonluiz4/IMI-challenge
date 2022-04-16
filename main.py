# from clickhouse_driver import Client

# client = Client(host='localhost', password='c6n3s2')

# print(client.execute('SHOW DATABASES'))

# print(client.execute('SELECT * FROM system.numbers LIMIT 5'))

from clickhouse_driver import Client
from datetime import datetime
import json
import pandas as pd
from clickhouse_migrate.migrate import migrate



def connection(): # create clickhouse connection
   return Client(host='localhost', password='c6n3s2')

with open('config.json', 'r') as f:
	config = json.load(f)



class Validation(object):

	def __init__(self, json_data):
		self.json_data = json_data
    
	def validate_json(self): # check if it's a valida json format
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
				print('Incorrect time format')
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
		

class ClickHouseOperations(object):
	def __init__(self, value):
		self.value = value
		
	# recieves the json and insert in the clickhouse database
	def insert(self):
		errors_list = Validation(self.value).overall_validation()
		if len(errors_list) == 0: # if no errors has been founded, proceed with the ingestion
			data = json.loads(self.value)
			types = "'{}'".format(data['type'])
			correlation_id = "'{}'".format(data['correlation_id'])
			site_id = "'{}'".format(data['site_id'])
			dt = "'{}'".format(datetime.fromisoformat(data['time']).strftime("%Y-%m-%dT00:00:00"))
			insert_query = "INSERT INTO test.real_test_6 (*) VALUES ({}, {}, {}, {})".format(dt, types, correlation_id, site_id)
			connection().execute('CREATE TABLE IF NOT EXISTS test.real_test_6 ( ''time'' String, ''type'' String, ''correlation_id'' String, ''site_id'' String) ENGINE = MergeTree() ORDER BY time')
			connection().execute(insert_query)
			value = 'Event captured!'
			return value
		else:
			return errors_list.pop(0)

	def read(self): # run the query in clickhouse database to model data
		if self.value:
			filter_str = "where {} ".format(self.value)
		else:
			filter_str = ''
		try:
			query_str = "with solved as ( select distinct time, site_id, count(*) as solved from test.real_test_6 where type = 'solved' group by time, site_id ), unsolved as ( select distinct time, site_id, count(*) as serve from test.real_test_6 where type = 'serve' group by time, site_id ), unification as ( select distinct a.time as time, a.site_id as site_id, b.solved, c.serve from test.real_test_6 a LEFT JOIN solved b on a.time = b.time and a.site_id = b.site_id LEFT JOIN unsolved c on a.time = c.time and a.site_id = c.site_id ) select distinct time, site_id, sum(b.solved) as solved, sum(c.serve) as serve from unification {} group by time, site_id".format(filter_str)
			results = connection().execute(query_str)
			if results:
				df = pd.DataFrame(results, columns=config['final_schema'])
				dictt = df.to_dict(orient='records')
				json_data = json.dumps(dictt)
			else:
				json_data = 'No records matched the filtering.'
		except:
			json_data = 'Query failed, check your filter taxonomy'
		return json_data