import firebase_admin
from firebase_admin import credentials, db

# Fetch the service account key JSON file contents
cred = credentials.Certificate('adminsdk.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://woolen-firebase-test1-default-rtdb.firebaseio.com/'
})

# Reference to the database service
ref = db.reference('texts')

# Function to fetch data from Firebase
def fetch_data():
    data = ref.get()
    if data:
        for key, value in data.items():
            print(f"Key: {key}, Content: {value['content']}")
    else:
        print("No data found")

# 定义数据变化处理函数
def on_data_change(event):
    if 'source' in event.data and event.data['source'] == 'python':
    return
    # if event.event_type == 'put':  # 数据写入事件
    #     print('Data updated:', event.data)
    # elif event.event_type == 'patch':  # 部分数据更新事件
    #     print('Data patched:', event.data)
    fetch_data()

# 读取现有数据
def initialize():
    print("Existing data:")
    fetch_data()

def write_data(new_data):
    # 向 Firebase 实时数据库写入新数据
    ref.child(key).update(new_data)  # 使用 update 更新数据

# Example usage
if __name__ == "__main__":
    initialize()  # 读取现有数据

    # 添加监听器
    print("Listening for new data...")
    ref.listen(on_data_change)

    # 保持脚本运行以持续监听
    import time
    while True:
        time.sleep(1)