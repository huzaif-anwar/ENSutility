import configparser
import os
import json
import requests
from requests.auth import HTTPBasicAuth
import logging

# Configure logging to console and file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('sendrequest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
        'url': default.get('PostPaymentURL', ''),
        'username': default.get('UserName', ''),
        'password': default.get('Password', ''),
        'bypass_ssl': default.get('BypassSSLVerification', 'true').lower() == 'true',
        'ca_cert_path': default.get('CACertPath', '')
    }
    logger.debug(f"Config loaded: URL={config_data['url']}, Username={config_data['username']}, Password={'*' * len(config_data['password'])}, BypassSSL={config_data['bypass_ssl']}, CACertPath={config_data['ca_cert_path']}")
    return config_data

def read_requests(requests_file):
    """Read JSON requests from the file."""
    logger.debug(f"Reading requests from {requests_file}")
    if not os.path.exists(requests_file):
        logger.error(f"Requests file {requests_file} not found")
        raise FileNotFoundError(f"Requests file {requests_file} not found")
    
    requests_list = []
    with open(requests_file, 'r') as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                logger.warning(f"Empty line at line {line_number}")
                continue
            try:
                request = json.loads(line)
                requests_list.append(request)
                logger.debug(f"Parsed request at line {line_number}: requestId={request.get('headerInfo', {}).get('requestId', 'unknown')}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON at line {line_number}: {e}")
    if not requests_list:
        logger.warning("No valid requests found in file")
    else:
        logger.info(f"Loaded {len(requests_list)} valid requests")
    return requests_list

def send_post_request(request, url, username, password, bypass_ssl, ca_cert_path):
    """Send a POST request and return the response details."""
    request_id = request.get('headerInfo', {}).get('requestId', 'unknown')
    logger.debug(f"Sending POST request for requestId={request_id}")
    headers = {'Content-Type': 'application/json'}
    verify = True
    if bypass_ssl:
        logger.warning(f"Bypassing SSL verification for requestId={request_id} (insecure)")
        verify = False
    elif ca_cert_path and os.path.exists(ca_cert_path):
        logger.debug(f"Using custom CA certificate: {ca_cert_path}")
        verify = ca_cert_path
    else:
        logger.debug("Using default SSL verification")
    
    try:
        response = requests.post(
            url,
            json=request,
            headers=headers,
            auth=HTTPBasicAuth(username, password),
            timeout=30,
            verify=verify
        )
        logger.info(f"Request {request_id} received status: {response.status_code}")
        try:
            response_body = response.json()
            logger.debug(f"Response JSON for {request_id}: {json.dumps(response_body, indent=2)}")
        except ValueError:
            response_body = response.text
            logger.debug(f"Response text for {request_id}: {response_body}")
        return {
            'request_id': request_id,
            'status_code': response.status_code,
            'response_body': response_body,
            'request': request
        }
    except requests.RequestException as e:
        logger.error(f"Request {request_id} failed: {str(e)}")
        return {
            'request_id': request_id,
            'status_code': None,
            'response_body': f"Request failed: {str(e)}",
            'request': request
        }

def save_requests_and_responses(responses, output_file):
    """Save requests and responses to a text file."""
    logger.debug(f"Saving requests and responses to {output_file}")
    try:
        with open(output_file, 'w') as f:
            for resp in responses:
                f.write("Request:\n")
                f.write(f"{json.dumps(resp['request'], indent=2)}\n")
                f.write("Response:\n")
                f.write(f"Status Code: {resp['status_code']}\n")
                f.write(f"Response Body: {json.dumps(resp['response_body'], indent=2)}\n")
                f.write("-" * 50 + "\n")
        logger.info(f"Requests and responses saved to {output_file}")
    except Exception as e:
        logger.error(f"Error writing to {output_file}: {e}")
        raise

def send_requests_and_save(config_file, requests_file, output_file):
    """Send requests and save both requests and responses."""
    logger.info("Starting request sending process")
    
    # Load API configuration
    try:
        config = load_api_config(config_file)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return
    
    url = config['url']
    username = config['username']
    password = config['password']
    bypass_ssl = config['bypass_ssl']
    ca_cert_path = config['ca_cert_path']
    
    # Validate configuration
    if not url:
        logger.error("PostPaymentURL is missing in config")
        return
    if not username or not password:
        logger.error("Username or Password missing in config")
        return
    logger.debug("Configuration validated successfully")
    
    # Read JSON requests
    try:
        requests_list = read_requests(requests_file)
    except Exception as e:
        logger.error(f"Failed to read requests: {e}")
        return
    
    if not requests_list:
        logger.error("No requests to process")
        return
    
    # Send POST requests and collect responses
    responses = []
    for request in requests_list:
        response = send_post_request(request, url, username, password, bypass_ssl, ca_cert_path)
        responses.append(response)
    
    # Save requests and responses
    try:
        save_requests_and_responses(responses, output_file)
    except Exception as e:
        logger.error(f"Failed to save responses: {e}")

def main():
    logger.info("Starting sendrequest.py")
    # File paths
    config_file = os.path.join('resources', 'postpaymentapi.properties')
    requests_file = 'payment_requests.txt'
    output_file = 'payment_requests_responses.txt'
    
    # Send requests and save responses
    send_requests_and_save(config_file, requests_file, output_file)
    
    logger.info("sendrequest.py completed")

if __name__ == "__main__":
    main()