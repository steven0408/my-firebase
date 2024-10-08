# %% [code]
import os
import sys
import json
import time
import threading
import subprocess
import importlib.metadata
import google.generativeai as genai
from datetime import datetime
from google.generativeai.types.generation_types import StopCandidateException

# Ensure required packages are installed
def ensure_package_installed(package_name, github_url=None):
    try:
        importlib.metadata.version(package_name)
        print(f"{package_name} is already installed.")
    except importlib.metadata.PackageNotFoundError:
        print(f"{package_name} not found. Installing...")
        if github_url:
            subprocess.run(["git", "clone", github_url], check=True)
            package_dir = github_url.split('/')[-1].replace('.git', '')
            subprocess.run([sys.executable, '-m', 'pip', 'install', f'./{package_dir}'], check=True)
        else:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package_name], check=True)

ensure_package_installed('firebase_admin')

# Import packages
try:
    import firebase_admin
    from firebase_admin import credentials, db, storage
except ImportError as e:
    print(f"Error importing firebase_admin: {e}")
    sys.exit(1)

# 设置环境变量
os.environ['KAGGLE_USERNAME'] = "woolen"
os.environ['KAGGLE_KEY'] = "5eed2f6ca0fcac029f78dea97cd20b0e"

import kaggle
from kaggle.api.kaggle_api_extended import KaggleApi
# 初始化 Kaggle API
api = KaggleApi()
api.authenticate()

# 設置數據集名稱和下載目錄
dataset_name = 'woolen/woolen8edc990443'
download_dir = '/kaggle/working/woolen8edc990443'

# 創建下載目錄（如果不存在的話）
os.makedirs(download_dir, exist_ok=True)

# 下載並解壓數據集
api.dataset_download_files(dataset_name, path=download_dir, unzip=True)

# Fetch the service account key JSON file contents
cred = credentials.Certificate('/kaggle/working/woolen8edc990443/adminsdk.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL':
    'https://woolen-firebase-test1-default-rtdb.firebaseio.com/'
})

# 设置空闲时间（秒）
IDLE_TIME_THRESHOLD = 1200  # 5 分钟

# 全局变量，用于存储上次数据变化时间
last_data_change_time = time.time()

# Reference to the database service
ref = db.reference('texts')

# Global variable to track if the listener is running
listener_running = False


def clear_database_if_idle():
    global last_data_change_time
    while True:
        current_time = time.time()
        if current_time - last_data_change_time >= IDLE_TIME_THRESHOLD:
            # 空闲时间超过阈值，清空数据库
            try:
                ref = db.reference('texts/')
                ref.delete()  # 清空指定路径的数据
                print("Database cleared due to inactivity.")
            except Exception as e:
                print("Error clearing database:", e)

            # 重置上次数据变化时间
            last_data_change_time = time.time()

        # 每隔一段时间检查一次
        time.sleep(300)


# Function to fetch data from Firebase
def fetch_data(content, history, charactor):
    try:
        # 假设 gemini.chat 是一个函数，可以处理内容并返回响应和情感
        if history == 'null':
            gemini = Gemini(history=[], charactor=charactor)
        else:
            gemini = Gemini(history=history, charactor=charactor)

        response, emotion, history = gemini.chat(content)
        
        return response, emotion, history
    except Exception as e:
        print("Error processing data with gemini.chat:", e)
        return None, None, None
    
