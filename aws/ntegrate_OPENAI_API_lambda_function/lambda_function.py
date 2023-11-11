import json
import openai
import boto3
from generate_response import OpenAPIGenerateResponse

def lambda_handler(event, context):
    data = event['body-json']['input_prompt']
    oagr = OpenAPIGenerateResponse()
    response = oagr.generate_response(data)

    return {
        'statusCode':200,
        'body': response
    }