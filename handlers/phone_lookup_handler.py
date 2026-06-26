from api.phone_api import PhoneAPI
from utils.logger import log_info, log_error

def format_number_info(data):
    """Format user info for display"""
    if not data or not isinstance(data, dict):
        return None
    
    if 'name' in data and data.get('name') != 'N/A':
        formatted = f"""
📱 <b>Phone Number Details</b>
━━━━━━━━━━━━━━━━━━
👤 <b>Name:</b> {data.get('name', 'N/A')}
👨‍👦 <b>Father:</b> {data.get('fname', 'N/A')}
📱 <b>Mobile:</b> {data.get('mobile', 'N/A')}
📞 <b>Alt Number:</b> {data.get('alt', 'N/A')}
📍 <b>Circle:</b> {data.get('circle', 'N/A')}
🏠 <b>Address:</b> {data.get('address', 'N/A')}
📌 <b>Aadhaar:</b> {data.get('id', 'N/A')}
📧 <b>Email:</b> {data.get('email', 'N/A')}
━━━━━━━━━━━━━━━━━━
👨‍💻 <b>Developer:</b> Colden Minj
📞 <b>Contact:</b> @ColdenMinjBot
━━━━━━━━━━━━━━━━━━
        """
        return formatted
    return None

def handle_phone_lookup(phone_number, config):
    """Handle phone lookup request"""
    # Validate number
    phone_number = ''.join(filter(str.isdigit, phone_number))
    
    if len(phone_number) != 10 or not phone_number.isdigit():
        return None, "Invalid number! Please send exactly 10 digits."
    
    # Call API
    api = PhoneAPI(config['api_url'])
    user_data, error = api.lookup_number(phone_number)
    
    if error:
        return None, error
    
    if user_data:
        formatted = format_number_info(user_data)
        if formatted:
            return formatted, None
    
    return None, "No information found for this number."
