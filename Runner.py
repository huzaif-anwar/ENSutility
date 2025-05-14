import configparser
import oracledb
import json
import os
from datetime import datetime
import re
import pytz
from encrypt import is_encrypted, decrypt_string, load_api_config
import logging
from sendrequest import send_requests_and_save  # Import the function from sendrequest.py

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def parse_jdbc_url(jdbc_url):
    """Parse JDBC URL to extract host, port, and service name."""
    pattern = r'jdbc:oracle:thin:@([^:]+):(\d+)/(\w+)'
    match = re.match(pattern, jdbc_url)
    if match:
        host, port, service_name = match.groups()
        return host, port, service_name
    raise ValueError(f"Invalid JDBC URL format: {jdbc_url}")

def load_db_config(config_file):
    """Load database configuration from properties file."""
    config = configparser.ConfigParser()
    config.read(config_file)
    default = config['DEFAULT']
    return {
        'connection_string': default['DBConnectionString'],
        'username': default['DBUserName'],
        'password': default['DBPassword']
    }

def load_query(query_file):
    """Load SQL query from Query.properties file."""
    config = configparser.ConfigParser()
    config.read(query_file)
    return config['DEFAULT']['PaymentQuery']

def execute_query(connection_string, username, password, query):
    """Execute the query and return results with non-null VENDOR_PAYMENT_ID where rule exists."""
    try:
        host, port, service_name = parse_jdbc_url(connection_string)
        connection = oracledb.connect(
            user=username,
            password=password,
            host=host,
            port=port,
            service_name=service_name
        )
        cursor = connection.cursor()
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        results = []
        for row in cursor:
            row_dict = {columns[i]: value for i, value in enumerate(row)}
            results.append(row_dict)
        cursor.close()
        connection.close()
        return results
    except oracledb.DatabaseError as e:
        logger.error(f"Database error: {e}")
        return []
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return []

def create_json_request(record, index, api_config):
    """Create a JSON request in the specified format."""
    eastern = pytz.timezone('US/Eastern')
    current_time = datetime.now(eastern)
    send_timestamp = current_time.isoformat()
    process_date = current_time.strftime('%Y-%m-%dT00:00:00')
    
    business_nm = record.get('BUSINESS_NM')
    email = record.get('EMAIL_ADRS')
    first_nm = record.get('FIRST_NM')
    
    if email and is_encrypted(email):
        email = decrypt_string(email, api_config)
    
    if business_nm is None and first_nm is None:
        business_name = '.'
    else:
        business_name = first_nm if business_nm is None else business_nm

    card_type = record.get('CARD_TYPE_CD', '')
    card_type = card_type.upper() if card_type else ''

    request = {
        "headerInfo": {
            "requestId": str(134255678 + index),
            "sendTimeStamp": send_timestamp,
            "srcApplicationCd": record.get('SOURCE_APPLICATION_CD', ''),
            "inputChannelCd": record.get('INPUT_CHANNEL_CD', '')
        },
        "requestInfo": {
            "paymentInfo": {
                "maskedAccountNumber": record.get('MASKED_PAYMENT_ACCNT_NO', ''),
                "bankAccountType": "",
                "cardType": card_type,
                "customerEmail": email,
                "convenienceFeeAmount": record.get('CONVENIENCE_FEE_AMT', ''),
                "paymentAmount": float(record.get('PAYMENT_AMT', 0.0)),
                "paymentProcessDate": process_date,
                "paymentMethodCd": record.get('PAYMENT_METHOD_CD', ''),
                "paymentTypeCd": record.get('PAYMENT_TYPE_CD', ''),
                "paymentSubmittedBy": record.get('CREATED_APPLICATION_CD', ''),
                "customerType": record.get('CUSTOMER_TYPE_CD', ''),
                "paymentScheduleCd": record.get('PAYMENT_SCHEDULE_CD', ''),
                "orderOrInvoiceNumber": record.get('ORDER_NO', ''),
                "businessName": business_name,
                "customerFirstName": record.get('FIRST_NM', ''),
                "customerLastName": record.get('LAST_NM', ''),
                "billingApplicationCd": record.get('BILLING_APPLICATION_CD', 'ENS'),
                "billingAccountNumber": record.get('BILLING_APPLICATION_ACCNT_ID', ''),
                "vendorPaymentId": record.get('VENDOR_PAYMENT_ID', ''),
                "initiationIPAddress": "172.26.50.59",
                "checkId": record.get('CHECK_NO', ''),
                "payerFirstName": record.get('PAYER_FIRST_NM', ''),
                "payerLastName": record.get('PAYER_LAST_NM', ''),
                "currencyCd": "USD"
            }
        }
    }
    return request

def save_to_json_file(records, output_file, api_config):
    """Save records as JSON requests to a text file."""
    try:
        with open(output_file, 'w') as f:
            for index, record in enumerate(records):
                json_request = json.dumps(create_json_request(record, index, api_config))
                f.write(json_request + '\n')
        logger.info(f"JSON requests saved to {output_file}")
    except Exception as e:
        logger.error(f"Error writing to file: {e}")

def save_update_queries(queries, output_file):
    """Save UPDATE queries to a text file."""
    try:
        with open(output_file, 'w') as f:
            for query in queries:
                f.write(query + '\n')
        logger.info(f"UPDATE queries saved to {output_file}")
    except Exception as e:
        logger.error(f"Error writing UPDATE queries to {output_file}: {e}")

def main():
    # Paths
    config_file = os.path.join('resources', 'DB-config-prod.properties')
    query_file = os.path.join('resources', 'Query.properties')
    api_config_file = os.path.join('resources', 'postpaymentapi.properties')
    requests_file = 'payment_requests.txt'
    update_queries_file = 'update_queries.txt'
    output_file = 'payment_requests_responses.txt'
    
    # Load configuration
    if not os.path.exists(config_file):
        logger.error(f"Config file {config_file} not found.")
        return
    
    if not os.path.exists(query_file):
        logger.error(f"Query file {query_file} not found.")
        return
    
    if not os.path.exists(api_config_file):
        logger.error(f"API config file {api_config_file} not found.")
        return
    
    config = load_db_config(config_file)
    query = load_query(query_file)
    api_config = load_api_config(api_config_file)
    
    # Execute query
    records = execute_query(
        config['connection_string'],
        config['username'],
        config['password'],
        query
    )
    
    if not records:
        logger.info("No records found with non-null VENDOR_PAYMENT_ID where VendorForPayment rule exists.")
        return
    
    # Generate and display UPDATE queries
    logger.info("\nGenerated UPDATE Queries:")
    logger.info("------------------------")
    update_queries = [
        f"UPDATE payment SET PAYMENT_STATUS_CD = 'Settlement_Completed' WHERE PAYMENT_ID = '{record['PAYMENT_ID']}';" 
        for record in records
    ]
    for query in update_queries:
        logger.info(query)
    
    # Save UPDATE queries to file
    save_update_queries(update_queries, update_queries_file)
    
    # Save JSON requests (needed for sending later if confirmed)
    save_to_json_file(records, requests_file, api_config)
    
    # Prompt user for confirmation
    print("\nDo you want to update these records in the database and send POST requests? (y/n)")
    response = input().strip().lower()
    
    if response == 'y':
        # Send POST requests and save requests with responses
        send_requests_and_save(api_config_file, requests_file, output_file)
    else:
        logger.info("Update and request sending cancelled.")

if __name__ == "__main__":
    main()