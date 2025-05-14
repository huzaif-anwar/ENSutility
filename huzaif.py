import configparser
import oracledb
import json
import os
from datetime import datetime
import re
from datetime import datetime, timezone
import pytz

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

def execute_query(connection_string, username, password):
    """Execute the query and return results."""
    query = """
    SELECT PAYMENT_ID, SOURCE_APPLICATION_CD, INPUT_CHANNEL_CD, MASKED_PAYMENT_ACCNT_NO, CARD_TYPE_CD, 
           EMAIL_ADRS, PAYMENT_AMT, PAYMENT_METHOD_CD, PAYMENT_TYPE_CD, CREATED_APPLICATION_CD, 
           CUSTOMER_TYPE_CD, PAYMENT_SCHEDULE_CD, ORDER_NO, BUSINESS_NM, FIRST_NM, LAST_NM, 
           BILLING_APPLICATION_CD, BILLING_APPLICATION_ACCNT_ID, VENDOR_PAYMENT_ID,PAYER_FIRST_NM,PAYER_LAST_NM,CONVENIENCE_FEE_AMT,CHECK_NO 
    FROM payment 
    WHERE BILLING_APPLICATION_CD = 'ENS' 
    AND PAYMENT_CREATE_DT >= '01-FEB-25' 
    AND PAYMENT_STATUS_CD = 'Posting_Error'
    """
    try:
        # Parse JDBC URL
        host, port, service_name = parse_jdbc_url(connection_string)
        
        # Establish database connection in thin mode
        connection = oracledb.connect(
            user=username,
            password=password,
            host=host,
            port=port,
            service_name=service_name
        )
        cursor = connection.cursor()
        
        # Execute query
        cursor.execute(query)
        
        # Fetch column names
        columns = [col[0] for col in cursor.description]
        
        # Fetch all rows
        results = []
        for row in cursor:
            row_dict = {columns[i]: value for i, value in enumerate(row)}
            results.append(row_dict)
        
        # Close cursor and connection
        cursor.close()
        connection.close()
        
        return results
    
    except oracledb.DatabaseError as e:
        print(f"Database error: {e}")
        return []
    except ValueError as e:
        print(f"Configuration error: {e}")
        return []

def create_json_request(record, index):
    """Create a JSON request in the specified format."""
    eastern = pytz.timezone('US/Eastern')
    current_time = datetime.now(eastern)
    send_timestamp = current_time.isoformat()
    process_date = current_time.strftime('%Y-%m-%dT00:00:00')
    
    # Check if both BUSINESS_NM and FIRST_NM are null
    business_nm = record.get('BUSINESS_NM')
    first_nm = record.get('FIRST_NM')
    if business_nm is None and first_nm is None:
        business_name = '.'
    else:
        if business_nm is None:
            business_name = first_nm
        else:
            business_name = business_nm


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
                "cardType": record.get('CARD_TYPE_CD', ''),
                "customerEmail": record.get('EMAIL_ADRS', ''),
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

def save_to_json_file(records, output_file):
    """Save records as JSON requests to a text file."""
    try:
        with open(output_file, 'w') as f:
            for index, record in enumerate(records):
                json_request = json.dumps(create_json_request(record, index))
                f.write(json_request + '\n')
        print(f"JSON requests saved to {output_file}")
    except Exception as e:
        print(f"Error writing to file: {e}")

def main():
    # Paths
    config_file = os.path.join('resources', 'DB-config-prod.properties')
    output_file = 'payment_requests.txt'
    
    # Load configuration
    if not os.path.exists(config_file):
        print(f"Config file {config_file} not found.")
        return
    
    config = load_db_config(config_file)
    
    # Execute query
    records = execute_query(
        config['connection_string'],
        config['username'],
        config['password']
    )
    
    # Save results to file
    if records:
        save_to_json_file(records, output_file)
    else:
        print("No records found or query failed.")

if __name__ == "__main__":
    main()