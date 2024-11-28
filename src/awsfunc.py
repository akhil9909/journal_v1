import boto3
import json
import os
from botocore.exceptions import ClientError
import logging
from datetime import datetime
import uuid

#aws_access_key_id = os.getenv('AWS_ACCESS_KEY')
#aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

# Configure logging
aws_error_log = []

# Get the name of the DynamoDB table
def get_dynamodb_table_name():
    try:
        # Attempt to fetch the table name from environment variables (for production)
        table_name = os.environ['DYNAMODB_TABLE']
        return table_name
    except KeyError:
        # If the environment variable is not set, default to a static name (for development)
        return 'streamlit_backend'

#get dynamodb table name for promptops
def get_dynamodb_table_name_promptops():
    try:
        # Attempt to fetch the table name from environment variables (for production)
        table_name = os.environ['DYNAMODB_TABLE_PROMPTOPS']
        return table_name
    except KeyError:
        # If the environment variable is not set, default to a static name (for development)
        return 'dev_promptops' 


def aws_log_error(message):
    aws_error_log.append(message)
    logging.error(message)


# Initialize a session using Amazon DynamoDB
dynamodb = boto3.resource('dynamodb')

# Insert a new item or update an existing item
def save_chat_history(thread_id, assistant_id, user_prompt, chat_history, Boolean_Flag_to_Update_Chat_History):
    try:
        table_name = get_dynamodb_table_name()
        table = dynamodb.Table(table_name)
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if Boolean_Flag_to_Update_Chat_History:
            table.update_item(
                Key={
                'thread_id': thread_id
                },
                UpdateExpression="SET history = :h,  #d = :d, #dt = :dt",
                ExpressionAttributeNames={
                    '#d': 'date',
                    '#dt': 'datetime'
                },
                ExpressionAttributeValues={
                ':h': chat_history,
                ':d': current_date,
                ':dt': current_datetime
                }
            )
            return True
        else:
            table.put_item(
                Item={
                    'thread_id': thread_id,
                    'assistant': assistant_id,
                    'prompt': user_prompt,
                    'history': chat_history,
                    'date': current_date,
                    'datetime': current_datetime
                }
            )
            return True  # Indicate success
    except Exception as e:
        aws_log_error(f"Error saving chat history: {e}")
        return False  # Indicate failure
    

def get_openai_api_key():

    secret_name = "OPENAI_API_KEY"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager'
        )

        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    try:
        secret_data = get_secret_value_response['SecretString']
    except KeyError:
        aws_log_error("SecretString not found")
        return None
    
    try:
        secret_dict = json.loads(secret_data)  # Parse the JSON string
        openai_api_key_res = secret_dict['OPENAI_API_KEY'] 
    except json.JSONDecodeError as e:
        aws_log_error(f"Error decoding JSON: {e}")
        return None
    
    return openai_api_key_res

def get_credentials():
    
    secret_name = "streamlit_credentials"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e
    
    secret = get_secret_value_response['SecretString']
    return secret

def save_feedback(thread_id, assistant_id, assistant_response, feedback,other_feedback):
    try:
        table_name = get_dynamodb_table_name()
        table = dynamodb.Table(table_name)
        table.update_item(
            Key={
            'thread_id': thread_id,
            },
            UpdateExpression="SET assistant_response = :ar, feedback = :fb, other_feedback = :of",
            ExpressionAttributeValues={
            ':ar': assistant_response,
            ':fb': feedback,
            ':of': other_feedback
            }
        )
        return True  # Indicate success
    except Exception as e:
        aws_log_error(f"Error saving feedback: {e}")
        return False  # Indicate failure
    


def fetch_conversations() -> list:
    sorted_items = []
    try:
        table_name = get_dynamodb_table_name()
        table = dynamodb.Table(table_name)        
        response = table.scan()
        items = response['Items']
        
        # Ensure 'date' key exists in items before sorting
        items_with_date = [item for item in items if 'date' in item]
        # Sort items by date in descending order and get the last 10 conversations
        sorted_items = sorted(items_with_date, key=lambda x: x['date'], reverse=True)[:50]
        
    except ClientError as e:
        aws_log_error(f"Error fetching conversations: {e}")
        raise e
    return sorted_items

