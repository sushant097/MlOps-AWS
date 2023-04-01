import boto3
import os
import json
from boto3.dynamodb.conditions import Key
from datetime import datetime


def lambda_handler(event, context):
    if ('body' not in event or
            event['httpMethod'] != 'PUT'):
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

    current_timestamp = datetime.now().isoformat()

    table = post_table.Table(table_name)
    post_id = event['pathParameters']['id']
    post = json.loads(event['body'])

    params = {
        'id': post_id
    }
    print('PARAMS::>>>>>', params)

    response = table.update_item(
        Key=params,
        UpdateExpression="set content=:c, author=:a, updatedAt=:u",
        ExpressionAttributeValues={
            ':c': post['content'],
            ':a': post['author'],
            ':u': str(current_timestamp)
        },
        ReturnValues="UPDATED_NEW"
    )
    print('::====>', response)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Post updated",
            # "location": ip.text.replace("\n", "")
        }),
    }
