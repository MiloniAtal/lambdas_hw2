import json 
import boto3
import numpy as np
import requests
from requests_aws4auth import AWS4Auth

region = 'us-east-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service,
session_token=credentials.token)

host = 'https://search-photos-fnoyjk7ev3wwyqeuzmmmzt5tje.us-east-1.es.amazonaws.com'
index = 'photos'
url = host + '/' + index + '/_search'

def tester():
    search_url = host + '/' + index + '/_search'
    query = {
        "query": {
            "match": {
                    "labels" : "Cat"
            }
        }
    }
    headers = { "Content-Type": "application/json" }
    es_response_ = requests.get(search_url, auth=awsauth, headers=headers, data=json.dumps(query))
    print(es_response_)
    print(es_response_.text)
    
def lambda_handler(event, context):
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

