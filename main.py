import sys
import os
import time
from datetime import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QThread, pyqtSignal
from gui import Ui_MainWindow
from scraper_thread import ScraperThread

try:
    from data_utils import load_csv_to_table, table_to_rows, rows_to_table
except ImportError:
    import csv

    def load_csv_to_table(csv_path, table_widget):
        if not os.path.exists(csv_path):
            return []
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            data = list(reader)
        table_widget.clearContents()
        table_widget.setColumnCount(len(headers))
        table_widget.setRowCount(len(data))
        table_widget.setHorizontalHeaderLabels(headers)
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                table_widget.setItem(r, c, QtWidgets.QTableWidgetItem(val))
        return data

    def table_to_rows(table_widget):
        rows, headers = [], []
        for c in range(table_widget.columnCount()):
            hdr_item = table_widget.horizontalHeaderItem(c)
            headers.append(hdr_item.text() if hdr_item else f"Column {c+1}")
        for r in range(table_widget.rowCount()):
            row = [table_widget.item(r, c).text() if table_widget.item(r, c) else "" for c in range(table_widget.columnCount())]
            rows.append(row)
        return rows, headers

    def rows_to_table(rows, headers, table_widget):
        table_widget.clearContents()
        table_widget.setColumnCount(len(headers))
        table_widget.setRowCount(len(rows))
        table_widget.setHorizontalHeaderLabels(headers)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                table_widget.setItem(r, c, QtWidgets.QTableWidgetItem("" if val is None else str(val)))


from sorting_algorithms import sort_rows


class SortingThread(QThread):
    finished_signal = pyqtSignal(list, int)
    error_signal = pyqtSignal(str)
    
    def __init__(self, rows, key_fn, algo_name):
        super().__init__()
        self.rows = rows
        self.key_fn = key_fn
        self.algo_name = algo_name
    
    def run(self):
        try:
            start = time.perf_counter()
            sorted_rows = sort_rows(self.rows, self.key_fn, self.algo_name)
            end = time.perf_counter()
            time_ms = int((end - start) * 1000)
            self.finished_signal.emit(sorted_rows, time_ms)
        except Exception as e:
            self.error_signal.emit(str(e))


class ScraperApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.scraper_thread = None
        self.sorting_thread = None
        self.csv_path = "tvmaze_shows_limited.csv"
        self.total_pages = 150
        self.sorted_folder = "sorted_results"
        self.all_data_rows = []
        self.pending_sort_data = None
        os.makedirs(self.sorted_folder, exist_ok=True)

        self.progressBar.setMaximum(self.total_pages)

        self.startButton.clicked.connect(self.start_scraping)
        self.pauseResumeButton.clicked.connect(self.pause_resume_scraping)
        self.stopButton.clicked.connect(self.stop_scraping)
        self.sortButton.clicked.connect(self.on_sort_clicked)

        self.addFilterButton.clicked.connect(self.add_filter)
        self.applyFilterButton.clicked.connect(self.apply_filters)
        self.clearFilterButton.clicked.connect(self.clear_filters)

        self._ensure_sort_algos()

        self.sortButton.setEnabled(False)
        self.sortTimeLabel.setText("⏱ Time: 0 ms")
        self.pauseResumeButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.progressBar.setValue(0)
        self.progressLabel.setText("Ready. Click ▶ Start to scrape fresh data.")

        self.active_filters = []

    def _ensure_sort_algos(self):
        wanted = ["Quick Sort", "Merge Sort", "Bubble Sort", "Heap Sort",
                  "Insertion Sort", "Selection Sort", "Counting Sort",
                  "Radix Sort", "Bucket Sort", "Tim Sort"]
        existing = [self.sortAlgoCombo.itemText(i) for i in range(self.sortAlgoCombo.count())]
        for w in wanted:
            if w not in existing:
                self.sortAlgoCombo.addItem(w)

    def start_scraping(self):
        self.scraper_thread = ScraperThread(output_file=self.csv_path, max_pages=self.total_pages)
        self.scraper_thread.progress.connect(self.update_progress)
        self.scraper_thread.finished.connect(self.scraping_finished)
        self.scraper_thread.status.connect(self.update_status)
        self.scraper_thread.start()

        self.startButton.setEnabled(False)
        self.pauseResumeButton.setEnabled(True)
        self.stopButton.setEnabled(True)
        self.progressLabel.setText("🟢 Scraping started...")

    def pause_resume_scraping(self):
        if not self.scraper_thread:
            return
        if self.pauseResumeButton.text().lower().startswith("⏸"):
            self.scraper_thread.pause()
            self.pauseResumeButton.setText("▶ Resume")
            self.progressLabel.setText("⏸ Paused")
        else:
            self.scraper_thread.resume()
            self.pauseResumeButton.setText("⏸ Pause")
            self.progressLabel.setText("▶ Resumed")

    def stop_scraping(self):
        if self.scraper_thread:
            self.scraper_thread.stop()
            self.progressLabel.setText("🛑 Stopping...")

    def update_progress(self, current_page):
        cur = int(current_page) if current_page else 0
        cur = max(0, min(cur, self.total_pages))
        self.progressBar.setValue(cur)
        percent = int((cur / self.total_pages) * 100) if self.total_pages else 0
        self.progressLabel.setText(f"Progress: {percent}% ({cur}/{self.total_pages} pages)")

    def update_status(self, message):
        print(message)
        self.progressLabel.setText(str(message))

    def scraping_finished(self, csv_path):
        current_progress = self.progressBar.value()
        self.progressLabel.setText("✅ Scraping finished. Loading data...")
        load_csv_to_table(csv_path, self.dataTable)
        self.all_data_rows, _ = table_to_rows(self.dataTable)
        self._populate_sort_columns_from_table()
        self._populate_search_columns()
        self.sortButton.setEnabled(True)
        self.startButton.setEnabled(True)
        self.pauseResumeButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        percent = int((current_progress / self.total_pages) * 100) if self.total_pages else 0
        self.progressLabel.setText(f"✅ Data loaded ({current_progress}/{self.total_pages} pages, {percent}%) — you can now sort or filter the table.")

    def _populate_sort_columns_from_table(self):
        self.sortColumnsList.clear()
        headers = [self.dataTable.horizontalHeaderItem(c).text() if self.dataTable.horizontalHeaderItem(c) else f"Column {c+1}"
                   for c in range(self.dataTable.columnCount())]
        self.sortColumnsList.addItems(headers)
        return headers

    def _populate_search_columns(self):
        self.searchColumnCombo.clear()
        headers = [self.dataTable.horizontalHeaderItem(c).text() if self.dataTable.horizontalHeaderItem(c) else f"Column {c+1}"
                   for c in range(self.dataTable.columnCount())]
        self.searchColumnCombo.addItems(headers)

    def on_sort_clicked(self):
        selected_items = self.sortColumnsList.selectedItems()
        if not selected_items:
            self.progressLabel.setText("⚠ Select at least one column to sort by.")
            return
        selected_column_names = [it.text() for it in selected_items]
        algo_name = self.sortAlgoCombo.currentText() or "Tim Sort"

        headers = [self.dataTable.horizontalHeaderItem(c).text() if self.dataTable.horizontalHeaderItem(c) else f"Column {c+1}" for c in range(self.dataTable.columnCount())]
        header_map = {h: i for i, h in enumerate(headers)}
        indices = [header_map[col] for col in selected_column_names if col in header_map]

        rows, _ = table_to_rows(self.dataTable)
        if not rows:
            self.progressLabel.setText("⚠ No rows present to sort.")
            return

        def key_fn(row):
            return tuple(auto_parse_value(row[i]) for i in indices)

        self.progressLabel.setText(f"🔃 Sorting by {', '.join(selected_column_names)} using {algo_name} ...")
        self.sortTimeLabel.setText("⏱ In Progress...")
        self.sortButton.setEnabled(False)
        QtCore.QCoreApplication.processEvents()

        self.pending_sort_data = {
            'algo_name': algo_name,
            'headers': headers,
            'selected_columns': selected_column_names
        }

        self.sorting_thread = SortingThread(rows, key_fn, algo_name)
        self.sorting_thread.finished_signal.connect(self.on_sorting_finished)
        self.sorting_thread.error_signal.connect(self.on_sorting_error)
        self.sorting_thread.start()

    def on_sorting_finished(self, sorted_rows, time_ms):
        if not self.pending_sort_data:
            return

        algo_name = self.pending_sort_data['algo_name']
        headers = self.pending_sort_data['headers']

        safe_algo = algo_name.strip().lower().replace(" ", "_")
        out_path = os.path.join(self.sorted_folder, f"sorted_tvmaze_shows_{safe_algo}.csv")

        try:
            import pandas as pd
            pd.DataFrame(sorted_rows, columns=headers).to_csv(out_path, index=False, encoding="utf-8-sig")
        except Exception:
            try:
                import csv
                with open(out_path, "w", newline='', encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(sorted_rows)
            except Exception as e:
                print("Failed to save sorted CSV:", e)

        rows_to_table(sorted_rows, headers, self.dataTable)
        self.sortTimeLabel.setText(f"⏱ Time: {time_ms} ms")
        self.progressLabel.setText(f"✅ Sorted saved to {out_path} ({time_ms} ms)")
        self.sortButton.setEnabled(True)
        self.pending_sort_data = None

    def on_sorting_error(self, error_msg):
        self.sortTimeLabel.setText("⏱ Error!")
        self.progressLabel.setText(f"❌ Sorting error: {error_msg}")
        self.sortButton.setEnabled(True)
        self.pending_sort_data = None

    def add_filter(self):
        column = self.searchColumnCombo.currentText()
        operator = self.operatorCombo.currentText()
        value = self.searchValueInput.text().strip()

        if not value:
            self.progressLabel.setText("⚠ Please enter a value for the filter.")
            return

        filter_text = f"{column} {operator} '{value}'"
        self.active_filters.append({
            'column': column,
            'operator': operator,
            'value': value
        })
        
        self.progressLabel.setText(f"✅ Filter added: {filter_text}")
        self.searchValueInput.clear()

    def apply_filters(self):
        if not self.active_filters:
            self.progressLabel.setText("⚠ No filters to apply. Add a filter first.")
            return

        headers = [self.dataTable.horizontalHeaderItem(c).text() if self.dataTable.horizontalHeaderItem(c) else f"Column {c+1}"
                   for c in range(self.dataTable.columnCount())]
        header_map = {h: i for i, h in enumerate(headers)}

        if not self.all_data_rows:
            self.all_data_rows, _ = table_to_rows(self.dataTable)

        filtered_rows = []
        logic_mode = "AND" if self.andRadio.isChecked() else "OR" if self.orRadio.isChecked() else "NOT"

        for row in self.all_data_rows:
            if logic_mode == "AND":
                if all(self._match_filter(row, f, header_map) for f in self.active_filters):
                    filtered_rows.append(row)
            elif logic_mode == "OR":
                if any(self._match_filter(row, f, header_map) for f in self.active_filters):
                    filtered_rows.append(row)
            elif logic_mode == "NOT":
                if not any(self._match_filter(row, f, header_map) for f in self.active_filters):
                    filtered_rows.append(row)

        rows_to_table(filtered_rows, headers, self.dataTable)
        self.progressLabel.setText(f"🔎 Filtered: {len(filtered_rows)} rows match ({logic_mode} logic)")

    def _match_filter(self, row, filter_dict, header_map):
        col_name = filter_dict['column']
        operator = filter_dict['operator']
        value = filter_dict['value'].lower()

        if col_name not in header_map:
            return False

        col_idx = header_map[col_name]
        if col_idx >= len(row):
            return False

        cell_value = str(row[col_idx]).lower()

        if operator == "Equals":
            return cell_value == value
        elif operator == "Contains":
            return value in cell_value
        elif operator == "Starts With":
            return cell_value.startswith(value)
        elif operator == "Ends With":
            return cell_value.endswith(value)
        elif operator == "Not Equals":
            return cell_value != value
        elif operator == "Greater Than":
            try:
                return float(cell_value) > float(value)
            except:
                return cell_value > value
        elif operator == "Less Than":
            try:
                return float(cell_value) < float(value)
            except:
                return cell_value < value
        return False

    def clear_filters(self):
        self.active_filters.clear()
        self.searchValueInput.clear()

        if self.all_data_rows:
            headers = [self.dataTable.horizontalHeaderItem(c).text() if self.dataTable.horizontalHeaderItem(c) else f"Column {c+1}"
                       for c in range(self.dataTable.columnCount())]
            rows_to_table(self.all_data_rows, headers, self.dataTable)
            self.progressLabel.setText("🔍 All filters cleared — showing all data.")
        else:
            load_csv_to_table(self.csv_path, self.dataTable)
            self.all_data_rows, _ = table_to_rows(self.dataTable)
            self.progressLabel.setText("🔍 Filters cleared — data reloaded.")


def auto_parse_value(v):
    if v is None:
        return ""
    s = str(v).strip()
    if not s:
        return ""
    try:
        if "." not in s:
            return int(s)
    except Exception:
        pass
    try:
        return float(s)
    except Exception:
        pass
    try:
        import pandas as pd
        ts = pd.to_datetime(s, errors="coerce")
        if not pd.isna(ts):
            return float(ts.timestamp())
    except Exception:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%Y.%m.%d", "%d.%m.%Y", "%b %d, %Y", "%B %d, %Y"):
            try:
                return float(datetime.strptime(s, fmt).timestamp())
            except Exception:
                pass
    return s.lower()

#main
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ScraperApp()
    window.show()
    sys.exit(app.exec_())