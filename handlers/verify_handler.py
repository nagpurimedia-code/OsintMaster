from utils.file_handlers import load_verified_users, save_verified_users
from utils.logger import log_info

def verify_user(user_id):
    """Verify a user"""
    verified_users = load_verified_users()
    verified_users.add(str(user_id))
    save_verified_users(verified_users)
    log_info(f"User {user_id} verified successfully")
    return True

def is_user_verified(user_id):
    """Check if user is verified"""
    verified_users = load_verified_users()
    return str(user_id) in verified_users
