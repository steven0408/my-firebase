import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

try:
    import firebase_admin
except ImportError:
    install('firebase_admin')
    import firebase_admin

import time
import threading
import firebase_admin
from firebase_admin import credentials, db
from chatAI import Gemini

# Fetch the service account key JSON file contents
root = ''
cred = credentials.Certificate(root + 'adminsdk.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://woolen-firebase-test1-default-rtdb.firebaseio.com/'
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
        if data.get('source') != 'python':
            content = data.get('content')
            history = data.get('history')
            print("Data", data)
            if content:
                response, emotion, history = fetch_data(content, history)
                if response:
                    write_data(event.path, response, emotion, history)

def write_data(key, response, emotion, history):
    try:
        ref = db.reference(f'texts/{key}')
        ref.update({
            'content': response ,
            'emotion': emotion ,
            'source': 'python' ,
            'history': history
        })
        print(f"Data updated in Firebase at key: {key}")
    except Exception as e:
        print("Error updating data in Firebase:", e)

def start_listener():
    global listener_running
    if not listener_running:
        # 启动后台线程以监控空闲时间并清空数据库
        idle_monitor_thread = threading.Thread(target=clear_database_if_idle, daemon=True)
        idle_monitor_thread.start()

        print("Listening for new data...")
        ref.listen(on_data_change)
        listener_running = True
    else:
        print("Listener is already running.")

# Example usage
if __name__ == "__main__":

    start_listener()
