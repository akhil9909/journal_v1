import boto3
import json
import os
from botocore.exceptions import ClientError
import logging
from datetime import datetime
import uuid
import requests

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

#get dynamodb table name for promptops
def get_dynamodb_table_name_static_prompt():
    try:
        # Attempt to fetch the table name from environment variables (for production)
        table_name = os.environ['DYNAMODB_TABLE_STATIC_PROMPT']
        return table_name
    except KeyError:
        # If the environment variable is not set, default to a static name (for development)
        return 'dev_static_prompts' 

#get dynamodb table name for FILE_IDS_DYNAMODB_TABLE
def get_dynamodb_table_name_file_ids():
    try:
        # Attempt to fetch the table name from environment variables (for production)
        table_name = os.environ['FILE_IDS_DYNAMODB_TABLE']
        return table_name
    except KeyError:
        # If the environment variable is not set, default to a static name (for development)
        return 'file_ids_dev'

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

def fetch_thread_ids(assistant_id) -> list:
    try:
        table_name = get_dynamodb_table_name()
        table = dynamodb.Table(table_name)
        response = table.scan()
        items = response['Items']
        thread_ids = [item['thread_id'] for item in items if item.get('assistant') == assistant_id]
        return thread_ids
    except Exception as e:
        aws_log_error(f"Error fetching thread_ids for assistant {assistant_id}: {e}")
        return []

# get and add learning components

def get_and_add_learning_components(get_or_add,component_name,user_id):
    try:
        table_name = os.environ['LEARNING_COMPONENT_DYNAMODB_TABLE']
    except KeyError:
        table_name =  'learning_components_dev'
    table = dynamodb.Table(table_name)
    if get_or_add == 'get':
        response = table.scan()
        items = response['Items']
        component_names = [item['component_name'] for item in items if item['user_id'] == user_id]
        return component_names
    elif get_or_add == 'add':
        try: 
            current_date = datetime.now().strftime('%Y-%m-%d')
            user_component_name = user_id + '_' + component_name
            table.put_item(
                    Item={
                        'user_component_name': user_component_name,
                        'component_name': component_name,
                        'date_component': current_date,
                        'user_id': user_id
                    }
                )
            return True
        except Exception as e:
            aws_log_error(f"Error adding learning component: {e}")
            return False

#Brene Brown Bare Footed Coach todo
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
    
def update_promptops_entry_to_DB(uuid_promptops, some_date_value, updated_description,do_not_stage_value,updated_title,changed_type):
    try:
        table_name = get_dynamodb_table_name_promptops()
        table = dynamodb.Table(table_name)
        table.update_item(
            Key={
            'date_promptops': some_date_value,  # Replace 'some_date_value' with the actual date value
            'uuid_promptops': uuid_promptops
            },
            UpdateExpression="SET description = :d, do_not_stage = :e, title = :t, #ty = :ty",
            ExpressionAttributeNames={
                '#ty': 'type'
            },
            ExpressionAttributeValues={
            ':d': updated_description,
            ':e': do_not_stage_value,
            ':t': updated_title,
            ':ty': changed_type
            }
        )
        return True  # Indicate success
    except Exception as e:
        aws_log_error(f"Error updating promptops entry: {e}")
        return False  # Indicate failure
######
def fetch_static_prompts_from_DB() -> list:
    sorted_items = []
    try:
        table_name = get_dynamodb_table_name_static_prompt()
        table = dynamodb.Table(table_name)
        response = table.scan()
        items = response['Items']        
    except ClientError as e:
        aws_log_error(f"Error fetching static prompts: {e}")
        raise e
    return items
######
def update_static_prompt_to_DB(title,description):
    try:
        table_name = get_dynamodb_table_name_static_prompt()
        table = dynamodb.Table(table_name)
        table.update_item(
            Key={
            'title': title
            },
            UpdateExpression="SET description = :d",
            ExpressionAttributeValues={
            ':d': description
            }
        )
        return True  # Indicate success
    except Exception as e:
        aws_log_error(f"Error updating static prompts: {e}")
        return False  # Indicate failure


######

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

