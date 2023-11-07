import os
import re
import openai
import json
import boto3

def get_api_key():
    lambda_client = boto3.client('lambda', region_name='ap-northeast-2')
    response = lambda_client.invoke(
            FunctionName = 'arn:aws:lambda:ap-northeast-2:811439093840:function:openai_get_api_key',
            InvocationType = 'RequestResponse'
        )

    openai_api_key = json.load(response['Payload'])['body']['api_key']
    return openai_api_key

openai.api_key = get_api_key()

class OpenAPIGenerateResponse:
    def __init__(self) -> None:
        
        self.base_message = [
            {"role": "system", "content": "Take Korean travel review data as input and perform the following tasks based on whether the given text's last sentence is complete:"},
            {"role": "system", "content": """1. If the last sentence is complete:
            - Analyze the review and provide recommendations for topics that could be added to the review."""},
            {"role": "system", "content": "This is an example of a topic recommendation."},
            
            {"role": "system", "content": "If the last sentence is complete, Please follow this format: {'sort' : 1, 'results': '<result text>'}"},
            {"role": "user", "content": "위치도 좋고 깨끗한 호텔이었어요. 다만, 조식이 너무 단순해서 아쉬웠어요."},
            {"role": "assistant", "content": "{'sort' : 1, 'results': '조식이 어땠는지 조금 더 자세히 작성해 주실 수 있을까요?'}"},
            {"role": "user", "content": "청소가 제대로 되어 있지 않았어요."},
            {"role": "assistant", "content": "{'sort' : 1, 'results': '그래도 다른 좋은 점이 있었나요?'}"},
            {"role": "user", "content": "위치도 양재역과 매우 가까워서 좋았고, 직원분들도 친절하셨어요."},
            {"role": "assistant", "content": "{'sort' : 1, 'results': '음식이나 청소 상태 등 다른 부분은 어땠나요?'}"},

            
            {"role": "system", "content": """2. If the last sentence is incomplete:
            - Complete the unfinished sentence.
            If You have to figure out the context of the sentence and complete the rest of the sentence.
            If the context requires a negative sentence, you must complete one negative sentence.
            Conversely, if the context is positive, you must complete one positive sentence.
            If you can't decide whether it's positive or negative, you need to complete two sentences, one positive and one negative."""},
            {"role": "system", "content": "This is an example of sentence completion."},
            {"role": "system", "content": "If the last sentence is incomplete, Please follow this format: {'sort' : 2, 'last sentence': '<last sentence text>', 'polarity': ['POS', 'NEG'], 'results': ['<result text1>', '<result text2>']}"},
            
            {"role": "user", "content": "위치도 좋고 깨끗한 호텔이었어요. 다만 조식을 먹으러 갔는데"},
            {"role": "assistant", "content": "{'sort' : 2, 'last sentence': '다만 조식을 먹으러 갔는데', 'polarity' : ['NEG'], 'results': ['음식이 너무 단순해서 아쉬웠어요.']}"},
            {"role": "user", "content": "방이 정말 깨끗했어요. 특히"},
            {"role": "assistant", "content": "{'sort' : 2, 'last sentence': '특히', 'polarity' : ['POS'], 'results': ['화장실이 깨끗해서 좋았어요.']}"},
            {"role": "user", "content": "호텔 방 밖으로"},
            {"role": "assistant", "content": "{'sort' : 2, 'last sentence': '호텔 방 밖으로', 'polarity' : ['POS', 'NEG'], 'results': ['보이는 경치가 너무 좋았어요.', '뷰가 정말 별로여서 아쉬웠어요.']}"},

            {"role": "system", "content": "If the input is not in Korean, please handle it as an exception and provide an appropriate response or error message."},
            {"role": "user", "content": "what a nice hotel!"},
            {"role": "assistant", "content": "I'm sorry, but this model only supports Korean language input. Please provide your input in Korean."},

            
            
        ]

    def generate_response(self, content):
        response = self.create_openai_response(content)
        json_response = self.response_to_json(response)
        print("json_response: ", json_response)
        # topic recommendation 인 경우
        if json_response['sort'] == 1:
            return json_response
        # sentence completion 인 경우
        elif json_response['sort'] == 2:
            return self.sentence_completion_postprocessing(content, json_response)
        else:
            assert False, "sort 값이 1 또는 2가 아닙니다."
    
    def topic_recommendation_postprocessing(self, json_response):
        json_response['content'] = json_response['results']
        del json_response['results']
        return [json_response]
    
    def sentence_completion_postprocessing(self, content, json_response):
        # 마지막 문장이 '?'로 끝나는 경우, topic recommendation으로 처리
        # 주제 추천인데 gpt가 sort값을 2로 반환하는 경우가 있음
        if json_response['results'][0][-1] == '?':
            json_response['sort'] = 1
            del json_response['last sentence']
            del json_response['polarity']
            json_response['results'] = json_response['results'][0]
            return self.topic_recommendation_postprocessing(json_response)

        ret = []

        # content에서 마지막 문장의 인덱스 찾기
        last_sentence_start_index = content.find(json_response['last sentence'])
        last_sentence_end_index = -1
        json_response['idx'] = [last_sentence_start_index, last_sentence_end_index]

        # POS, NEG 라벨 0, 1로 변경
        for i in json_response['polarity']:
            if i == 'POS':
                json_response['polarity'][json_response['polarity'].index(i)] = 0
            elif i == 'NEG':
                json_response['polarity'][json_response['polarity'].index(i)] = 1
            else:
                assert False, "polarity 값이 POS 또는 NEG가 아닙니다."

        # results가 여러 개인 경우, ret에 각각을 분할해서 저장
        for i in range(len(json_response['results'])):
            tmp_json = {}
            tmp_json['sort'] = json_response['sort']
            tmp_json['idx'] = json_response['idx']
            tmp_json['polarity'] = json_response['polarity'][i]
            tmp_json['content'] = json_response['results'][i]
            ret.append(tmp_json)

        return ret

    def create_openai_response(self, content):
        response = openai.ChatCompletion.create(
            model = 'gpt-3.5-turbo',
            messages = self.base_message + [{
                "role" : "user",
                "content" : content
            }],
            temperature = 0.2,
            max_tokens = 150
        )
        return response.choices[0]["message"]["content"]
    
    def response_to_json(self, content):
        # json 형태로 변환
        response_content = content
        response_content = response_content.replace("'", '"')
        response_content = response_content.replace("True", 'true')
        response_content = response_content.replace("False", 'false')
        response_content = response_content.replace("None", 'null')
        json_response = json.loads(response_content)
        return json_response
    
        