import json
import openai
import boto3
from topic_recommendation import TopicRecommendation

def lambda_handler(event, context):
    topic_recommendation = TopicRecommendation()
    responses = topic_recommendation.generate_openai_response(event['body-json']['input_prompt'])
    
    return {
        'statusCode':200,
        'body': {
            # ensure_ascii : 한글 깨짐 방지
            'response' : json.dumps(responses, ensure_ascii = False)
        }
    }
    