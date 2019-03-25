import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    # Fetch results from the database
    result = table.scan(
        Limit=100
    )

    response = []
    for i in result['Items']:
        response.append({
            "title": i['title'],
            "salary": int(i['salary'])
        })

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin":"*"},
        "body": json.dumps(response)
    }