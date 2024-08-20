import google.generativeai as genai
from google.generativeai.types.generation_types import StopCandidateException
import os

class Gemini:
    def __init__(self, history):
        api_key = 'AIzaSyBflo5s9osZ4JkvdC5wtHmm1niWgmEEiII'
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.chat_rule = [{"role": "user", "parts": "請使用女性友人的語氣和我對話"}]
        self.emotion_rule = [{"role": "user", "parts": "請判斷以下對話的情緒屬於下列哪一種 : [喜, 怒, 哀, 樂, 中性]，只需要回答框框內的文字"}]
        self.chat_history = history

    def chat(self, message):
        while True:
            try:
                # 创建一个新的聊天会话
                chat_session = self.model.start_chat(history=self.chat_rule + self.chat_history)
                response = chat_session.send_message(message)

                # 更新聊天历史
                # self.chat_history.append({"role": "user", "parts": message})
                self.chat_history.append({"role": "model", "parts": response.text})
                self.remove_first_if_long(self.chat_history)
                
                # 创建一个新的情绪检测会话
                emotion_session = self.model.start_chat(history=self.emotion_rule + [{"role": "model", "parts": response.text}])
                emotion_res = emotion_session.send_message(response.text)

                return response.text, emotion_res.text, self.chat_history

            except genai.types.generation_types.StopCandidateException:
                # 处理异常并继续尝试发送消息
                continue
    
    def remove_first_if_long(self, list):
        if len(list) > 10:
            list.pop(0)
            list.pop(0)
        return list
