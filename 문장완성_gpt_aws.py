import os
import openai
import json

# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import boto3
from botocore.exceptions import ClientError

# secret manager에서 openai api key 가져오는 코드
def get_secret():

    secret_name = "openai_api_key_20231012"
    region_name = "ap-northeast-2"

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

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    
    # Your code goes here.
    return secret

class TopicRecommendation:
    def __init__(self):
        self.model, self.temperature, self.max_tokens, self.base_message = self.set_gpt_model_parameters()
    
    # gpi api parameters
    def set_gpt_model_parameters(self):
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.2
        self.max_tokens = 2048
        self.base_message = [{"role": "system",
                              "content": """A Korean traveler is writing a review written in Korean. 
                                            All you have to do is look at the reviews that have been written so far, 
                                            and recommend topics that you think would be good to come in next. 
                                            The subject should recommend two things. 
                                            Since the review will be written in Korean, 
                                            the answer should be in Korean as well."""}]
        
        return self.model, self.temperature, self.max_tokens, self.base_message
    
    # content 입력받아서 gpt api에 전달
    def generate_openai_response(self, content):
        # prompt message
        messages = self.base_message + [{"role": "user", "content": content}]
        response = openai.ChatCompletion.create(
            model = self.model,
            messages = messages,
            temperature = self.temperature,
            max_tokens = self.max_tokens
        )
        return response["choices"][0]["message"]["content"]
        
        
def lambda_handler(event, context):
    secret = get_secret()
    secret_data = json.loads(secret)
    openai.api_key = secret_data['OPENAI_API_KEY']
    
    review = json.loads(event.get('reviews'))

    # openai api 호출
    topic_recommendation = TopicRecommendation()
    #responses = topic_recommendation.generate_openai_response(review)
    responses = topic_recommendation.generate_openai_response("샘플 문장")

    return {
        #'openai_api_key': openai.api_key,
        #'responses': responses,
        #'message' : message,
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }