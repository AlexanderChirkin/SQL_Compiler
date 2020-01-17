import xlrd
from table import Table


def get_tables_from_excel(path: str):
    tables = []
    rb = xlrd.open_workbook(path, formatting_info=True)
    for sheet in rb.sheets():
        table = []
        for rownum in range(sheet.nrows):
            row = sheet.row_values(rownum)
            table.append(row)
        tables.append(Table(sheet.name, table))
    return tables


if __name__ == '__main__':
    for t in get_tables_from_excel('D:/tables/xl.xls'):
        print(t)
