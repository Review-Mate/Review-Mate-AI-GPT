import json
import openai
import boto3
from sentence_completion import SentenceCompletion

def lambda_handler(event, context):
    sentence_completion = SentenceCompletion()
    responses = sentence_completion.generate_openai_response(event['body-json']['input_prompt'])
    
    return {
        'statusCode':200,
        'body': {
            # ensure_ascii : 한글 깨짐 방지
            'response' : json.dumps(responses, ensure_ascii = False)
        }
    }
    