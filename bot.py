import requests
import json
import time
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Import custom modules
from utils.file_handlers import load_json_file, save_json_file
from utils.logger import log_info, log_error, log_warning
from handlers.verify_handler import verify_user, is_user_verified
from handlers.admin_handler import is_admin, ban_user, unban_user, is_user_banned, get_banned_users, get_verified_count, get_banned_count
from handlers.phone_lookup_handler import handle_phone_lookup

# Load configuration
config = load_json_file('config/config.json')
messages = load_json_file('config/messages.json')

BOT_TOKEN = config.get('bot_token', '')
ADMIN_IDS = config.get('admin_ids', [])
CHANNEL_1 = config.get('channels', {}).get('channel_1', '@HYPERMXPRIVATE')
CHANNEL_2 = config.get('channels', {}).get('channel_2', '@HYPERMX_PRO')

# Global state
user_state = {}

# ============ TELEGRAM API FUNCTIONS ============

def send_message(chat_id, text, reply_markup=None, parse_mode='HTML'):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        log_error(f"Error sending message: {e}")
        return None

def get_updates(offset=None):
    """Get updates from Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    payload = {"timeout": 30}
    if offset:
        payload["offset"] = offset
    
    try:
        response = requests.get(url, params=payload)
        return response.json()
    except Exception as e:
        log_error(f"Error getting updates: {e}")
        return {"ok": False}

# ============ KEYBOARD FUNCTIONS ============

def create_access_keyboard():
    """Create access required keyboard"""
    return {
        "inline_keyboard": [
            [
                {"text": "📌 JOIN @HYPERMXPRIVATE", "url": f"https://t.me/{CHANNEL_1.replace('@', '')}"}
            ],
            [
                {"text": "📌 JOIN @HYPERMX_PRO", "url": f"https://t.me/{CHANNEL_2.replace('@', '')}"}
            ],
            [
                {"text": "✅ Verify", "callback_data": "verify"}
            ]
        ]
    }

def create_main_keyboard():
    """Create main menu keyboard"""
    return {
        "keyboard": [
            ["📱 Phone Lookup"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def create_admin_keyboard():
    """Create admin keyboard"""
    return {
        "keyboard": [
            ["📊 Status", "👥 Ban User"],
            ["🔓 Unban User", "📋 Banned List"],
            ["🔙 Back to Main"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

# ============ MESSAGE HANDLERS ============

def send_access_required(chat_id):
    """Send access required message"""
    text = messages.get('access_required', 'Access Required')
    send_message(chat_id, text, reply_markup=create_access_keyboard())

def handle_start(chat_id, user_id):
    """Handle /start command"""
    if is_user_banned(user_id):
        send_message(chat_id, messages.get('banned', 'You are banned'))
        return
    
    if is_user_verified(user_id):
        send_message(chat_id, messages.get('welcome_verified', 'Welcome'), reply_markup=create_main_keyboard())
    else:
        send_access_required(chat_id)

def handle_verify_callback(chat_id, user_id):
    """Handle verify callback"""
    if is_user_banned(user_id):
        send_message(chat_id, messages.get('banned', 'You are banned'))
        return
    
    verify_user(user_id)
    send_message(chat_id, messages.get('verification_success', 'Verified!'), reply_markup=create_main_keyboard())

def handle_phone_lookup_request(chat_id, user_id, text):
    """Handle phone lookup request"""
    if is_user_banned(user_id):
        send_message(chat_id, messages.get('banned', 'You are banned'))
        return
    
    if not is_user_verified(user_id):
        send_access_required(chat_id)
        return
    
    result, error = handle_phone_lookup(text, config)
    
    if error:
        send_message(chat_id, error)
    else:
        send_message(chat_id, result)

def handle_admin_commands(chat_id, user_id, text):
    """Handle admin commands"""
    if not is_admin(user_id, ADMIN_IDS):
        send_message(chat_id, messages.get('admin_only', 'Not authorized'))
        return
    
    if text == "📊 Status":
        verified_count = get_verified_count()
        banned_count = get_banned_count()
        status = f"""
