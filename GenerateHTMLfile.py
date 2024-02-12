from flask import Flask, render_template
import pandas as pd
import numpy as np


app = Flask(__name__)


@app.route('/')
def generateHTMLReport():
    # GenerateEPWFFalloutReport.generateExcelFileforFalloutReport()
    # Read the Excel file
    xls = pd.ExcelFile('output.xlsx')

    # Get the sheet names
    sheet_names = xls.sheet_names

    # Create a list to hold the data for each sheet
    data = []
    potential_fallouts = []
    # Create a list to hold the names of the specific sheets for unsuccessful payments
    specific_sheets = []
    # Create a list to hold the names of the specific sheets for successful payments
    specific_sheets_S = []
    # Create a list to hold the Blocked_Job data
    blocked_jobs = []

    # Iterate over the sheet names
    for sheet_name in sheet_names:
        # Read the sheet into a DataFrame
        df = pd.read_excel(xls, sheet_name)

        # Get the total count as the sum of the first column
        total_count = df.iloc[:, 0].sum()

        # Generate the HTML table manually
        html_table = '<table>'

        # Add the headers to the table
        html_table += '<tr>'
        for column in df.columns:
            html_table += f'<th>{column}</th>'
        html_table += '</tr>'

        # Add the data to the table
        for row in df.itertuples(index=False):
            html_table += '<tr>'
            for cell in row:
                if np.issubdtype(type(cell), np.number):
                    html_table += f'<td class="number">{cell}</td>'
                else:
                    html_table += f'<td class="string">{cell}</td>'
            html_table += '</tr>'
        html_table += '</table>'

        # Add the sheet name, total count, and HTML table to the data list
        sheet_data = {'sheet_name': sheet_name, 'total_count': total_count, 'html_table': html_table}

        # Check if the sheet is the Blocked_Job sheet
        if 'Blocked_Job' in sheet_name:
            # If it is, add its data to the blocked_jobs list
            blocked_jobs.append({'sheet_name': sheet_name, 'total_count': total_count, 'html_table': html_table})

        # If the sheet is a potential fallout, add it to the potential fallouts list
        if 'Capture_Requested' in sheet_name:
            sheet_data[
                'heading'] = 'Capture_Requested for more than 12 hours : (@TeamPayTwo, please take care of these payments)'
            sheet_data['baseline'] = '0'
            potential_fallouts.append(sheet_data)
        if 'Capture_Ready' in sheet_name:
            sheet_data[
                'heading'] = 'Payments were not processed which are in Capture_Ready : (@TeamPayTwo, please take care of these payments)'
            sheet_data['baseline'] = '0'
            potential_fallouts.append(sheet_data)
        if 'Posting_Pending' in sheet_name:
            sheet_data[
                'heading'] = 'Posting_Pending for more than 15 days : (@TeamPayTwo, please take care of these payments)'
            sheet_data['baseline'] = '40000'
            potential_fallouts.append(sheet_data)
        if 'Posting_Requested' in sheet_name:
            sheet_data[
                'heading'] = 'Posting_Requested for more than 10 days : (@TeamPayTwo, please take care of these payments)'
            sheet_data['baseline'] = '10000'
            potential_fallouts.append(sheet_data)
        if 'Settlement_Completed' in sheet_name:
            sheet_data[
                'heading'] = 'Settlement_Completed more than 12 hours: (@TeamPayTwo, please take care of these payments)'
            sheet_data['baseline'] = '2000'
            potential_fallouts.append(sheet_data)
        if 'Settlement_Pending' in sheet_name:
            sheet_data[
                'heading'] = 'Settlement_Pending more than 5 days : (@TeamPayTwo, please take care of these payments)'
            sheet_data['baseline'] = '0'
            potential_fallouts.append(sheet_data)
        if 'XCASH' in sheet_name:
            sheet_data['heading'] = f'Posting_Requested XCASH Payments today’s count: {sheet_data["total_count"]}.'
            sheet_data['baseline'] = '0'
            potential_fallouts.append(sheet_data)
        if 'Pending_Correction' in sheet_name:
            sheet_data['heading'] = f'Payments in Pending_Correction today’s count is {sheet_data["total_count"]}.'
            sheet_data['baseline'] = '0'
            potential_fallouts.append(sheet_data)
##############################################################################################################
        # Define the specific sheet names
        specific_sheet_names = {'Denied': '1.5k', 'Capture_Error': '2k', 'Session_Error': '1k'}

        # Check if any of the specific sheet names are present
        if any(specific_sheet in sheet_names for specific_sheet in specific_sheet_names.keys()):
            # If a specific sheet is present, append a dictionary with its data to the list
            for specific_sheet, baseline in specific_sheet_names.items():
                if specific_sheet in sheet_name:
                    sheet_data = {'sheet_name': specific_sheet, 'total_count': total_count, 'html_table': html_table}
                    sheet_data[
                        'heading'] = f'Below {specific_sheet} payments are exceeding their baseline. (Baseline: {baseline}, Today’s Count : {sheet_data["total_count"]})'
                    specific_sheets.append(sheet_data)
        else:
            # If none of the specific sheets are present, append a one line string to the list
            specific_sheets.append('Unsuccessful Payments are within their baseline.')
#######################################################################################################################
        # Define the specific sheet names
        specific_sheet_names_S ={'Capture_Ready_suc': '90K', 'Posted': '250K'}

        # Check if any of the specific sheet names are present
        if any(specific_sheet_S in sheet_names for specific_sheet_S in specific_sheet_names_S.keys()):
            # If a specific sheet is present, append a dictionary with its data to the list
            for specific_sheet_S, baseline in specific_sheet_names_S.items():
                if specific_sheet_S in sheet_name:
                    sheet_data = {'sheet_name': specific_sheet_S, 'total_count': total_count, 'html_table': html_table}
                    sheet_data[
                        'heading'] = f'Below {specific_sheet_S} payments are exceeding their baseline. (Baseline: {baseline}, Today’s Count : {sheet_data["total_count"]})'
                    specific_sheets_S.append(sheet_data)
        else:
            # If none of the specific sheets are present, append a one line string to the list
            specific_sheets_S.append('Successful Payments are within their baseline.')

    if 'Blocked_Job' not in sheet_names:
        blocked_jobs.append('No batch job blocked today')


    # Render the HTML page
    return render_template('falloutReport.html', potential_fallouts=potential_fallouts, specific_sheets=specific_sheets, specific_sheets_S=specific_sheets_S, blocked_jobs=blocked_jobs)


if __name__ == '__main__':
    app.run(debug=True)