from datetime import datetime
import boto3
from io import BytesIO
from PIL import Image, ImageOps
import os
import uuid
import json



s3 = boto3.client('s3')
size = int(os.getenv("THUMBNAIL_SIZE"))
dbtable = str(os.getenv("DYNAMODB_TABLE"))
dynamodb = boto3.resource(
    'dynamodb', region_name=str(os.getenv('REGION_NAME'))
)

def get_s3_image(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    imagecontent = response['Body'].read()
     
    file = BytesIO(imagecontent)
    img = Image.open(file)
    return img         
    
def image_to_thumbnail(image):
    return ImageOps.fit(image, (size, size), Image.ANTIALIAS)
    
def new_filename(key):
    key_split = key.rsplit('.', 1)
    return key_split[0] + "_thumbnail.png"


def upload_to_s3(bucket, thumbnail_key, image, img_size):
    # Saving the image into a BytesIO object to avoid writing to disk
    out_thumbnail = BytesIO()
    
    # specify the file type because there is no file name 
    image.save(out_thumbnail, 'PNG')
    out_thumbnail.seek(0)
    
    response = s3.put_object(
        ACL='public-read',
        Body= out_thumbnail,
        Bucket= bucket,
        ContentType='image/png',
        Key= thumbnail_key
    )
    
    print(response)
    
    url = '{}/{}/{}'.format(s3.meta.endpoint_url, bucket, thumbnail_key)
    
    print(url)
    
    #save image url to db:
    s3_save_thumbnail_url_to_dynamo(url_path=url, img_size=img_size)
    
    return url

def s3_save_thumbnail_url_to_dynamo(url_path, img_size):
    toint = float(img_size*0.53)/1000
    table = dynamodb.Table(dbtable)
    response = table.put_item(
        Item={
            'id': str(uuid.uuid4()),
            'url': str(url_path),
            'approxReducedSize': str(toint) + str('KB'),
            'createdAt': str(datetime.now()),
            'updatedAt': str(datetime.now())
        }
    )
    
    # get all image urls from the bucked and show in a json format.
    return {
        'statusCode':200,
        'headers': {'Content-Type':'application/json'},
        'body': json.dumps(response)
    }
    

def s3_get_thumbnail_urls(event, context):
    # get all image urls from the db and show in json format
    table = dynamodb.Table(dbtable)
    response = table.scan()
    data = response['Items']
    # paginate through the results in a loop
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluateKey'])   
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type':'application/json'},
        'body': json.dumps(data)    
    }
    
def s3_thumbnail_generator(event, context):
    print("Event:: ", event)
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key'] 
    img_size = event['Records'][0]['s3']['object']['size']
    
    if (not key.endswith("_thumbnail.png")): # take image only
        image = get_s3_image(bucket, key) 
        
        # resize image and create thumbnail
        thumbnail = image_to_thumbnail(image)
        
        thumbnail_key = new_filename(key)
        
        url = upload_to_s3(bucket, thumbnail_key, thumbnail, img_size)
        
        return url
    

def s3_get_item(event, context):
    table = dynamodb.Table(dbtable)
    response = table.get_item(Key={
        'id': event['pathParameters']['id']
        
    })
    item = response['Item']
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(item),
        'isBase64Encoded':False,
    }
    
def s3_delete_item(event, context):
    item_id = event['pathParameters']['id']
    
    # Set the default error response
    response = {
        "statusCode": 500,
        "body": f"An error occured while deleting post {item_id}"
    }
    
    table = dynamodb.Table(dbtable)
    response = table.delete_item(Key={
        'id': item_id
    })
    all_good_response = {
        'deleted': True,
        'itemDeletedId': item_id
    }
    
    # If deletion is sucessful for post
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        response = {
            "statusCode": 200,
            "headers": {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps(all_good_response)
        }
        return response
    