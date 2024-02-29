import os
import subprocess
import sys
from datetime import date
from datetime import datetime

from utility import PrepareUpdateQueries
from utility.EmailModule import send_email_for_update_queries, send_cpe_email, send_mdw_report_email
from utility.GenerateEPWFFalloutReport import generateExcelFileforFalloutReport
from utility.ModifyMDWExcel import checkForMDWFallout


def generate_data_for_report():
    print("Please ensure the EPWF & MDW Fallout report and CBR Report are downloaded in the downloads folder.")

    # Get today's date
    today = date.today()

    # Check if the files exist
    downloads_folder = os.path.expanduser('~\\Downloads\\')
    # Get a list of all files in the downloads folder
    entries = list(os.scandir(downloads_folder))
    required_files = [entry for entry in entries if entry.name.startswith('QWPROD_')]

    # Initialize the file variables
    epwf_report_file = cbr_report_file = mdw_report_file = ''
    epwf_report_time = cbr_report_time = mdw_report_time = 0

    # Get the most recent files created today
    for entry in required_files:
        creation_date = datetime.fromtimestamp(entry.stat().st_ctime).date()
        if creation_date != today:
            continue

        if 'QWPROD_EPWF_FALLOUT' in entry.name and '.pdf' in entry.name and (
                not epwf_report_file or entry.stat().st_ctime > epwf_report_time):
            epwf_report_file = entry.name
            epwf_report_time = entry.stat().st_ctime
        elif 'QWPROD_REPORT' in entry.name and '.xlsx' in entry.name and (
                not cbr_report_file or entry.stat().st_ctime > cbr_report_time):
            cbr_report_file = entry.name
            cbr_report_time = entry.stat().st_ctime
        elif 'QWPROD_EPWF_MDW_FALLOUT' in entry.name and '.csv' in entry.name and (
                not mdw_report_file or entry.stat().st_ctime > mdw_report_time):
            mdw_report_file = entry.name
            mdw_report_time = entry.stat().st_ctime
    print(f"EPWF report file: {epwf_report_file}")
    print(f"CBR report file: {cbr_report_file}")
    print(f"MDW report file: {mdw_report_file}")

    # Check if the files exist in the downloads folder
    if not os.path.isfile(os.path.join(downloads_folder, epwf_report_file)):
        print(f"The EPWF Fallout Report file does not exist in the downloads folder. A copy of Report file will not be attached at the end of the report.")
    else:
        # Write the PDF file name to a temporary file
        with open('pdf_file.tmp', 'w') as f:
            f.write(epwf_report_file)
    print("Generating the report...")
    generateExcelFileforFalloutReport()
    if not os.path.isfile(os.path.join(downloads_folder, cbr_report_file)):
        print(f"The CBR Report file does not exist in the downloads folder.")
        print("Preparing the update queries without analyzing the CBR report...")
    else:
        print("Preparing the update queries and analyzing the CBR report...")
    PrepareUpdateQueries.generate_update_queries(cbr_report_file)
    send_email_for_update_queries()
    # Check if the CPE file is present and not empty
    if os.path.exists('/cpe_email_content.txt') and os.path.getsize('/cpe_email_content.txt') > 0:
        # Call the send_email method
        send_cpe_email('/cpe_email_content.txt')
    if not os.path.isfile(os.path.join(downloads_folder, mdw_report_file)):
        print(f"The MDW Fallout report file does not exist in the downloads folder.")
        return
    else:
        print("Checking for MDW Fallout...")
        checkForMDWFallout(mdw_report_file)
        send_mdw_report_email()


# print start time
starttime = datetime.now()
print("Start time: ", starttime)
generate_data_for_report()
# print end time
endtime = datetime.now()
print("End time: ", endtime)
# print total time taken in minutes
total_time = (endtime - starttime).total_seconds() / 60
print("Total time taken: ", total_time, "minutes")
# Path to the Python interpreter in your virtual environment
# python_path = "C:/Users/ac65760/PycharmProjects/ProdSupport_scripts/venv/Scripts/python.exe"
python_path = sys.executable
# Run GenerateHTMLFile.py
process = subprocess.Popen([python_path, "GenerateHTMLfile.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

# Print the output from the Flask application in real-time
for line in iter(process.stdout.readline, b''):
    print(line.decode().strip())
