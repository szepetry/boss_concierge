import json
import boto3
import urllib3
import ast
import random
import boto3
from boto3.dynamodb.conditions import Key
import json
import urllib3
import ast
import random
import os
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION = 'us-east-1'
HOST = 'search-restaurantsearch-67epyyqo43w62rmsekj2ipjxam.us-east-1.es.amazonaws.com'
INDEX = 'restaurants'

def query(term):
    print("Hi",term)
    q = {'size': 20, 'query': {'multi_match': {'query': term}}}
    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth=get_awsauth(REGION, 'es'),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)
    print(client)
    res = client.search(index=INDEX, body=q)
    print(res)

    hits = res['hits']['hits']
    results = []
    for hit in hits:
        results.append(hit['_source'])

    return results


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)


def get_elastic_result(cuisine):
    results = query(cuisine)
    print("Bye",results)
    return results

def send_plain_email(email,message):
    ses_client = boto3.client("ses", region_name=REGION)
    CHARSET = "UTF-8"

    response = ses_client.send_email(
        Destination={
            "ToAddresses": [
                email,
            ],
        },
        Message={
            "Body": {
                "Text": {
                    "Charset": CHARSET,
                    "Data": message,
                }
            },
            "Subject": {
                "Charset": CHARSET,
                "Data": "Restaurant Recommendations",
            },
        },
        Source="bararia.swati@yahoo.in",
    )
    print("email",response)

def getSQSData():
    # Create SQS client
    sqs = boto3.client('sqs')
    
    queue_url = 'https://sqs.us-east-1.amazonaws.com/590138386437/chatBotQueue'
    
    # Receive message from SQS queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    key = "Messages"
    if key not in response:
        return {}

    message = response['Messages'][0]
    receipt_handle = message['ReceiptHandle']
    
    # Delete received message from queue
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
    
    print('Received and deleted message: %s' % message['Body'])
    return message['Body']
    
def updateDbForRecommendation(email,slots):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('userDetails')
    response = table.update_item(
        Key={
            'email': email
        },
        UpdateExpression="set slots=:s",
        ExpressionAttributeValues={
            ':s': slots
        },
        ReturnValues="UPDATED_NEW"
    )
    return response


def lambda_handler(event, context):
    response = getSQSData()
    if response == {}:
        return {
        'statusCode': 200,
        'body': json.dumps('No Messages in Queue')
        }
    slots = json.loads(response)
    

    
    cuisine = slots['cuisine']['value']['originalValue']
    email = slots['email']['value']['originalValue']
    print("email",email)
    query_results = get_elastic_result(cuisine)
    ids_from_es = random.sample(range(0, len(query_results)), 3)
    print("random", ids_from_es)
    business_ids = []
    for i in ids_from_es:
        business_ids.append(query_results[i]['business_id'])

    final_restaurant_recommendation = []
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp-restaurants')
    
    for business_id in business_ids:
        response = table.query(KeyConditionExpression=Key('business_id').eq(business_id))
        final_restaurant_recommendation.append(response['Items'])

    client = boto3.client('sns')

    first_name_res = final_restaurant_recommendation[0][0]['name']
    first_address_res = final_restaurant_recommendation[0][0]['address']
    second_name_res = final_restaurant_recommendation[1][0]['name']
    second_address_res = final_restaurant_recommendation[1][0]['address']
    third_name_res = final_restaurant_recommendation[2][0]['name']
    third_address_res = final_restaurant_recommendation[2][0]['address']
    my_cuisine = cuisine
    number_of_people = slots['no_of_people']['value']['originalValue']
    what_time = slots['dining_time']['value']['originalValue']
    what_date = slots['dining_date']['value']['originalValue']
    # what_time = slots['time']
    
    updateDbForRecommendation(email, slots)
    #
    message = f"Hello! Here are my {my_cuisine} restaurant suggestions for {number_of_people} people,for {what_date}  at {what_time}:\n 1. {first_name_res}, located at {first_address_res} \n 2. {second_name_res}, located at {second_address_res}\n 3. {third_name_res}, located at {third_address_res} \n Enjoy your meal!"
    print(message)
    send_plain_email(email,message)
    #client.publish(PhoneNumber='+1' + slots['phone'], Message=message)

    return {
        'statusCode': 200,
        'body': json.dumps('Sending the data from db!')
    }