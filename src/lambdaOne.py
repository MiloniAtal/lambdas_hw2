import json 
import boto3
import requests
import datetime
from requests_aws4auth import AWS4Auth
from botocore.exceptions import ClientError
import logging
import re
import os
#from en import singular
#from pattern.text.en import singularize
#from nltk.stem import PorterStemmer
#Running into compatibility issues while adding nltk layer to AWS lambda, hecne using a low level regex based stemmer

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

region = 'us-east-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service,session_token=credentials.token)

#ps = nltk.stem.PorterStemmer()

# AWS Clients
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
host = 'https://' + os.environ['opensearchurl']
index = 'photos'
url = host + '/' + index + '/_doc'
headers = { "Content-Type": "application/json" }

def get_labels(bucket, photo):
    all_labels = rekognition.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}})
    labels = []
    for lab in all_labels['Labels']:
        labels.append(lab['Name'].lower())
    return labels

def index_photo( record ):
    bucket_name = record['s3']['bucket']['name']
    photo_name = record['s3']['object']['key']
    head_response = s3.head_object(Bucket=bucket_name, Key=photo_name)
    print('Head response')
    print(head_response)
    print(head_response.keys())
    if 'customlabels' in head_response['Metadata']:
        customs = head_response['Metadata']['customlabels'].lower().split(',')
    else:
        customs = []
    # bucket_name = "b2-hw2-my2727-ma4338"
    # photo_name = "random2.jpg"
   
    labels = get_labels(bucket_name, photo_name)
    labels.extend(customs)
    labels = list(set(labels))
    
    # TESTING STEMMING of labels
    # To cater to plural
    # print(labels)
    # labels = [ ps.stem(word) for word in labels]
    # labels = list(set(labels))
    # print(labels)
    
    
    # TESTING STEMMING of labels using regex
    #print(labels)
    #labels = [ re.sub(r'less|ship|ing|les|ly|es|s', '', word)  for word in labels]
    #labels = list(set(labels))
    #print(labels)
    
    jsonObj = {
                'objectKey': photo_name,
                'bucket': bucket_name,
                'createdTimestamp': datetime.datetime.now().strftime('%Y-%d-%mT%H:%M:%S'),
                'labels': labels
              }
    print('JSON object to search index')
    print(jsonObj)
    #To insert into opensearch

    r = requests.post(url, auth=awsauth, json = jsonObj, headers=headers)
    logger.debug(r.text)
    
def create_index():    
    headers = { "Content-Type": "application/json" }
    r = requests.get(host + '/_cat/indices/', auth=awsauth, headers=headers)
    if(index not in r.text):
        create = requests.put(host + '/' + index, auth=awsauth, json={}, headers=headers)
        logger.debug(create.text)
    r = requests.get(host + '/_cat/indices/', auth=awsauth, headers=headers)
    logger.debug(r.text)

def delete_documents_index():
    query = {
      "query": {
        "match_all": {}
      }
    }
    headers = { "Content-Type": "application/json" }
    logger.debug("here IMP")
    r = requests.post(host + '/' + index + '/_delete_by_query', auth=awsauth, headers=headers, data=json.dumps(query))
    logger.debug(r.text)
    r = requests.get(host + '/' + index + '/_search', auth=awsauth, headers=headers, data=json.dumps(query))
    logger.debug(r.text)

def lambda_handler(event, context):
    create_index()
    print(event['Records'])
    for record in  event['Records']:
         index_photo(record)
    
    #index_photo(None)
    '''
    example
    [{'eventVersion': '2.1', 'eventSource': 'aws:s3', 'awsRegion': 'us-east-1', 'eventTime': '2022-11-03T02:47:00.235Z', 
    'eventName': 'ObjectCreated:Put', 'userIdentity': {'principalId': 'A2I50MNBVA971P'}, 
    'requestParameters': {'sourceIPAddress': '66.180.180.23'}, 
    'responseElements': {'x-amz-request-id': 'ZSN4S3EP978HNW6D', 
                'x-amz-id-2': '/MzCyEm8FeKNepKhuuXucLDF7HCnvy6tGTv0CF6yPT2u9jBhTQcwlNzeFGWkmq/jmcwHnb/B1nZ7x4Newv4qwLUlef0QaBqo'}, 
    's3': {'s3SchemaVersion': '1.0', 'configurationId': '32d7f07f-cd5e-4833-bfd8-a6df4a1fa53a', 
                'bucket': {'name': 'b2-hw2-my2727-ma4338', 'ownerIdentity': {'principalId': 'A2I50MNBVA971P'},
                'arn': 'arn:aws:s3:::b2-hw2-my2727-ma4338'}, 
                'object': {'key': '20220129_161534.jpg', 'size': 2890664, 'eTag': '6d483c3f226d0b959a5f0de768f189ab', 'sequencer': '0063632BA420993421'}}}]

    '''
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
