# %% [code]
import os
import sys
import json
import time
import threading
import subprocess
import importlib.metadata
import google.generativeai as genai
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

from kaggle.api.kaggle_api_extended import KaggleApi
# 初始化 Kaggle API
api = KaggleApi()
api.authenticate()

dataset_name = 'woolen/woolen8edc990443'
download_dir = '/kaggle/working/woolen8edc990443'
os.makedirs(download_dir, exist_ok=True)
api.dataset_download_files(dataset_name, path=download_dir, unzip=True)

# 設定基礎標題和其他配置
base_title = "Voice Task"
current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
kernel_id = "woolen/notebook8edc990443"  # 替換為你的 Kernel ID

# 創建帶有時間戳的標題
title_with_timestamp = f"{base_title}_{current_time}"

# 更新 kernel.json 的內容
kernel_config = {
    "id": kernel_id,
    "title": title_with_timestamp,
    "language": "python",
    "kernel_type": "script",
    "license": "mit",
    "tags": ["tag1", "tag2"],
    "enable_gpu": True,
    "enable_internet": True
}

# 保存 kernel.json 文件
kernel_json_path = os.path.join(download_dir, 'kernel.json')
with open(kernel_json_path, 'w') as f:
    json.dump(kernel_config, f, indent=4)

# 執行 kaggle kernels push 命令
push_command = ['kaggle', 'kernels', 'push', '-p', download_dir]

try:
    subprocess.run(push_command, check=True)
    print(f"Successfully pushed the kernel from {notebook_directory}")
except subprocess.CalledProcessError as e:
    print(f"Error occurred while pushing the kernel: {e}")

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
def fetch_data(content, history):
    try:
        # 假设 gemini.chat 是一个函数，可以处理内容并返回响应和情感
        if history == 'null':
            gemini = Gemini(history=[])
        else:
            gemini = Gemini(history=history)

        response, emotion, history = gemini.chat(content)
        
        return response, emotion, history
    except Exception as e:
        print("Error processing data with gemini.chat:", e)
        return None, None, None
    
# 定义数据变化处理函数
def on_data_change(event):
    global last_data_change_time
    if event.data:
        # 更新上次数据变化时间
        last_data_change_time = time.time()

        # 处理数据变动
        data = event.data
        if data.get('source') == 'JS':
            sound = data.get('sound')
            content = data.get('content')
            history = data.get('history')
            if content:
                response, emotion, history = fetch_data(content, history)
                if response:
                    write_data(event.path, response, emotion, history)
                    if sound:
                        # 检查 Kernel 状态
                        api = KaggleApi()
                        api.authenticate()
    
                        max_attempts = 60
                        attempts = 0
                        
                        while True:
                            try:
                                status = api.kernel_status('woolen', 'notebook8edc990443')
                                print(f"Kernel status: {status['status']}")
                                if status['status'] == 'complete':
                                    output = api.kernel_output('woolen', 'notebook8edc990443')
                                    print('output:',output)
                                    break
                                time.sleep(60)
                                attempts += 1 # 每分钟检查一次
                            except Exception as e:
                                print(f"An error occurred: {e}")
                                break


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
    def __init__(self, history):
        api_key = 'AIzaSyBtY513gNRPNRzyfrqYQFot11ixSGxeA2w'
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


# Example usage
if __name__ == "__main__":
    start_listener()
