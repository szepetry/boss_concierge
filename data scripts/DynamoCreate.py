import boto3
import json
from decimal import Decimal
from datetime import datetime

def create_yelp_table(dynamodb=None):
    dynamodb = boto3.resource('dynamodb',
    region_name='us-east-1',
    aws_access_key_id='AKIAYSZX5FACWW45ADCB',
    aws_secret_access_key='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')
    table = dynamodb.create_table(
        TableName='yelp-restaurants',
        KeySchema=[
            {
                'AttributeName': 'business_id',
                'KeyType': 'HASH'  # Partition key
            },
           {
                'AttributeName': 'insertedAtTimestamp',
                'KeyType': 'RANGE'  # Sort key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'business_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'insertedAtTimestamp',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 4,
            'WriteCapacityUnits': 4
        }
    )
    return table

def write_yelp_data():
    db = boto3.resource('dynamodb',region_name='us-east-1',
    aws_access_key_id='AKIAYSZX5FACWW45ADCB',
    aws_secret_access_key='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')
    count = 0
    table = db.Table('yelp-restaurants')
    with open('yelp.json', 'r') as file:
        for row in file:
            temp = json.loads(row, parse_float=Decimal)
            with table.batch_writer() as batch:
                for i in temp:
                    i['insertedAtTimestamp'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S:%f")
                    batch.put_item(Item=i)
                    count += 1
                    #print(count, end='\r')


def lambda_handler(event, context):
    
    #print("Table status:", yelp_table.table_status)

    write_yelp_data()
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


write_yelp_data()