📊 <b>Bot Status:</b>
━━━━━━━━━━━━━━━━━━
👑 <b>Total Admins:</b> {len(ADMIN_IDS)}
✅ <b>Verified Users:</b> {verified_count}
🚫 <b>Banned Users:</b> {banned_count}
🆔 <b>Your ID:</b> {user_id}
━━━━━━━━━━━━━━━━━━
        """
        send_message(chat_id, status)
    
    elif text == "👥 Ban User":
        send_message(chat_id, messages.get('ban_prompt', 'Enter user ID to ban'))
        user_state[chat_id] = "awaiting_ban"
    
    elif text == "🔓 Unban User":
        send_message(chat_id, messages.get('unban_prompt', 'Enter user ID to unban'))
        user_state[chat_id] = "awaiting_unban"
    
    elif text == "📋 Banned List":
        banned = get_banned_users()
        if banned:
            banned_list = "\n".join(list(banned))
            send_message(chat_id, f"📋 <b>Banned Users:</b>\n━━━━━━━━━━━━━━━━━━\n<pre>{banned_list}</pre>")
        else:
            send_message(chat_id, messages.get('no_banned_users', 'No banned users'))
    
    elif text == "🔙 Back to Main":
        send_message(chat_id, messages.get('back_to_main', 'Back to main'), reply_markup=create_main_keyboard())
        if chat_id in user_state:
            del user_state[chat_id]

def handle_message(chat_id, user_id, text):
    """Handle incoming messages"""
    # Check if user is banned
    if is_user_banned(user_id):
        send_message(chat_id, messages.get('banned', 'You are banned'))
        return
    
    # Handle state-based commands
    if chat_id in user_state:
        if user_state[chat_id] == "awaiting_ban":
            if is_admin(user_id, ADMIN_IDS):
                try:
                    ban_user_id = int(text.strip())
                    ban_user(ban_user_id)
                    send_message(chat_id, messages.get('ban_success', 'User banned').format(user_id=ban_user_id))
                except ValueError:
                    send_message(chat_id, messages.get('invalid_user_id', 'Invalid ID'))
                del user_state[chat_id]
            return
        
        elif user_state[chat_id] == "awaiting_unban":
            if is_admin(user_id, ADMIN_IDS):
                try:
                    unban_user_id = int(text.strip())
                    unban_user(unban_user_id)
                    send_message(chat_id, messages.get('unban_success', 'User unbanned').format(user_id=unban_user_id))
                except ValueError:
                    send_message(chat_id, messages.get('invalid_user_id', 'Invalid ID'))
                del user_state[chat_id]
            return
        
        elif user_state[chat_id] == "awaiting_phone":
            handle_phone_lookup_request(chat_id, user_id, text)
            del user_state[chat_id]
            return
    
    # Admin commands
    if text in ["📊 Status", "👥 Ban User", "🔓 Unban User", "📋 Banned List", "🔙 Back to Main"]:
        handle_admin_commands(chat_id, user_id, text)
        return
    
    # Main commands
    if text == "/start":
        handle_start(chat_id, user_id)
    
    elif text == "📱 Phone Lookup":
        if is_user_verified(user_id):
            send_message(chat_id, messages.get('enter_number', 'Send 10 digit number'))
            user_state[chat_id] = "awaiting_phone"
        else:
            send_access_required(chat_id)
    
    else:
        send_message(chat_id, messages.get('unknown_command', 'Unknown command'))

# ============ HEALTH CHECK SERVER ============

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    
    def log_message(self, format, *args):
        pass

def run_health_server():
    """Run health check server"""
    port = config.get('settings', {}).get('port', 10000)
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    log_info(f"Health check server running on port {port}")
    server.serve_forever()

# ============ MAIN FUNCTION ============

def main():
    """Main bot loop"""
    log_info("🤖 Bot is starting...")
    log_info(f"📊 Admin IDs: {ADMIN_IDS}")
    log_info(f"🔗 API URL: {config.get('api_url', 'Not set')}")
    
    if not BOT_TOKEN:
        log_error("❌ BOT_TOKEN is empty! Please set your bot token.")
        return
    
    # Start health check server
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    last_update_id = 0
    
    while True:
        try:
            updates = get_updates(offset=last_update_id + 1)
            
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    
                    # Handle callback query
                    if "callback_query" in update:
                        callback = update["callback_query"]
                        chat_id = callback["message"]["chat"]["id"]
                        user_id = callback["from"]["id"]
                        data = callback["data"]
                        
                        # Answer callback
                        url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
                        requests.post(url, json={"callback_query_id": callback["id"]})
                        
                        if data == "verify":
                            handle_verify_callback(chat_id, user_id)
                    
                    # Handle message
                    elif "message" in update:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        user_id = message["from"]["id"]
                        
                        if "text" in message:
                            text = message["text"]
                            log_info(f"📨 Received from {user_id}: {text}")
                            handle_message(chat_id, user_id, text)
                        else:
                            send_message(chat_id, "❌ Please send text messages only.")
            
            time.sleep(1)
            
        except Exception as e:
            log_error(f"❌ Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