def download_and_save_image(image_url, component_name, user_id, img_prompt_text, summ_text):
    try: 
        image_response = requests.get(image_url)
        image_binary = image_response.content  # This will store the binary content of the image
    except Exception as e:
        raise e
        aws_log_error(f"Error downloading image: {e}")
        return False  # Indicate failure
    
    try:
        table_name = os.environ.get('IMAGE_METADATA_DYNAMODB_TABLE', 'image_metadata_dev')
        table = dynamodb.Table(table_name)
    except Exception as e:
        raise e
        aws_log_error(f"Error fetching image metadata table: {e}")
        return False
    
    try:
        s3 = boto3.client('s3')
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'streamlit-dev-bucket')
        image_filename = f"{user_id}/{component_name}/{uuid.uuid4()}.jpg"
        s3.put_object(Bucket=bucket_name, Key=image_filename, Body=image_binary, ContentType='image/jpeg')
        table.put_item(
            Item={
                'image_url': image_filename,
                'component_name': component_name,
                'user_id': user_id,
                'date_uploaded': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summarized_text': summ_text,
                'image_prompt_text': img_prompt_text
            }
        )
        return True
    except Exception as e:
        raise e
        aws_log_error(f"Error saving image to S3: {e}")
        return False
    
def fetch_image_metadata(component_name, user_id):
    try:
        table_name = os.environ.get('IMAGE_METADATA_DYNAMODB_TABLE', 'image_metadata_dev')
        table = dynamodb.Table(table_name)
        response = table.scan()
        items = response['Items']
        filtered_items = [item for item in items if item['component_name'] == component_name and item['user_id'] == user_id and item.get('delete_request') != 'delete']
        return [item['image_url'] for item in filtered_items]
    except Exception as e:
        aws_log_error(f"Error fetching image metadata: {e}")
        return []

def delete_image_metadata(image_url):
    try:
        table_name = os.environ.get('IMAGE_METADATA_DYNAMODB_TABLE', 'image_metadata_dev')
        table = dynamodb.Table(table_name)
        table.update_item(
            Key={
                'image_url': image_url
            },
            UpdateExpression="SET delete_request = :d",
            ExpressionAttributeValues={
                ':d': 'delete'
            }
        )
        return True
    except Exception as e:
        aws_log_error(f"Error deleting image metadata: {e}")
        return False

def generate_presigned_url(image_url):
    try:
        s3 = boto3.client('s3')
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'streamlit-dev-bucket')
        signed_url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': image_url}, ExpiresIn=3600)
        return signed_url
    except Exception as e:
        aws_log_error(f"Error creating signed image URL: {e}")
        return None

def save_file_ids(file_id, assistant_id, assistant_name,file_name):
    try:
        table_name = os.environ.get('FILE_IDS_DYNAMODB_TABLE', 'file_ids_dev')
        table = dynamodb.Table(table_name)
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        table.put_item(
            Item={
                'file_id': file_id,
                'file_name': file_name,
                'assistant_id': assistant_id,
                'assistant_name': assistant_name,
                'date_uploaded': current_date,
                'datetime_uploaded': current_datetime
            }
        )
        return True
    except Exception as e:
        aws_log_error(f"Error saving file IDs: {e}")
        return False

def delete_file_id(file_id):
    try:
        table_name = os.environ.get('FILE_IDS_DYNAMODB_TABLE', 'file_ids_dev')
        table = dynamodb.Table(table_name)
        table.update_item(
            Key={
                'file_id': file_id
            },
            UpdateExpression="SET delete_flag = :d",
            ExpressionAttributeValues={
                ':d': True
            }
        )
        return True
    except Exception as e:
        aws_log_error(f"Error setting delete_flag for file ID: {e}")
        return False

def fetch_file_ids(assistant_id):
    try:
        table_name = os.environ.get('FILE_IDS_DYNAMODB_TABLE', 'file_ids_dev')
        table = dynamodb.Table(table_name)
        response = table.scan()
        items = response['Items']
        filtered_items = [item for item in items if item.get('assistant_id') == assistant_id and item.get('delete_flag') != True]
        return [item['file_id'] for item in filtered_items]
    except Exception as e:
        aws_log_error(f"Error fetching file IDs: {e}")
        return []
    
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



# def fetch_static_prompts_from_DB() -> list:
#     sorted_items = []
#     try:
#         table_name = get_dynamodb_table_name_static_prompt()
#         table = dynamodb.Table(table_name)
#         response = table.scan()
#         items = response['Items']
        
#         # Ensure 'description' key exists in items before sorting
#         items_with_description = [item for item in items if 'description' in item]
#         # Filter items by description is not null
#         filtered_items = [item for item in items_with_description if item.get('description') not in [None, '']]
#         # Sort items by title in ascending order
#         sorted_items = sorted(filtered_items, key=lambda x: x['title'], reverse=False)
#     except ClientError as e:
#         aws_log_error(f"Error fetching static prompts: {e}")
#         raise e
#     return sorted_items