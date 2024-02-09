import pandas as pd
import os


def checkForMDWFallout(path):
    # Load the Excel file and sheet using pandas
    input_file_name = path
    downloads_folder = os.path.expanduser('~\\Downloads\\')
    excel_path = os.path.join(downloads_folder, input_file_name)
    file_name = os.path.basename(excel_path)
    print(file_name)
    df = pd.read_csv(excel_path)

    # code to get the count and compare with its threshold
    thresholds = {
        'AcctNotationsSubProcess': 10,
        'AuthorizePaymentSubProcess': 10,
        'AutoPayCustomerNotificationProcess': 300,
        'BatchPaymentProcess': 10,
        'BMNotificationProcess': 25,
        'CardVoidSubProcess': 5,
        'CRISAutoPayEnrollmentProcess': 5,
        'CustomerNotificationSubProcess': 5,
        'DocsFalloutSubProcess': 100,
        'EPWFEmailNotificationProcess': 30,
        'FTSOrderConstructionProcess': 5,
        'InitiateMultiPaymentSessionService': 20,
        'InitiatePaymentSessionService': 100,
        'MailNotificationPSMCreation Process': 5,
        'NachaComplianceProcess': 5,
        'NotesAndNotificationsSubProcess': 10,
        'NotesSubProcess': 300,
        'OrphanSessionCleanupSubProcess': 20,
        'PaymentProcessingSubProcess': 10,
        'PostingAllocationProcess': 5,
        'RefundPaymentService': 5,
        'SendPmtArrangementNotesSubProcess': 15,
        'TestAMWSConnectProcess': 5,
        'UpdateCIPSPaperLessBillingProcess': 100,
        'UpdateExternalSystemPaymentStatusProcess': 500,
        'UpdatePaymentSubService': 10,
        'WGProcess': 10
    }

    # Count the occurrences of each process name
    counts = df['WORK_NAME'].value_counts().to_dict()
    print(counts)
    # Compare with the threshold values
    for process, threshold in thresholds.items():
        count = counts.get(process, 0)
        if count > threshold:
            print(
                f"The process '{process}' has exceeded its threshold. Count: {count}, Threshold: {threshold} -----> Report")
        # else:
        #     print(f"The process '{process}' is within its baseline. Count: {count}, Threshold: {threshold}")

    #
    # # Remove duplicate rows based on column 1 and 2
    # initial_rows = len(df)
    # df.drop_duplicates(subset=['WORK_NAME', 'MASTER_REQUEST_ID'], inplace=True)
    # rows_removed = initial_rows - len(df)
    # print(f'{rows_removed} rows removed due to duplicates')
    #
    # # Remove rows based on filter on column 1
    # initial_rows = len(df)
    # df = df[df['WORK_NAME'] != 'HyperConverseNotificationSubProcess']
    # rows_removed = initial_rows - len(df)
    # print(f'{rows_removed} rows removed as they were - HyperConverseNotificationSubProcess')
    # initial_rows = len(df)
    # df = df[df['WORK_NAME'] != 'TreatmentSubProcess']
    # rows_removed = initial_rows - len(df)
    # print(f'{rows_removed} rows removed as they were -TreatmentSubProcess')
    # initial_rows = len(df)
    # df = df[df['WORK_NAME'] != 'CLOUNotificationSubProcess']
    # rows_removed = initial_rows - len(df)
    # print(f'{rows_removed} rows removed as they were - CLOUNotificationSubProcess')
    #

    # # Save the updated Excel file in a specific location
    # new_file_path = 'C:/Camel/input/' + file_name
    # df.to_excel(new_file_path, index=False, engine='openpyxl')
