from utils.file_handlers import load_banned_users, save_banned_users, load_verified_users
from utils.logger import log_info

def is_admin(user_id, admin_ids):
    """Check if user is admin"""
    return user_id in admin_ids

def ban_user(user_id):
    """Ban a user"""
    banned_users = load_banned_users()
    banned_users.add(str(user_id))
    save_banned_users(banned_users)
    log_info(f"User {user_id} banned")
    return True

def unban_user(user_id):
    """Unban a user"""
    banned_users = load_banned_users()
    banned_users.discard(str(user_id))
    save_banned_users(banned_users)
    log_info(f"User {user_id} unbanned")
    return True

def is_user_banned(user_id):
    """Check if user is banned"""
    banned_users = load_banned_users()
    return str(user_id) in banned_users

def get_banned_users():
    """Get list of banned users"""
    return load_banned_users()

def get_verified_count():
    """Get count of verified users"""
    return len(load_verified_users())

def get_banned_count():
    """Get count of banned users"""
    return len(load_banned_users())
