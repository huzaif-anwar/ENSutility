import os
import sys

from bs4 import BeautifulSoup

from flask import Flask, render_template
import pandas as pd
import numpy as np

from utility.EmailModule import send_email
from utility.PDFToDOCX import pdf_to_docx, docx_to_html

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
        html_table = '<table style="border-collapse: collapse; table-layout: auto; width: auto;">'

        # Add the headers to the table
        html_table += '<tr style="background-color: #000000;">'
        for column in df.columns:
            html_table += f'<th style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border: 1px solid #FFFFFF; padding: 4px; font-size: 14px; color: #FFFFFF; text-align: center;">{column}</th>'
        html_table += '</tr>'

        # Add the data to the table
        for i, row in enumerate(df.itertuples(index=False)):
            if i % 2 == 0:
                row_color = '#9F9F9F'  # even row
            else:
                row_color = '#D2D2D2'  # odd row
            html_table += f'<tr style="background-color: {row_color};">'
            for cell in row:
                if np.issubdtype(type(cell), np.number):
                    html_table += f'<td class="number" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border: 1px solid #FFFFFF; padding: 4px; font-size: 14px; text-align: right;">{cell}</td>'
                else:
                    html_table += f'<td class="string" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border: 1px solid #FFFFFF; padding: 4px; font-size: 14px; text-align: left;">{cell}</td>'
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

    # Add content of EPWF Fallout Report pdf to the HTML page
    # Read the PDF file name from the temporary file
    with open('pdf_file.tmp', 'r') as f:
        pdf_file = f.read().strip()
    # Define the downloads folder
    downloads_folder = os.path.expanduser('~\\Downloads\\')
    # Define the full path to the PDF file
    pdf_file_path = os.path.join(downloads_folder, pdf_file)

    # Convert the PDF to DOCX
    docx_path = pdf_to_docx(pdf_file_path)

    # Convert the DOCX to HTML
    html_content = docx_to_html(docx_path)

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the first <p> tag and add the 'main-heading' class to it
    main_heading = soup.find('p')
    main_heading['class'] = 'main-heading'
    main_heading[
        'style'] = "text-align: center; margin-top: 20px; margin-bottom: 20px; font-weight: bold; font-family: Arial, sans-serif; font-size: 30px;"

    # Find the next <p> tags before the table and add the 'secondary-heading' class to them
    for p in soup.find_all('p')[1:]:
        if p.find_next_sibling('table'):
            p['class'] = 'secondary-heading'
            p[
                'style'] = "text-align: center; margin-top: 20px; margin-bottom: 20px; font-weight: bold; font-family: Arial, sans-serif; font-size: 15px;"

    # Apply styles to the table elements
    for table in soup.find_all('table'):
        table['style'] = "margin-left: auto; margin-right: auto; border-collapse: collapse;"
    for td in soup.find_all(['td', 'th']):
        td['style'] = "border: 1px solid black; background-color: white; text-align: center; width: 800px;"

    # Convert the BeautifulSoup object back to a string
    pdf_html = str(soup)

    # Wrap the HTML content in a div
    pdf_html = f'<div class="pdf-content" style="text-align: center;">{pdf_html}</div>'


    # Render the HTML page
    full_page = render_template('falloutReport.html', potential_fallouts=potential_fallouts, specific_sheets=specific_sheets, specific_sheets_S=specific_sheets_S, blocked_jobs=blocked_jobs, pdf_html=pdf_html)
    send_email(full_page)
    return full_page

def send_emails_on_start():
    with app.app_context():
        generateHTMLReport()
        sys.exit()  # Terminate the script

if __name__ == '__main__':
    send_emails_on_start()
    app.run(debug=True)