#in this function below, a default value of False is set for do_not_stage_flag. 
#this is interesting beacuase, its not part of function callm so if we change the default value, we need to change the function call as well.
#it is also difficult to guess because do not stage is not part of the ui where this function is called.
# this is a bad practice.
# we should either handle default values as separate dictionary with descriotion about where used - like session states issues.
# Simialr to session states, we should also track the lineage of deafult values.
#we should also track the calls to dynamodb to make sure we dont miss in these changes
#ideally, tracking ui elements, wrt session state, and data flows , and as well as dynamodb calls, and default values should be tracked in a single place.
#should this be a part of testing strategy? like session state changes test between navigations.
def save_new_promptops_entry_to_DB(title, description,type):
    try:
        table_name = get_dynamodb_table_name_promptops()
        table = dynamodb.Table(table_name)
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        uuid_promptops = str(uuid.uuid4())
        table.put_item(
                Item={
                    'date_promptops': current_date,
                    'uuid_promptops': uuid_promptops,
                    'datetime_promptops': current_datetime,
                    'type': type,
                    'title': title,
                    'description': description,
                    'do_not_stage': False
                }
            )
        return True
    except Exception as e:
        aws_log_error(f"Error saving new promptops entry while updating {type}: {e}")
        return False
    #date_promptops partition
    #uuid_promptops  sort key
    #type .. entry as todo or staging etc
    #title
    #descriotion

def get_promptops_entries(type) -> list:
    sorted_items = []
    try:
        table_name = get_dynamodb_table_name_promptops()
        table = dynamodb.Table(table_name)
        response = table.scan()
        items = response['Items']
        
        # Ensure 'datetime_promptops' key exists in items before sorting
        items_with_datetime = [item for item in items if 'datetime_promptops' in item]
        # Filter items by type and ensure description is not null
        filtered_items = [item for item in items_with_datetime if item['type'] == type and item.get('description') not in [None, '']]
        # Sort items by datetime in descending order and get the last 50 entries
        sorted_items = sorted(filtered_items, key=lambda x: x['datetime_promptops'], reverse=True)[:50]
    except ClientError as e:
        aws_log_error(f"Error fetching topic_entries_for_{type}: {e}")
        raise e
    return sorted_items
    
def update_promptops_entry_to_DB(uuid_promptops, some_date_value, updated_description,do_not_stage_value):
    try:
        table_name = get_dynamodb_table_name_promptops()
        table = dynamodb.Table(table_name)
        table.update_item(
            Key={
            'date_promptops': some_date_value,  # Replace 'some_date_value' with the actual date value
            'uuid_promptops': uuid_promptops
            },
            UpdateExpression="SET description = :d, do_not_stage = :e",
            ExpressionAttributeValues={
            ':d': updated_description,
            ':e': do_not_stage_value
            }
        )
        return True  # Indicate success
    except Exception as e:
        aws_log_error(f"Error updating promptops entry: {e}")
        return False  # Indicate failure

def delete_promptops_entry_from_DB(uuid_promptops, some_date_value):
    try:
        table_name = get_dynamodb_table_name_promptops()
        table = dynamodb.Table(table_name)
        table.delete_item(
            Key={
            'date_promptops': some_date_value,  # Replace 'some_date_value' with the actual date value
            'uuid_promptops': uuid_promptops
            }
        )
        return True  # Indicate success
    except Exception as e:
        aws_log_error(f"Error deleting promptops entry: {e}")
        return False  # Indicate failure


# def update_db_doNOT_stage_flag(uuid_promptops,date_promptops,do_not_stage_flag):
#     try:
#         table_name = get_dynamodb_table_name_promptops()
#         table = dynamodb.Table(table_name)
#         table.update_item(
#             Key={
#             'date_promptops': date_promptops,
#             'uuid_promptops': uuid_promptops
#             },
#             UpdateExpression="SET do_not_stage = :d",
#             ExpressionAttributeValues={
#             ':d': do_not_stage_flag
#             }
#         )
#         return True  # Indicate success
#     except Exception as e:
#         aws_log_error(f"Error updating do_not_stage flag: {e}")
#         return False  # Indicate failure