# 定义数据变化处理函数
def on_data_change(event):
    global last_data_change_time
    global previous_sound  # 使用全局變量保存 sound
    global previous_charactor
    if event.data:
        # 更新上次数据变化时间
        last_data_change_time = time.time()

        # 处理数据变动
        data = event.data
        if data.get('source') == 'JS':
            # 如果 sound 是 None，則使用上次的 sound 值
            sound = data.get('sound')
            if sound is None:
                sound = previous_sound
            else:
                previous_sound = sound  # 更新 previous_sound
                
            charactor = data.get('charactor')
            if charactor is None:
                charactor = previous_charactor
            else:
                previous_charactor = charactor  # 更新 previous_sound
                
            content = data.get('content')
            history = data.get('history')
            if content:
                response, emotion, history = fetch_data(content, history, charactor)
                if response:
                    write_data(event.path, response, emotion, history)
                    print('sound: ', sound)
                    if sound:
                        max_attempts = 10
                        attempts = 0
                        
                        while attempts < max_attempts:
                            try:
                                # 設定基礎標題和其他配置
                                base_title = "Voice Task"
                                current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                kernel_id = "woolen/notebook8edc990443"  # 替換為你的 Kernel ID
                                
                                # 創建帶有時間戳的標題
                                title_with_timestamp = f"{base_title}_{current_time}"
                                
                                # 更新 kernel-metadata.json 的內容
                                kernel_config = {
                                    "id": "woolen/notebook8edc990443",
                                    "title": title_with_timestamp,
                                    "code_file": "notebook8edc990443.py",
                                    "language": "python",
                                    "kernel_type": "script",
                                    "license": "mit",
                                    "tags": ["tag1", "tag2"],
                                    "enable_gpu": True,
                                    "enable_internet": True
                                }
                                
                                # 保存 kernel.json 文件
                                kernel_json_path = os.path.join(download_dir, 'kernel-metadata.json')
                                with open(kernel_json_path, 'w') as f:
                                    json.dump(kernel_config, f, indent=4)
                                
                                # 執行 kaggle kernels push 命令
                                push_command = ['kaggle', 'kernels', 'push', '-p', download_dir]
                                result = subprocess.run(push_command, check=True, capture_output=True, text=True)
                                print(f"Successfully pushed the kernel from {download_dir}")
                                print(f"Command output: {result.stdout}")
                                break  # 成功后跳出循环
                            except subprocess.CalledProcessError as e:
                                attempts += 1
                                print(f"Error occurred while pushing the kernel (attempt {attempts}/{max_attempts}): {e}")
                                print(f"Command output: {e.output}")
                                print(f"Command stderr: {e.stderr}")
                                if attempts < max_attempts:
                                    print(f"Retrying in 30 seconds...")
                                    time.sleep(30)
                                else:
                                    print("Max retries reached. Giving up.")


def write_data(key, response, emotion, history):
    try:
        ref = db.reference(f'texts/{key}')
        ref.update({
            'content': response,
            'emotion': emotion,
            'source': 'python',
            'history': history
        })
        print(f"Data updated in Firebase at key: {key}")
    except Exception as e:
        print("Error updating data in Firebase:", e)


def start_listener():
    global listener_running
    if not listener_running:
        # 启动后台线程以监控空闲时间并清空数据库
        idle_monitor_thread = threading.Thread(target=clear_database_if_idle,
                                               daemon=True)
        idle_monitor_thread.start()

        print("Listening for new data...")
        ref.listen(on_data_change)
        listener_running = True
    else:
        print("Listener is already running.")
        

class Gemini:
    def __init__(self, history, charactor):
        api_key = 'AIzaSyBtY513gNRPNRzyfrqYQFot11ixSGxeA2w'
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.emotion_rule = [{"role": "user", "parts": "請判斷以下對話的情緒屬於下列哪一種 : [anger, disgust, fear, joy, neutral, others, pled, sadness, smug, surprise]，只需要回答框框內的文字"}]
        self.chat_history = history
        if (charactor == 'A'):
            self.chat_rule = [{"role": "user", "parts": "請使用女性友人的語氣和我對話，並盡量不要超過 100 字"}]
        elif (charactor == 'B'):
            self.chat_rule = [{"role": "user", "parts": "請使用男性友人的語氣和我對話，並盡量不要超過 100 字"}]

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


# Example usage
if __name__ == "__main__":
    start_listener()
