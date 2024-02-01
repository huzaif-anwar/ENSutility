import os
import subprocess
from datetime import datetime

import PrepareUpdateQueries
from GenerateEPWFFalloutReport import generateExcelFileforFalloutReport
import GenerateHTMLfile
from ModifyMDWExcel import checkForMDWFallout

# print start time
starttime = datetime.now()
print("Start time: ", starttime)
generateExcelFileforFalloutReport()
PrepareUpdateQueries.generate_update_queries(
    "QWPROD_REPORT_20240201_030000_lxomavmpceap67217067252832391706725282926.xlsx")
checkForMDWFallout("QWPROD_EPWF_MDW_FALLOUT_20240131040000_To_20240201040000_202402010540.csv")
# print end time
print("End time: ", datetime.now())
# print total time taken
print("Total time taken: ", starttime - datetime.now())
# Path to the Python interpreter in your virtual environment
python_path = "C:/Users/ac65760/PycharmProjects/ProdSupport_scripts/venv/Scripts/python.exe"

# Run GenerateHTMLFile.py
process = subprocess.Popen([python_path, "GenerateHTMLfile.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

# Print the output from the Flask application in real-time
for line in iter(process.stdout.readline, b''):
    print(line.decode().strip())
