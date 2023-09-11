import os
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

def gpt_model_parameters():
    model = "gpt-3.5-turbo"
    temperature = 0.2
    max_tokens = 2048
    return model, temperature, max_tokens

base_message = [{"role": "system",
             "content": """The reviewer will enter the review they are writing.
This sentence is an incomplete sentence and all korean text.
A reviewer is korean, so you have to answer with korean.
If You have to figure out the context of the sentence and complete the rest of the sentence.
If the context requires a negative sentence, you must complete one negative sentence.
Conversely, if the context is positive, you must complete one positive sentence.
If you can't decide whether it's positive or negative, you need to complete two sentences, one positive and one negative.
You have to read the reviewer's review and write it by following the tone of the reviewer. 

This is some examples.
<format>
{
    "input" : "조식과 석식을 호텔에서 먹었는데"
  "results" : [
    {"긍정적", "조식과 석식을 호텔에서 먹었는데 맛과 다양성 모두 훌륭했습니다."},
    {"부정적", "조식과 석식을 호텔에서 먹었는데 식사 퀄리티가 기대에 미치지 않았습니다."}
  ]
},
{
    "input" : "침대에서 이상한 냄새가 나고"
    "results" : [
        {"부정적", "침대에서 이상한 냄새가 나고 불편했습니다."}
    ]
}
"""}]

def generate_openai_response(base_message, content):
    model, temperature, max_tokens = gpt_model_parameters()
    # prompt message
    messages = base_message + [{"role": "user", "content": content}]
    response = openai.ChatCompletion.create(
        model = model,
        messages = messages,
        temperature = temperature,
        max_tokens = max_tokens
    )
    return response["choices"][0]["message"]["content"]

## response 후처리
"""
답변 형태 1) '<format>\n{\n  "results" : [\n    {"긍정적", "바다가 보이는 60층 숙소에 묵었는데 풍경이 너무 아름다웠습니다."},\n    {"부정적", "바다가 보이는 60층 숙소에 묵었는데 풍경이 기대에 미치지 않았습니다."}\n  ]\n}'
답변 형태 2) '긍정적: 바다가 보이는 60층에 묵었는데 풍경이 너무 아름다웠습니다.\n부정적: 바다가 보이는 60층에 묵었는데 전망이 기대에 미치지 않았습니다.'
답변 형태 3) '부정적: 침대가 너무 더러웠고 청결하지 않았습니다.'
"""
def response_postprocessing(responses):
    # 형태 1
    if 'format' in responses:
        pattern = r'{"(긍정적|부정적)", "(.*?)"}'
        matches = re.findall(pattern, responses)
        if matches:
            result_dict = {key : value for key, value in matches}
        return result_dict
    # 형태 2, 3
    elif ':' in responses:
        responses = responses.split('\n')
        result_dict = {}
        for response in responses:
            response = response.split(':')
            if len(response) == 2:
                result_dict[response[0]] = response[1].strip()
        return result_dict