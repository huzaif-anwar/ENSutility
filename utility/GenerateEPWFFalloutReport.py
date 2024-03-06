import os
import pandas as pd
import jpype
import jaydebeapi
import configparser


class CaseSensitiveConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr


def run_query_and_create_table(query, baseline, conn):
    curs = conn.cursor()
    curs.execute(query)
    rows = curs.fetchall()
    column_names = [desc[0] for desc in curs.description]
    df = pd.DataFrame(rows, columns=column_names)
    if df.iloc[:, 0].sum() > baseline:  # Compare the sum of the first column values with the baseline
        print("Total count - " + str(df.iloc[:, 0].sum()) + " - exceeding the Baseline -> Will be added in the report.")
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


def generateExcelFileforFalloutReport():
    # Check if the file exists
    if os.path.exists("../ProdSupport_scripts/output.xlsx"):
        # If it does, delete it
        os.remove("../ProdSupport_scripts/output.xlsx")

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter('../ProdSupport_scripts/output.xlsx', engine='xlsxwriter')
    conn = None
    try:
        conn = create_db_connection()

        # Load query and baseline config
        queryconfig = CaseSensitiveConfigParser()
        queryconfig.read('resources/ProdQueries.properties')

        # Define a dictionary with the query names and their corresponding baselines
        queries_and_baselines = {}
        for query_name in queryconfig.options('Fallout'):
            queries_and_baselines[query_name] = int(queryconfig.get('Baselines', query_name + '_baseline'))

        # Iterate over the dictionary and run each query
        for query_name, baseline in queries_and_baselines.items():
            print("Checking for " + query_name + " with Baseline of " + str(baseline) + ".")
            query = queryconfig.get('Fallout', query_name)
            df = run_query_and_create_table(query, baseline, conn)
            if df is not None:
                # Convert Java string objects to Python string objects
                df = df.astype(str)
                sheet_name = str(query_name)
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        # code to check for blocked jobs
        query = queryconfig.get('BlockedBatchJob', 'Blocked_Job')
        print("Checking for Blocked Jobs.")
        with conn.cursor() as curs:
            curs.execute(query)
            rows = curs.fetchall()
            column_names = [desc[0] for desc in curs.description]

        df = pd.DataFrame(rows, columns=column_names)
        if not df.empty:
            print("Blocked Jobs found. -> Will be added in the report.")
            # Select the first two columns
            df = df.iloc[:, :2]
            # Convert Java string objects to Python string objects
            df = df.astype(str)
            df.to_excel(writer, sheet_name='Blocked_Job', index=False)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the Pandas Excel writer and output the Excel file.
        writer.close()

        # Close the connection
        if conn is not None:
            conn.close()
