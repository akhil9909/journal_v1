import boto3
import json
import os
from botocore.exceptions import ClientError
import logging
from datetime import datetime

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


def aws_log_error(message):
    aws_error_log.append(message)
    logging.error(message)


# Initialize a session using Amazon DynamoDB
dynamodb = boto3.resource('dynamodb')

# Insert a new item or update an existing item
def save_chat_history(thread_id, assistant_id, user_prompt, chat_history,Boolean_Flag_to_Update_Chat_History):
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
                UpdateExpression="SET prompt = :p, history = :h, #d = :d, #dt = :dt",
                ExpressionAttributeNames={
                    '#d': 'date',
                    '#dt': 'datetime'
                },
                ExpressionAttributeValues={
                ':p': user_prompt,
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