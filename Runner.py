import os
import subprocess
import sys
from datetime import datetime

from utility import PrepareUpdateQueries
from utility.EmailModule import send_email_for_update_queries, send_cpe_email
from utility.GenerateEPWFFalloutReport import generateExcelFileforFalloutReport
from utility.ModifyMDWExcel import checkForMDWFallout


def generate_data_for_report():
    print("Please ensure the EPWF & MDW Fallout report and CBR Report are downloaded in the downloads folder.")

    epwf_report_file = input("Enter the name of the EPWF report file: ").strip()
    cbr_report_file = input("Enter the name of the CBR report file: ").strip()
    mdw_report_file = input("Enter the name of the MDW fallout file: ").strip()

    # Check if the files exist
    downloads_folder = os.path.expanduser('~\\Downloads\\')

    # Check if the files exist in the downloads folder
    if not os.path.isfile(os.path.join(downloads_folder, epwf_report_file)):
        print(f"The file {epwf_report_file} does not exist in the downloads folder.")
        return
    else:
        print("Generating the report...")
        generateExcelFileforFalloutReport()
        # Write the PDF file name to a temporary file
        with open('pdf_file.tmp', 'w') as f:
            f.write(epwf_report_file)
    if not os.path.isfile(os.path.join(downloads_folder, cbr_report_file)):
        print(f"The file {cbr_report_file} does not exist in the downloads folder.")
        return
    else:
        print("Preparing the update queries...")
        PrepareUpdateQueries.generate_update_queries(cbr_report_file)
        send_email_for_update_queries()
    if not os.path.isfile(os.path.join(downloads_folder, mdw_report_file)):
        print(f"The file {mdw_report_file} does not exist in the downloads folder.")
        return
    else:
        print("Checking for MDW Fallout...")
        checkForMDWFallout(mdw_report_file)


# print start time
starttime = datetime.now()
print("Start time: ", starttime)

generate_data_for_report()
# Check if the file is present and not empty
if os.path.exists('cpe_email_content.txt') and os.path.getsize('cpe_email_content.txt') > 0:
    # Call the send_email method
    send_cpe_email('cpe_email_content.txt')

    # Delete the file
    os.remove('cpe_email_content.txt')
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
