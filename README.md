# IM-challenge

## Introduction

This project has the objective to create a input and output api to perform real time ETL analyses.
***
## Structure

The project is devided is 3 main folders:
- **app** - contains all files to run the application.
- **docker** - contains docker image to be deployed on kubernetes.
- **kubertes** - contains the yml file to deploy the application in kubernetes.
***
## Setup

This application require python > 3.7 to run as it should.

### Setup your local clickhouse database
>sudo apt-get install apt-transport-https ca-certificates dirmngr
>sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv E0C56BD4

>echo "deb https://repo.clickhouse.tech/deb/stable/ main/" | sudo tee \
    /etc/apt/sources.list.d/clickhouse.list
>sudo apt-get update

>sudo apt-get install -y clickhouse-server clickhouse-client

>sudo service clickhouse-server start
***

### Setup kafka

-   You need to have a kafka broker running in localhost:9090
-   And a topic called im_challenge.
    > kafka-topics.sh --bootstrap-server localhost:9090 --create --topic im_challenge --partitions 1 --replication-factor 1

It's necessary to create the destination tables and the materialized view to consume from kafka queue:

Create database:

> CREATE DATABASE IF NOT EXISTS im_challenge;

Create table that will consume from kafka queue:

> CREATE TABLE IF NOT EXISTS im_challenge.api_captcha_data (
    time String,
    type String,
    correlation_id String,
    site_id String
  ) ENGINE = Kafka('localhost:9090', 'im_challenge', 'im_ch_01', 'JSONEachRow');

> Create tbale that will recieve all the data from the above table:

> CREATE TABLE IF NOT EXISTS im_challenge.api_captcha_data_2 (
    time String,
    type String,
    correlation_id String,
    site_id String
  ) ENGINE = ReplacingMergeTree()
  ORDER BY (time, type, correlation_id, site_id);

And last create the materialized view:

> CREATE MATERIALIZED VIEW im_challenge.api_captcha_data_vw TO api_captcha_data_2
    AS SELECT * FROM im_challenge.api_captcha_data;

### Running local
 
- Add the clickhouse password defined in the previous step in the *main.py* file line 16.
- Go the app folder and run:
    >pip install -r requirements.txt
- To start, run:
    > python server.py
- Open https://localhost:5000

### Running with docker
***
- In the project root, run:

    >docker build -f docker/Dockerfile -t im-challenge:latest .

- Check if the image has been created:

    >docker image ls

- To start, run:

    > docker run -p 5001:5000 im-challenge

- Open https://localhost:5001

### Running in kubernetes:

- After the image is created, run:

    > kubectl apply -f kubernetes/deployment.yaml

- Check if the service was created as it should:

    > kubectl get pods

- Open https://localhost:6000

## Api's

It was created three main routes in the servery.y file:
- **"/"** - Home screen.
- **"/api/event/<event>"** - Route that recieves the parameteter, perform some validations(check the validation topic) and if the payload is in the correct format, sends to kafka queue.
- **"/api/report" and "api/report/filter"** - Responsible for perfoming the analytics query inside clickhouse and return the json payload to the front end. The filter parameter can be used to ***filter*** the analytics query. Example: */api/report/site_id='12345'*. If the filter is any different from this taxonomy or the column does not exist in clickhouse, will return an error message.
***
## Validations

### Input

- Check if it's a valid json.
- Check if all mandatory fields(check mandatory fields topic) exists in the jayson payload.
- Check if the ***time*** column is in the correct format.As the analytics is agregate by day, it's necessary to confirm if the format to prevent any errors to occour.
***
### Output

- the */report/filter* tries to use the filter inside the analytics query. If thie field does not exists or the taxonomy is incorrect, returns an error message.
***
### Mandatory fields

The mandatory api fields is:
- **time** - time of the event (string UTC isoformat)
- **type** - type of the event may be one of serve or solve (string)
- **correlation_id** - id of the whole captcha procedure (maybe be same across different types, new procedure should get a new ID) (uuid)
- **site_id** - id of site captcha is installed on (uuid) - grouping key

**If one of this fields are missing, it will return an error message when addng a new event.**
***
### Unit tests

In the test.py file there are three unit tests:
- **test_index** - Will check if the *"/api/report"* response is 200.
- **test_report_filter** - Will check the filter parameter in the *"/report/filter"* route. Change the filter variable inside the function to test for a specific value.
- **test_json_format** - Will check the event parameter in the *"/api/event/"* route to check the json format. Change the event variable inside the function to test for a specific value.