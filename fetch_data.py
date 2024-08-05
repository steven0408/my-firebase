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

# Example usage
if __name__ == "__main__":
    print(fetch_data())