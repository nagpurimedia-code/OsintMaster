import json
import os

def load_json_file(filepath):
    """Load data from JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {} if filepath.endswith('.json') and not filepath.endswith('_users.json') else []
    except json.JSONDecodeError:
        return {} if filepath.endswith('.json') and not filepath.endswith('_users.json') else []

def save_json_file(filepath, data):
    """Save data to JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False

def load_banned_users():
    """Load banned users from file"""
    data = load_json_file('data/banned_users.json')
    return set(data) if isinstance(data, list) else set()

def save_banned_users(banned_set):
    """Save banned users to file"""
    return save_json_file('data/banned_users.json', list(banned_set))

def load_verified_users():
    """Load verified users from file"""
    data = load_json_file('data/verified_users.json')
    return set(data) if isinstance(data, list) else set()

def save_verified_users(verified_set):
    """Save verified users to file"""
    return save_json_file('data/verified_users.json', list(verified_set))

def load_user_data():
    """Load user activity data"""
    return load_json_file('data/user_data.json')

def save_user_data(user_data):
    """Save user activity data"""
    return save_json_file('data/user_data.json', user_data)
