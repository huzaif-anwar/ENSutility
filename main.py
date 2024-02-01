# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import pandas as pd

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.

def refactor_MDW_fallout_excel_file(excel_path):

    # Load the Excel file and sheet using pandas
    df = pd.read_excel(excel_path)

    # Remove duplicate rows based on column 1 and 2
    df.drop_duplicates(subset=['column1', 'column2'], inplace=True)

    # Remove rows based on filter on column 1
    df = df[df['column1'] != 'value1']
    df = df[df['column1'] != 'value2']
    df = df[df['column1'] != 'value3']

    # Save the updated Excel file in a specific location
    df.to_excel('path/to/new/excel/file.xlsx', index=False)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    refactor_MDW_fallout_excel_file('')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
