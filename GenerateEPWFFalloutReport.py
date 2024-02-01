import os
import pandas as pd
import jpype
import jaydebeapi
import configparser

import PrepareUpdateQueries


def run_query_and_create_table(query, baseline, conn):
    curs = conn.cursor()
    curs.execute(query)
    rows = curs.fetchall()
    column_names = [desc[0] for desc in curs.description]
    df = pd.DataFrame(rows, columns=column_names)
    if df.iloc[:, 0].sum() > baseline:  # Compare the sum of the first column values with the baseline
        print("Total count - " + str(df.iloc[:, 0].sum()))
        return df
    else:
        return None


def create_db_connection():
    # Load DB config
    config = configparser.ConfigParser()
    config.read('DB-config-prod.properties')

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


def generateExcelFileforFalloutReport():
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')
    conn=None
    try:
        conn = create_db_connection()

        queryconfig = configparser.ConfigParser()
        queryconfig.read('ProdQueries.properties')

        # Define a dictionary with the query names and their corresponding baselines
        queries_and_baselines = {
            'Capture_Requested': 0,
            'Posting_Pending': 40000,
            'Posting_Requested': 10000,
            'Settlement_Completed': 2000,
            'Settlement_Pending': 0,
            'Capture_Ready': 0,
            'XCASH': 0,
            'Pending_Correction': 0,
            'Denied': 1500,
            'Capture_Error': 2000,
            'Session_Error': 100,
            'Capture_Ready_suc': 90000,
            'Posted': 250000,
        }

        # Iterate over the dictionary and run each query
        for query_name, baseline in queries_and_baselines.items():
            print(query_name)
            print("Baseline - " + str(baseline))
            query = queryconfig.get('Fallout', query_name)
            print(query)
            df = run_query_and_create_table(query, baseline, conn)
            if df is not None:
                # Convert Java string objects to Python string objects
                df = df.astype(str)
                sheet_name = str(query_name)
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # Get the xlsxwriter workbook and worksheet objects in order to set the formatting.
                workbook = writer.book
                worksheet = writer.sheets[f'{query_name}']

                # Add a header format.
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#000000',  # Black background
                    'font_color': '#FFFFFF',  # White text
                    'border': 1})

                # Write the column headers with the defined format.
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, str(value), header_format)

                # Add a format. Light gray fill with a dark gray border.
                format1 = workbook.add_format({'bg_color': '#C0C0C0',
                                               'border': 1})

                # Add a format. Dark gray fill with a light gray border.
                format2 = workbook.add_format({'bg_color': '#808080',
                                               'border': 1})

                # Get the number of rows and columns in the DataFrame.
                num_rows = len(df.index)
                num_cols = len(df.columns)

                # Convert the number of columns to Excel column letter.
                col_letter = chr(ord('A') + num_cols - 1)

                # Apply the formats to alternate rows and used columns.
                worksheet.conditional_format(f'A2:{col_letter}{num_rows + 1}', {'type': 'formula',
                                                                                'criteria': '=MOD(ROW(),2)=0',
                                                                                'format': format1})
                worksheet.conditional_format(f'A2:{col_letter}{num_rows + 1}', {'type': 'formula',
                                                                                'criteria': '=MOD(ROW(),2)=1',
                                                                                'format': format2})

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the Pandas Excel writer and output the Excel file.
        writer.close()

        # Close the connection
        if conn is not None:
            conn.close()
