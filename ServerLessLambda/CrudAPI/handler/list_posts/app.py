import boto3
import os
import json


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
    response = table.scan()
    print(':::::==>>>', response)

    return {
        'statusCode': 200,
        'headers': {},
        'body': json.dumps(response['Items'])
    }
