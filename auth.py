import pyrebase
import firebase_admin
from firebase_admin import credentials, db
from config import FIREBASE_CONFIG, SERVICE_ACCOUNT_PATH

# Initialize Pyrebase
firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
auth = firebase.auth()

# Initialize Firebase Admin SDK (only if not already initialized)
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_CONFIG['databaseURL']
    })

def register_user(email, password, role='student'):
    """
    Register a new user in Firebase Authentication and store role in Realtime Database.
    """
    try:
        user = auth.create_user_with_email_and_password(email, password)
        user_id = user['localId']
        
        # Store user role in Firebase Realtime Database
        ref = db.reference(f'users/{user_id}')
        ref.set({
            'email': email,
            'role': role
        })
        print(f"User {email} registered successfully as {role}.")
        return True
    except Exception as e:
        print(f"Error registering user: {e}")
        return False

def login_user(email, password):
    """
    Log in a user and return their role if successful.
    """
    try:
        # Attempt to sign in with email and password
        user = auth.sign_in_with_email_and_password(email, password)
        user_id = user['localId']

        # Fetch the user's role from Firebase Realtime Database
        ref = db.reference(f'users/{user_id}')
        user_info = ref.get()

        if user_info:
            print(f"Logged in as {user_info['role']} - {email}")
            return user_info['role']
        else:
            print("User not found in the database.")
            return None

    except Exception as e:
        error_message = str(e)
        print(f"Authentication failed: {error_message}")
        return None

def get_user_role(user_id):
    """
    Fetch the user's role from Firebase Realtime Database.
    """
    try:
        ref = db.reference(f'users/{user_id}')
        user_info = ref.get()
        if user_info and 'role' in user_info:
            return user_info['role']
        else:
            return None
    except Exception as e:
        print(f"Error fetching user role: {e}")
        return None

# Example usage (for testing purposes)
if __name__ == "__main__":
    print("1. Register User")
    print("2. Login User")
    choice = input("Select an option (1 or 2): ")

    if choice == '1':
        email = input("Enter email: ")
        password = input("Enter password: ")
        role = input("Enter role (admin/student): ")
        success = register_user(email, password, role)
        if success:
            print("Registration successful.")
    elif choice == '2':
        email = input("Enter email: ")
        password = input("Enter password: ")
        role = login_user(email, password)
        if role:
            print(f"Logged in as {role}")
