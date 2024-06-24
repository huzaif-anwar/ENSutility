import datetime
import os
import pandas as pd
import jpype
import jaydebeapi
import configparser


def run_query(query, conn):
    curs = conn.cursor()
    curs.execute(query)
    rows = curs.fetchall()
    column_names = [desc[0] for desc in curs.description]
    # Convert tuples to lists
    rows = [list(row) for row in rows]
    df = pd.DataFrame(rows, columns=column_names)
    if df is not None:  # Compare the sum of the first column values with the baseline
        return df
    else:
        return None


def create_db_connection():
    # Load DB config
    config = configparser.ConfigParser()
    config.read('resources/DB-config-prod.properties')

    # Start the JVM
    jar = os.path.join(os.getcwd(), 'jar', 'ojdbc8.jar')
    args = '-Djava.class.path=%s' % jar

    jvm_path = jpype.getDefaultJVMPath()
    if not jpype.isJVMStarted():
        jpype.startJVM(jvm_path, args)

    # Create DB connection
    conn = jaydebeapi.connect('oracle.jdbc.driver.OracleDriver',
                              config.get('DEFAULT', 'DBConnectionString'),
                              [config.get('DEFAULT', 'DBUserName'), config.get('DEFAULT', 'DBPassword')])
    return conn


def generate_update_queries(cbr_report):
    conn = None
    file = None
    try:
        conn = create_db_connection()

        # Open the file in write mode
        file = open('../ProdSupport_scripts/update_queries.txt', 'w')

        # Write the first line to the file
        today = datetime.date.today()
        file.write(f'Queries to run in production for {today}\r\n')

        queryconfig = configparser.ConfigParser()
        queryconfig.read('resources/Prepupdatequery.properties')

        # Define a dictionary with the query names and their corresponding baselines
        queries = [
            'Settlement_Completed_Stuck',
            'Notation_Batch_Transaction',
            'Notification_Batch_Transaction',
            'Approved_Payments'
        ]

        # Iterate over the dictionary and run each query
        for query_name in queries:
            # print(query_name)
            query = queryconfig.get('Update', query_name)
            # print(query)
            df = run_query(query, conn)
            if df is not None:
                # print(df)
                # If the query name is 'Notation_Batch_Transaction' or 'Notification_Batch_Transaction'
                if query_name in ['Notation_Batch_Transaction', 'Notification_Batch_Transaction']:
                    # Get the BATCH_TRANSACTION_IDs from the DataFrame
                    batch_transaction_ids = df['BATCH_TRANSACTION_ID'].tolist()
                    if batch_transaction_ids:
                        # Generate the update query
                        update_query = f"update EPWF.BATCH_TRANSACTION set BATCH_STATUS_CD='ManualReviewComplete' where BATCH_TRANSACTION_ID in({','.join(map(str, batch_transaction_ids))});"
                        print(update_query)
                        file.write(f"{update_query}\r\n")
                elif query_name == 'Settlement_Completed_Stuck':
                    for index, row in df.iterrows():
                        if row['TRANSACTION_TYPE_CD'] == 'Chargeback' and row['BILLING_APPLICATION_CD'] == 'CPE':
                            print("CPE - Details to send to CPE team")
                            print(f"{row['BILLING_APPLICATION_ACCNT_ID']} - BTN")
                            print(f"CB ID -{row['PAYMENT_ID']} - PAYMENT_ID")
                            print(f"Original Pmt-{row['ASSOCIATED_PAYMENT_ID']} -ASSOCIATED_PAYMENT_ID")
                            print(f"PMT amt- {row['PAYMENT_AMT']} - payment_amt")
                            print(f"PMT Process date -{row['PAYMENT_PROCESS_DT']} - payment_process_dt")
                            # Append to the text file
                            with open('../ProdSupport_scripts/cpe_email_content.txt', 'a') as cpefile:
                                if os.path.getsize('../ProdSupport_scripts/cpe_email_content.txt') == 0:
                                    cpefile.write("CPE - Details to send to CPE team\r\n")
                                cpefile.write(f"{row['BILLING_APPLICATION_ACCNT_ID']} - BTN\r\n")
                                cpefile.write(f"CB ID -{row['PAYMENT_ID']} - PAYMENT_ID\r\n")
                                cpefile.write(f"Original Pmt-{row['ASSOCIATED_PAYMENT_ID']} -ASSOCIATED_PAYMENT_ID\r\n")
                                cpefile.write(f"PMT amt- {row['PAYMENT_AMT']} - payment_amt\r\n")
                                cpefile.write(f"PMT Process date -{row['PAYMENT_PROCESS_DT']} - payment_process_dt\r\n")

                                # Generate the update query for each record
                                update_query = f"update payment set payment_status_cd='Posted' where payment_id in ({row['PAYMENT_ID']}) and BILLING_APPLICATION_CD='CPE' and TRANSACTION_TYPE_CD='Chargeback';"
                                print('--Post confirmation from CPE team-- ' + update_query)
                                cpefile.write(f'--Post confirmation from CPE team-- {update_query}\r\n\n')
                        elif str(row['BILLING_APPLICATION_CD']).startswith('CRIS') and len(
                                row['BILLING_APPLICATION_ACCNT_ID']) < 13:
                            select_query = f"select * from payment where PAYMENT_CREATE_DT>= SYSDATE -400 and CREATED_DTTM>SYSDATE-400 and BILLING_APPLICATION_ACCNT_ID like '%{row['BILLING_APPLICATION_ACCNT_ID']}%' order by payment_process_dt desc"
                            # print(select_query)
                            select_df = run_query(select_query, conn)
                            if select_df is not None and len(select_df) > 1:
                                for _, second_row in select_df.iterrows():
                                    if len(second_row['BILLING_APPLICATION_ACCNT_ID']) == 13:
                                        update_query = f"update payment set BILLING_APPLICATION_ACCNT_ID = '{second_row['BILLING_APPLICATION_ACCNT_ID']}', LAST_MODIFIED_DTTM = sysdate, LAST_MODIFIED_USER_NM = 'ac65760' where payment_id = {row['PAYMENT_ID']} and BILLING_APPLICATION_ACCNT_ID='{row['BILLING_APPLICATION_ACCNT_ID']}';"
                                        print(update_query)
                                        file.write(f"{update_query}\r\n")
                                        break
                                else:
                                    update_query = f"update payment set payment_status_cd='Pending_Correction' ,LAST_MODIFIED_DTTM = sysdate, LAST_MODIFIED_USER_NM = 'AC65760' where  payment_id = {row['PAYMENT_ID']} and BILLING_APPLICATION_ACCNT_ID='{row['BILLING_APPLICATION_ACCNT_ID']}';"
                                    print(update_query)
                                    file.write(f"{update_query}\r\n")
                            else:
                                update_query = f"update payment set payment_status_cd='Pending_Correction' ,LAST_MODIFIED_DTTM = sysdate, LAST_MODIFIED_USER_NM = 'AC65760' where  payment_id = {row['PAYMENT_ID']} and BILLING_APPLICATION_ACCNT_ID='{row['BILLING_APPLICATION_ACCNT_ID']}';"
                                print(update_query)
                                file.write(f"{update_query}\r\n")

                elif query_name == 'Approved_Payments':
                    payment_ids = df['PAYMENT_ID'].tolist()
                    if payment_ids:
                        print("List of Approved payment_ids : ", payment_ids)
                        with open('payment_ids.txt', 'w') as f:
                            # Write today's date on the first line
                            f.write(f"Approved payment list for : {today}\n")
                            for payment_id in payment_ids:
                                f.write(f"{payment_id}\n")
                    for payment_id in payment_ids:
                        life_cycle_query = f"select pi.process_id, pi.PROCESS_INSTANCE_ID, w.work_name as process ," \
                                           f"ws.WORK_STATUS_DESC as status , pi.CREATE_DT from process_instance pi, " \
                                           f"work w ,work_status ws where pi.master_request_id='{payment_id}' and " \
                                           f"pi.process_id = w.work_id and pi.status_cd = ws.WORK_STATUS_ID order by " \
                                           f"pi.PROCESS_INSTANCE_ID asc"
                        # print(life_cycle_query)
                        lifecycle_df = run_query(life_cycle_query, conn)
                        if lifecycle_df is not None:
                            if len(lifecycle_df) > 3 and all(lifecycle_df['STATUS'] == 'Completed'):
                                update_query = f"UPDATE payment SET PAYMENT_STATUS_CD = (case when (VENDOR_CD =  " \
                                               f"'JPMC' OR VENDOR_CD = 'WELLSFARGO' OR ( VENDOR_CD =  'SPEEDPAY' and  " \
                                               f"PAYMENT_SCHEDULE_CD = 'Scheduled')) then 'Capture_Ready' when " \
                                               f"VENDOR_CD =  'SPEEDPAY' and  PAYMENT_SCHEDULE_CD = 'OneTime' then " \
                                               f"'Settlement_Completed' when VENDOR_CD =  'OPA' then " \
                                               f"'Session_Canceled' when VENDOR_CD = 'PAYPAL' and PAYMENT_SCHEDULE_CD " \
                                               f"= 'OneTime' then 'Settlement_Completed' end) WHERE PAYMENT_ID in (" \
                                               f"{payment_id});"
                                print(update_query)
                                file.write(f"{update_query}\r\n")
                            else:
                                print(f"Payment ID: {payment_id} has not completed the lifecycle")
                                # print(lifecycle_df[['PROCESS', 'STATUS', 'PROCESS_INSTANCE_ID']].to_string())

        # Check if the cbr_report is None or empty
        if not cbr_report:
            print("Analysis of CBR Report is skipped as no CBR report file provided.")
        else:
            print("Loading the Excel file")
            # Load the Excel file and sheet using pandas
            input_file_name = cbr_report
            downloads_folder = os.path.expanduser('~\\Downloads\\')
            excel_path = os.path.join(downloads_folder, input_file_name)
            file_name = os.path.basename(excel_path)
            print(file_name)
            df = pd.read_excel(excel_path)

            # Check if 'POST_STUS_MSG_TXT' column contains 'Invalid Parameters'
            if df['POST_STUS_MSG_TXT'].str.contains('Invalid parameter').any():
                # Get the respective payment_ids
                payment_ids = df.loc[df['POST_STUS_MSG_TXT'].str.contains('Invalid parameter'), 'PAYMENT_ID'].values
                # Run your SQL query for each payment_id
                for payment_id in payment_ids:
                    query = f"select * from post_allc where PAYMENT_ID in ({payment_id})"
                    # print(query)
                    df = run_query(query, conn)
                    # If data is present
                    if df is not None and not df.empty:
                        # Get the BILL_APPL_ACCT_ID
                        bill_appl_acct_id = df['BILL_APPL_ACCT_ID'].values[0]
                        # Run the second query
                        second_query = f"select * from EPWF.CRIS_ENS_MAPPING_REF where CRIS_BTN='{bill_appl_acct_id}'"
                        # print(second_query)
                        second_df = run_query(second_query, conn)
                        # If data is present in the second query
                        if second_df is not None and not second_df.empty:
                            # Run the third query
                            third_query = f"select * from EPWF.PMT_CORRECTION_MAPPING where OLD_BILLING_ACCT_ID='{bill_appl_acct_id}'"
                            # print(third_query)
                            third_df = run_query(third_query, conn)
                            # If data is present in the third query
                            if third_df is not None and not third_df.empty:
                                # Get the NEW_BILLING_ACCT_ID
                                new_billing_acct_id = third_df['NEW_BILLING_ACCT_ID'].values[0]
                                # Run the update query
                                update_query_1 = f"update payment set BILLING_APPLICATION_ACCNT_ID='{new_billing_acct_id}', BILLING_APPLICATION_CD='ENS', DESTINATION_APPLICATION_CD='ENJ', PAYMENT_STATUS_CD='Settlement_Completed' where PAYMENT_ID ={payment_id};"
                                update_query_2 = f"update EPWF.POST_ALLC set BILL_APPL_ACCT_ID='{new_billing_acct_id}',BILL_APPL_CD='ENS' where PAYMENT_ID ={payment_id};"
                                print(update_query_1)
                                file.write(f'{update_query_1}\r\n')
                                print(update_query_2)
                                file.write(f'{update_query_2}\r\n')
            else:
                print("No Invalid parameter found")
            df = pd.read_excel(excel_path)
            # Check if 'POST_STUS_MSG_TXT' column contains 'input string'
            if df['POST_STUS_MSG_TXT'].str.contains('input string').any():
                payment_ids = df.loc[df['POST_STUS_MSG_TXT'].str.contains('input string'), 'PAYMENT_ID'].values
                for payment_id in payment_ids:
                    query = f"update payment set CREATED_USER_NM='4500014',PAYMENT_STATUS_CD='Settlement_Completed' where PAYMENT_ID in ({payment_id});"
                    print(query)
                    file.write(f"{query}\r\n")
            else:
                print("No input string found")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the file
        if file is not None:
            file.close()
        # Close the connection
        if conn is not None:
            conn.close()
