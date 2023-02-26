import json
import boto3
import logging
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import ast
import random
import json
import re
from datetime import datetime
import dateutil.tz


def get_slots(intent_request):
    return intent_request['sessionState']['intent']['slots']


def get_slot(intent_request, slotName):
    slots = get_slots(intent_request)
    print(slots[slotName])
    if slots is not None and slotName in slots and slots[slotName] is not None:
        try:
            return slots[slotName]['value']['interpretedValue']
        except KeyError:
            try:
                return slots[slotName]['value']['resolvedValues'][0]
            except IndexError:
                # slots[slotName]['value']['originalValue']
                return slots[slotName]['value']['originalValue']
        except Exception as e:
            return slots[slotName]['value']['originalValue']
    else:
        return None


def get_session_attributes(intent_request):
    sessionState = intent_request['sessionState']
    if 'sessionAttributes' in sessionState:
        return sessionState['sessionAttributes']

    return {}


def close(intent_request, session_attributes, fulfillment_state, message):
    intent_request['sessionState']['intent']['state'] = fulfillment_state
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close'
            },
            'intent': intent_request['sessionState']['intent']
        },
        'messages': [message],
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }


def elicit_slot(intent_request, session_attributes, slotToElicit, slots, message=None):
    if message is None:
        return {
        "sessionState": {
            "dialogAction": {
                "slotToElicit": str(slotToElicit),
                "type": "ElicitSlot",
                "slots": slots
            },
            'intent': intent_request['sessionState']['intent'],
            'sessionAttributes': session_attributes,
            'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
        }
    }
    
    return {
        "sessionState": {
            "dialogAction": {
                "slotToElicit": str(slotToElicit),
                "type": "ElicitSlot",
                "slots": slots
            },
            'intent': intent_request['sessionState']['intent'],
            'sessionAttributes': session_attributes,
            'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
        },
        'messages': [{'contentType': 'PlainText', 'content': message}]
    }

def check_email(email):
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if(re.fullmatch(email_regex, email)):
        return True
    else:
        return False

