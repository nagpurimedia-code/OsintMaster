import requests
import re
import json
from utils.logger import log_info, log_error

class PhoneAPI:
    def __init__(self, api_url):
        self.api_url = api_url
        self.timeout = 30
    
    def lookup_number(self, phone_number):
        """Lookup phone number details"""
        try:
            api_url = f"{self.api_url}?api_key=database&number={phone_number}"
            log_info(f"Calling API: {api_url}")
            
            response = requests.get(
                api_url,
                timeout=self.timeout,
                headers={
                    "Accept": "application/json, text/html, */*",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            log_info(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                return self.parse_response(response.text, phone_number)
            else:
                return None, f"API Error: Status {response.status_code}"
                
        except requests.exceptions.Timeout:
            return None, "API request timed out"
        except requests.exceptions.ConnectionError:
            return None, "Cannot connect to API server"
        except Exception as e:
            log_error(f"API Error: {e}")
            return None, str(e)
    
    def parse_response(self, response_text, phone_number):
        """Parse API response"""
        try:
            # Try JSON parsing
            json_data = json.loads(response_text)
            user_data = self.extract_user_data(json_data)
            
            if user_data and isinstance(user_data, dict):
                return user_data, None
                
        except json.JSONDecodeError:
            log_info("JSON parsing failed, trying HTML parsing")
            return self.parse_html_response(response_text, phone_number)
        
        return None, "No information found"
    
    def extract_user_data(self, json_data):
        """Extract user data from JSON"""
        user_data = None
        
        # Check for data in 'data' array
        if 'data' in json_data and isinstance(json_data['data'], list):
            if len(json_data['data']) > 0:
                user_data = json_data['data'][0]
        
        # Check if response is array
        elif isinstance(json_data, list) and len(json_data) > 0:
            user_data = json_data[0]
        
        # Check if response has user fields
        elif isinstance(json_data, dict) and 'name' in json_data:
            user_data = json_data
        
        # Check nested keys
        elif isinstance(json_data, dict):
            for key in ['result', 'results', 'user', 'info', 'data']:
                if key in json_data:
                    if isinstance(json_data[key], list) and len(json_data[key]) > 0:
                        user_data = json_data[key][0]
                        break
                    elif isinstance(json_data[key], dict):
                        user_data = json_data[key]
                        break
        
        return user_data
    
    def parse_html_response(self, html_text, phone_number):
        """Parse HTML response using regex"""
        if 'FULAWA DEVI' in html_text or phone_number in html_text:
            extracted = {}
            patterns = {
                'name': r'(?:Name|नाम)\s*[:|]\s*([^<>\n\r]+)',
                'fname': r'(?:Father|Father Name|पिता)\s*[:|]\s*([^<>\n\r]+)',
                'mobile': r'(?:Mobile|Phone|Number|मोबाइल)\s*[:|]\s*([0-9]{10})',
                'alt': r'(?:Alt|Alternative|Alternate)\s*[:|]\s*([0-9]{10})',
                'circle': r'(?:Circle|Area|Location|ज़िला)\s*[:|]\s*([^<>\n\r]+)',
                'address': r'(?:Address|पता)\s*[:|]\s*([^<>\n\r]+)',
                'id': r'(?:Aadhaar|ID|आधार)\s*[:|]\s*([0-9]{12})'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, html_text, re.IGNORECASE | re.DOTALL)
                if match:
                    extracted[key] = match.group(1).strip()
                else:
                    extracted[key] = 'N/A'
            
            if extracted.get('name') != 'N/A':
                return extracted, None
        
        return None, "No information found"
