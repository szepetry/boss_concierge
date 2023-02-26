import boto3
import random

# Define the client to interact with Lex
client = boto3.client('lexv2-runtime')

def lambda_handler(event, context):
    cuisine_option_type = ['chinese', 'indian', 'american', 'mexican', 'italian', 'french', 'thai']
    botId = 'PGZVV04QIS'
    botAliasId = 'EMEVGP74CE'
    localeId = 'en_US'
    sessionId = 'testuser'
    
    print(event)

    msg_from_user = event['messages'][0]['unstructured']['text']
    # msg_from_user = "Hello"

    print(f"Message from frontend: {msg_from_user}")
    
    bot_session = client.put_session(
        botId=botId, 
        botAliasId=botAliasId, 
        localeId=localeId, 
        sessionId=sessionId,
        sessionState={}
    )
    if bot_session:
        bot_session = client.get_session(
            botId=botId, 
            botAliasId=botAliasId, 
            localeId=localeId, 
            sessionId=sessionId)
    else:
        return {
        'statusCode': 200,
        'messages': [{
            'type': 'unstructured',
            'unstructured': {
                'text': 'There was an error. Please try again later!'
            }
        }]
    }
    
    print(msg_from_user)
    print(bot_session)
    
    # if bot_session['recentIntentSummaryView']:
    #     current_dialog_action = bot_session['recentIntentSummaryView'][0]['dialogActionType']
    #     if current_dialog_action == 'ElicitSlot':
    #         slot_to_draw_out = bot_session['recentIntentSummaryView'][0]['slotToElicit']
    #         if slot_to_draw_out == 'cuisine':
    #             if not data.lower() in cuisine_option_type:
    #                 return {
    #                     'statusCode': 200,
    #                     'messages': [{
    #                         'type': 'unstructured',
    #                         'unstructured': {
    #                             'text': 'I request you to kindly select from the following options: ' + ', '.join(cuisine_option_type)
    #                         }
    #                     }]
    #                 }

    # Initiate conversation with Lex
    response = client.recognize_text(
        botId=botId, 
        botAliasId=botAliasId, 
        localeId=localeId, 
        sessionId=sessionId, 
        text=msg_from_user)
        
    print(f"Response: {response}")
    msg_from_lex = response.get('messages', [])
    if msg_from_lex:
        
        print(f"Message from Chatbot: {msg_from_lex[0]['content']}")
        print(response)
        resp = {
            'statusCode': 200,
            'messages': [{
                'type': 'unstructured',
                'unstructured': {
                    'text': str(msg_from_lex[0]['content'])
                }
            }]
        }

        return resp

# import boto3
# import random

# # Define the client to interact with Lex
# client = boto3.client('lexv2-runtime')

# def lambda_handler(event, context):
#     botId = 'PGZVV04QIS'
#     botAliasId = 'EMEVGP74CE'
#     localeId = 'en_US'
#     sessionId = str(random.randint(0, 100000))

#     msg_from_user = event['messages'][0]['unstructured']['text']

#     # change this to the message that user submits on 
#     # your website using the 'event' variable
#     # msg_from_user = "Hello"

#     print(f"Message from frontend: {msg_from_user}")

#     # Initiate conversation with Lex
#     response = client.recognize_text(
#             botId=botId, # MODIFY HERE
#             botAliasId=botAliasId, # MODIFY HERE
#             localeId=localeId,
#             sessionId=sessionId,
#             text=msg_from_user)
    
#     print(f"Response: {response}")
#     msg_from_lex = response.get('messages', [])
#     if msg_from_lex:
        
#         print(f"Message from Chatbot: {msg_from_lex[0]['content']}")
#         print(response)
#         resp = {
#             'statusCode': 200,
#             'messages': [{
#                 'type': 'unstructured',
#                 'unstructured': {
#                     'text': str(msg_from_lex[0]['content'])
#                 }
#             }]
#         }

#         return resp
