
# data_utils.py
import pandas as pd
from PyQt5.QtWidgets import QTableWidgetItem
from typing import List

def load_csv_to_table(csv_path: str, table_widget):
    """
    Loads CSV into QTableWidget. Also updates header labels.
    Returns list of rows (list of lists).
    """
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print("Error loading CSV:", e)
        return []

    table_widget.clearContents()
    table_widget.setRowCount(len(df))
    table_widget.setColumnCount(len(df.columns))
    table_widget.setHorizontalHeaderLabels([str(c) for c in df.columns.tolist()])

    for r, (_, row) in enumerate(df.iterrows()):
        for c, value in enumerate(row):
            item = QTableWidgetItem("" if pd.isna(value) else str(value))
            table_widget.setItem(r, c, item)
    table_widget.resizeColumnsToContents()
    return df.values.tolist()

def table_to_rows(table_widget) -> (List[List[str]], List[str]):
    """
    Convert current QTableWidget contents to rows (list of lists) and headers list.
    """
    rows = []
    headers = []
    col_count = table_widget.columnCount()
    row_count = table_widget.rowCount()
    for c in range(col_count):
        hdr = table_widget.horizontalHeaderItem(c)
        headers.append(hdr.text() if hdr else f"Column {c+1}")
    for r in range(row_count):
        row = []
        for c in range(col_count):
            item = table_widget.item(r, c)
            row.append(item.text() if item else "")
        rows.append(row)
    return rows, headers

def rows_to_table(rows, headers, table_widget):
    table_widget.clearContents()
    table_widget.setRowCount(len(rows))
    table_widget.setColumnCount(len(headers))
    table_widget.setHorizontalHeaderLabels(headers)
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            table_widget.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))
    table_widget.resizeColumnsToContents()
