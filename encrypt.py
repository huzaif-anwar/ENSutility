import re
import requests
import configparser
import os
from requests.auth import HTTPBasicAuth
import logging
import urllib3

# Configure logging to console and file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('decrypt_string.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress SSL warnings only if bypass is enabled (logged later)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_api_config(config_file):
    """Load API configuration from properties file."""
    logger.debug(f"Loading config from {config_file}")
    if not os.path.exists(config_file):
        logger.error(f"Config file {config_file} not found")
        raise FileNotFoundError(f"Config file {config_file} not found")
    
    config = configparser.ConfigParser()
    config.read(config_file)
    if 'DEFAULT' not in config:
        logger.error("No [DEFAULT] section in config file")
        raise ValueError("No [DEFAULT] section in config file")
    
    default = config['DEFAULT']
    config_data = {
        'api_key': default.get('UserName', ''),
        'api_password': default.get('Password', ''),
        'bypass_ssl': default.get('BypassSSLVerification', 'true').lower() == 'true',
        'ca_cert_path': default.get('CACertPath', '')
    }
    logger.debug(f"Config loaded: Username={config_data['api_key']}, Password={'*' * len(config_data['api_password'])}, BypassSSL={config_data['bypass_ssl']}, CACertPath={config_data['ca_cert_path']}")
    return config_data

def is_base64_encoded(s):
    """Check if a string is Base64 encoded."""
    logger.debug("Checking if string is Base64 encoded")
    if not s:
        logger.debug("Empty string, not Base64 encoded")
        return False
    
    base64_pattern = r'^(?:[A-Za-z0-9+/]{4})*(?:(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?)$'
    if not re.match(base64_pattern, s):
        logger.debug("String does not match Base64 pattern")
        return False
    
    logger.debug("String is Base64 encoded")
    return True

def is_hex(s):
    """Check if a string is Hex encoded."""
    logger.debug("Checking if string is Hex encoded")
    if not s:
        logger.debug("Empty string, not Hex encoded")
        return False
    
    hex_pattern = r'^[0-9A-Fa-f]+$'
    result = bool(re.match(hex_pattern, s))
    logger.debug(f"String is {'Hex' if result else 'not Hex'} encoded")
    return result

def is_encrypted(input_str):
    """Check if a string is encrypted (Base64 or Hex encoded)."""
    logger.debug("Checking if string is encrypted")
    if not input_str:
        logger.debug("Empty string, not encrypted")
        return False
    
    result = is_base64_encoded(input_str) or is_hex(input_str)
    logger.debug(f"String is {'encrypted' if result else 'not encrypted'}")
    return result

def decrypt_string(encrypted_str, api_config):
    """Decrypt a string using the external API with configurable SSL verification."""
    api_url = "https://api-test2.test.intranet/Application/v1/CIPS/crypto/DES/decryption"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "data": encrypted_str
    }
    
    verify = True
    if api_config['bypass_ssl']:
        logger.warning("Bypassing SSL verification (insecure)")
        verify = False
    elif api_config['ca_cert_path'] and os.path.exists(api_config['ca_cert_path']):
        logger.debug(f"Using custom CA certificate: {api_config['ca_cert_path']}")
        verify = api_config['ca_cert_path']
    else:
        logger.debug("Using default SSL verification")
    
    try:
        logger.debug(f"Sending decryption request for data: {encrypted_str}")
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            auth=HTTPBasicAuth(api_config['api_key'], api_config['api_password']),
            timeout=10,
            verify=verify
        )
        response.raise_for_status()
        result = response.json()
       
        decrypted_data = response.json().get('decrypted', result["data"])
        logger.info(f"Decryption successful, decrypted text: {decrypted_data}")
        return decrypted_data
    except requests.RequestException as e:
        logger.error(f"Decryption API error: {e}")
        return encrypted_str

if __name__ == "__main__":
    logger.info("Starting decrypt_string.py")
    config_file = os.path.join('resources', 'postpaymentapi.properties')
    try:
        config = load_api_config(config_file)
        # Example usage
        test_str = "ijDTHwS3Bo6jjjvD6IPPFB1U5+efqkb24chSTAwLqJg="  # Base64 encoded "Hello World"
        if is_encrypted(test_str):
            decrypted = decrypt_string(test_str, config)
        else:
            logger.warning(f"String {test_str} is not encrypted")
    except Exception as e:
        logger.error(f"Error: {e}")
    logger.info("decrypt_string.py completed")