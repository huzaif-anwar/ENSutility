import subprocess
from datetime import datetime

from utility import PrepareUpdateQueries
from utility.GenerateEPWFFalloutReport import generateExcelFileforFalloutReport
from utility.ModifyMDWExcel import checkForMDWFallout


def generate_data_for_report():
    generateExcelFileforFalloutReport()
    PrepareUpdateQueries.generate_update_queries(
        "QWPROD_REPORT_20240202_030000_lxomavmpceap67317068114749301706811474476.xlsx")
    checkForMDWFallout("QWPROD_EPWF_MDW_FALLOUT_20240201040000_To_20240202040000_202402020540.csv")

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
python_path = "C:/Users/ac65760/PycharmProjects/ProdSupport_scripts/venv/Scripts/python.exe"

# Run GenerateHTMLFile.py
process = subprocess.Popen([python_path, "GenerateHTMLfile.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

# Print the output from the Flask application in real-time
for line in iter(process.stdout.readline, b''):
    print(line.decode().strip())
