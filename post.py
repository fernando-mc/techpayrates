import boto3
import json
import os
import requests
import time
import uuid

from algoliasearch import algoliasearch

DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
GA_SECRET = os.environ['GOOGLE_RECAPTCHA_TOKEN']
ALGOLIA_APPLICATION_ID = os.environ['ALGOLIA_APPLICATION_ID']
ALGOLIA_SECRET_KEY = os.environ['ALGOLIA_SECRET_KEY']

client = algoliasearch.Client(
    ALGOLIA_APPLICATION_ID, 
    ALGOLIA_SECRET_KEY
)

ag_index = client.init_index('techpayrates')


def validate_inputs(request_input):
    required_fields = ("salary","title","captcha")
    # Check for missing fields
    if not all (field in request_input for field in required_fields):
        return {'status': 'failure', 'message': 'Parameter missing'}
    # Check for empty strings
    for i in request_input:
        if not request_input[i]:
            return {'status': 'failure', 'message': 'content of {} missing'.format(i)}
    return {'status': 'success'}

def validate_captcha(captcha_response):
    url = 'https://www.google.com/recaptcha/api/siteverify'
    response = json.loads(requests.post(
        url, 
        data={
            'secret': GA_SECRET, 
            'response':captcha_response
        }
    ).text)
    return response['success']

def handler(event, context):
    print(event['body'])
    event_body = event['body']
    vi = validate_inputs(event_body)
    if vi['status'] != 'success':
        return {
            "statusCode":400,
            "headers": {"Access-Control-Allow-Origin":"*"},
            "body": vi
        }
    if not validate_captcha(str(event_body['captcha'])):
        return {
            "statusCode":400,
            "headers": {"Access-Control-Allow-Origin":"*"},
            "body": {'status': 'failure', 'message': 'Captcha failed'}
        }
    item = {
        'title': event_body['title'],
        'epochtimestamp': int(time.time() * 1000),
        'date': time.strftime('%b %d, %Y'),
        'salary': int(event_body['salary']),
        'submissionid': str(uuid.uuid4())
    }
    optional_fields = ['location', 'company', 'experience', 'bonus', 'stock', 'gender']
    for field in optional_fields:
        if event_body.get(field):
            if field in ['experience', 'bonus', 'stock']:
                item[field] = int(event_body[field])
            else:
                item[field] = event_body[field]

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
    result = table.put_item(Item=item)
    ag_index.add_object(item)
    # if result['responseCode'] = 200:
    return {
        "statusCode":200,
        "headers": {"Access-Control-Allow-Origin":"*"},
        "body": item
    }
    # else: return baddie