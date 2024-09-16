import boto3
import json
import os
from botocore.exceptions import ClientError

#aws_access_key_id = os.getenv('AWS_ACCESS_KEY')
#aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

# Initialize a session using Amazon DynamoDB
dynamodb = boto3.resource('dynamodb')

# Insert a new item or update an existing item
def save_chat_history(thread_id, assistant_id, user_prompt, chat_history):
    try:
        table = dynamodb.Table('streamlit_backend')
        table.put_item(
            Item={
                'thread_id': thread_id,
                'assistant': assistant_id,
                'prompt': user_prompt,
                'history': chat_history
            }
        )
        return True  # Indicate success
    except Exception as e:
        print(f"Error saving chat history: {e}")  # Log the error for debugging
        return False  # Indicate failure
    

def get_openai_api_key():

    secret_name = "OPENAI_API_KEY"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager'
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret_data = get_secret_value_response['SecretString']
    secret_dict = json.loads(secret_data)  # Parse the JSON string
    openai_api_key_res = secret_dict['OPENAI_API_KEY'] 
    return openai_api_key_res

def get_credentials():

    secret_name = "streamlit_credentials"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']
    return secret