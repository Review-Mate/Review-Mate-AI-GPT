import os
import re
import openai
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

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
    
if __name__ == "__main__":
    content = "조식과 석식을 호텔에서 먹었는데"
    topic_recommendation = TopicRecommendation()
    responses = topic_recommendation.generate_openai_response(content)
    print(responses)