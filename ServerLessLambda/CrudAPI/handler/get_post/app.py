import boto3
import os
import json
from boto3.dynamodb.conditions import Key


def lambda_handler(event, context):
    if ('body' not in event or
            event['httpMethod'] != 'GET'):
        return {
            'statusCode': 400,
            'headers': {},
            'body': json.dumps({'msg': 'Bad Request'})
        }

    table_name = os.environ.get('DYNAMODB_TABLE', 'Posts')
    region = os.environ.get('REGION_NAME', 'us-west-2')

    post_table = boto3.resource(
        'dynamodb',
        region_name=region
    )

    table = post_table.Table(table_name)
    post_id = event['pathParameters']['id']

    response = table.query(
        KeyConditionExpression=Key('id').eq(post_id)
    )
    print(':::::==>>>', response)

    return {
        "statusCode": 200,
        "body": json.dumps(response['Items']),
    }
