import json 
import boto3
import requests
from requests_aws4auth import AWS4Auth
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

client = boto3.client('lexv2-runtime')
def connecting_to_opensearch():
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service,
    session_token=credentials.token)
    logger.debug('{}'.format(credentials.access_key))
    logger.debug('{}'.format(credentials.secret_key))
    logger.debug('{}'.format(credentials.token))
    
    host = 'https://' + os.environ['opensearchurl']
    index = 'photos'
    url = host + '/' + index + '/_search'
    return host, index, url, awsauth


def inter(item):
    try:
        return item['value']['interpretedValue']
    except KeyError:
        return None
def get_slots(intent_request):
    return intent_request['slots']

def search_intent(intent_request):
    """
    Performs dialog management and fulfillment for suggesting restaurant.
    """
    intent = intent_request['interpretations'][0]['intent']
    tag1 = get_slots(intent)["tag1"]
    tag2 = get_slots(intent)["tag2"]
    logger.debug('{Here in search_intent}')
    
    if(tag1):
        q1 = inter(tag1)
        logger.debug('{}'.format(q1))
    if(tag2):
        q2 = inter(tag2)
        logger.debug('{}'.format(q2))
    if(tag1 and tag2):
        query = str(tag1) + " or " + str(tag2)

    elif(tag1):
        query = str(tag1)

    else:
        query = None

    logger.debug(query)
    if(query):
        return opensearch(query)
    return []
        
    
    

""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    # logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['interpretations'][0]['intent']['name']
    # Dispatch to your bot's intent handlers
    if intent_name == 'SearchIntent':
        return search_intent(intent_request)

    return []

def opensearch(value):
    query = {
        "query": {
            "match": {
                    "labels" : value
            }
        }
    }
    headers = { "Content-Type": "application/json" }
    host, index, url, awsauth = connecting_to_opensearch()
    
    # logger.debug('{here in opensearch}')
    # logger.debug('{} {} {} {}'.format(url, awsauth, headers, json.dumps(query)))

    es_response_ = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
    es_response = json.loads(es_response_.text).get("hits").get("hits")
    
    matching = []
    for res in es_response:
        matching.append(res['_source']['objectKey'])
    print(es_response_)
    print(es_response_.text)
    print(es_response)
    return matching

def all():
    query = {
      "query": {
        "match_all": {}
      }
    }
    headers = { "Content-Type": "application/json" }
    host, index, url, awsauth = connecting_to_opensearch()
    es_response_ = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
    print(es_response_)
    print(es_response_.text)
    return es_response_

def create_index():    
    headers = { "Content-Type": "application/json" }
    host, index, url, awsauth = connecting_to_opensearch()
    create = requests.put(host + '/' + index, auth=awsauth, json={}, headers=headers)
    logger.debug(create.text)
    r = requests.get(host + '/_cat/indices/', auth=awsauth, headers=headers)
    logger.debug(r.text)




def lambda_handler(event, context):
    #TODO connect to frontent and get messages from there
     
    # msg_from_user = event['messages'][0]['unstructured']['text']
    # sessionId = event['messages'][1]['unstructured']['text']
    # disallowed_character = " ()-"
    # # sessionId = "Tue Oct 11 2022 18:47:03 GMT-0400 (Eastern Daylight Time)"
    # for character in disallowed_character:
    #         sessionId = sessionId.replace(character,"")
    # sessionId.replace("(", "")
    # sessionId.replace(")", "")
    # print(sessionId)
    # print(event)
    # print(context)
    # print(f"Message from frontend: {msg_from_user}")
    
    msg_from_user = "Show me dogs or person"
    sessionId = "testuser"
    
    # Initiate conversation with Lex
    response = client.recognize_text(
            botId='WTTENPIB9B', # MODIFY HERE
            botAliasId='OJX8DOKKZA', # MODIFY HERE
            localeId='en_US',
            sessionId=sessionId,
            text=msg_from_user)
    
    # response = {"interpretations":[{"intent":{"confirmationState":"None","name":"SearchIntent","slots":{"tag1":{"value":{"interpretedValue":"person","originalValue":"person","resolvedValues":["person"]}},"tag2":None},"state":"ReadyForFulfillment"},"nluConfidence":{"score":1.0}},{"intent":{"name":"FallbackIntent","slots":{}}}],"requestAttributes":{},"sessionId":"testuser","sessionState":{"dialogAction":{"type":"Close"},"intent":{"confirmationState":"None","name":"SearchIntent","slots":{"tag1":{"value":{"interpretedValue":"person","originalValue":"person","resolvedValues":["person"]}},"tag2":None},"state":"ReadyForFulfillment"},"originatingRequestId":"e382a7f9-06dd-4265-a5a5-3e38c1baee92","sessionAttributes":{}}}

    matched = dispatch(response)
    return matched
    