def DiningIntent(intent_request):
    try:
        cuisines = ['chinese', 'indian','american', 'mexican', 'italian', 'french', 'thai']
        eastern = dateutil.tz.gettz('US/Eastern')
        #datetime.datetime.now(tz=eastern)
        now = str(datetime.now(tz=eastern))
        date = now.split(" ")[0]
        time = now.split(" ")[1]
        session_attributes = get_session_attributes(intent_request)
        slots = get_slots(intent_request)
        
        if not get_slot(intent_request, 'email'):
            return elicit_slot(intent_request, session_attributes, 'email', slots)
        elif not get_slot(intent_request, 'location'):
            if(not check_email(get_slot(intent_request, 'email'))):
                del slots['email']
                text = "Please enter a valid email."
                return elicit_slot(intent_request, session_attributes, 'email', slots,text)
            print("inside location")
            if not get_slot(intent_request, 'confirmation'):
                print("inside none confirmation")
                dynamodb = boto3.resource('dynamodb')
                table = dynamodb.Table('userDetails')
                table_response = table.query(KeyConditionExpression=Key('email').eq(get_slot(intent_request, 'email')))
                if len(table_response["Items"]) > 0 :
                    print("inside history")
                    slot = table_response["Items"][0]['slots']
                    send_sqs_message("chatBotQueue", slot)
                    return elicit_slot(intent_request, session_attributes, 'confirmation', slots)
            # if(get_slot(intent_request, 'confirmation') and get_slot(intent_request, 'confirmation').lower() =='yes'):
            #     return elicit_slot(intent_request, session_attributes, 'location', slots)
            elif(get_slot(intent_request, 'confirmation').lower() =='no'):
                print("inside no confirmation")
                text = "You’re all set. Check email for Previous Search Results. Have a good day."
                message =  {
                        'contentType': 'PlainText',
                        'content': text
                    }
                fulfillment_state = "Fulfilled"
                return close(intent_request, session_attributes, fulfillment_state, message)
            elif(get_slot(intent_request, 'confirmation').lower() =='yes'):
                return elicit_slot(intent_request, session_attributes, 'location', slots)
            elif (get_slot(intent_request, 'confirmation').lower() !='yes' or get_slot(intent_request, 'confirmation').lower() !='no'):
                return elicit_slot(intent_request, session_attributes, 'confirmation', slots, "Please enter only yes or no.")
            return elicit_slot(intent_request, session_attributes, 'location', slots)
        elif not get_slot(intent_request, 'cuisine'):
            if(get_slot(intent_request, 'location').lower()!= "manhattan" ):
                text = 'Currently we only have suggestions for Manhattan, no suggestions available for restaurants in {}. Apologies for the inconvenience, would you like suggestions for a different location?  '.format(get_slot(intent_request, 'location'))
                del slots['location']
                return elicit_slot(intent_request, session_attributes, 'location', slots,text)
            return elicit_slot(intent_request, session_attributes, 'cuisine', slots)
        elif not get_slot(intent_request, 'no_of_people'):
            if get_slot(intent_request, 'cuisine').lower() not in cuisines:
                print("bad cuisine request")
                text = 'Currently we only have suggestions for American, Chinese, Indian, French, Italian and Thai cuisines, no suggestions available for restaurants with {} cuisine. Apologies for the inconvenience, would you like suggestions for a different cuisine?  '.format(get_slot(intent_request, 'cuisine'))
                del slots['cuisine']
                return elicit_slot(intent_request, session_attributes, 'cuisine', slots,text)
            return elicit_slot(intent_request, session_attributes, 'no_of_people', slots)
        elif not get_slot(intent_request, 'dining_date'):
            print("TEst here: "+str(intent_request['sessionState']['intent']['slots']['dining_date']))
            if not get_slot(intent_request, 'no_of_people').isdigit()  or int(get_slot(intent_request, 'no_of_people')) >20 or int(get_slot(intent_request, 'no_of_people')) <= 0:
                del slots['no_of_people']
                text = "Invalid number. Number of people can only be between 0 and 21 for making a reservation. Please enter number of people again."
                return elicit_slot(intent_request, session_attributes, 'no_of_people', slots,text)
            return elicit_slot(intent_request, session_attributes, 'dining_date', slots)
        elif not get_slot(intent_request, 'dining_time'):
            print("Reached")
            if (intent_request['sessionState']['intent']['slots']['dining_date']['value']['resolvedValues'] == [] or 'interpretedValue' not in intent_request['sessionState']['intent']['slots']['dining_date']['value']  or get_slot(intent_request, 'dining_date') <date):
                print("In resloved v bug")
                del slots['dining_date']
                text = "Invalid Date! Please enter the correct date. "
                return elicit_slot(intent_request, session_attributes, 'dining_date', slots,text)
            return elicit_slot(intent_request, session_attributes, 'dining_time', slots)
        else:
            print("Print stmt",get_slot(intent_request, 'dining_date'), get_slot(intent_request, 'dining_time'), date, time)
            if ('interpretedValue' not in intent_request['sessionState']['intent']['slots']['dining_time']['value']  or ((get_slot(intent_request, 'dining_date') ==date and get_slot(intent_request, 'dining_time')< time))):  
                del slots['dining_time']
                text = "Invalid Time! Please enter the correct time. "
                return elicit_slot(intent_request, session_attributes, 'dining_time', slots,text)
             
        msg = send_sqs_message("chatBotQueue", slots)
        
        text = "You’re all set. Expect my suggestions shortly! Have a good day."
        message =  {
                'contentType': 'PlainText',
                'content': text
            }
        
        fulfillment_state = "Fulfilled"
        return close(intent_request, session_attributes, fulfillment_state, message)
    except Exception as e:
        print(f"Something went wrong. {e}")
    
def send_sqs_message(QueueName,msg_body):
    sqs_client = boto3.client('sqs')
    
    # sqs_queue_url = sqs_client.get_queue_url(QueueName=QueueName)['QueueUrl']
    sqs_queue_url = "https://sqs.us-east-1.amazonaws.com/590138386437/chatBotQueue"
    # print(sqs_queue_url)
    
    try:
        msg = sqs_client.send_message(QueueUrl=sqs_queue_url,MessageBody=json.dumps(msg_body))
    except ClientError as e:
        print("Error",e)
        return None
    return msg


def dispatch(intent_request):
    intent_name = intent_request['sessionState']['intent']['name']
    response = None
    return DiningIntent(intent_request)

def lambda_handler(event, context):
    response = dispatch(event)
    
    return response
