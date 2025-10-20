# sort_manager.py
# Orchestrates: reading table rows, constructing multi-column key (with type parsing),
# calling sorting_algorithms.sort_rows, measuring time in ms, saving sorted CSV.

import time
import csv
from typing import List, Any, Tuple
import pandas as pd
from sorting_algorithms import sort_rows
from data_utils import table_to_rows, rows_to_table
from datetime import datetime

SortedResult = Tuple[List[List[Any]], int]  # (sorted_rows, time_ms)

# Helper to auto-parse a single value to int/float/date/string lowered
def auto_parse_value(v: Any):
    if v is None:
        return ""
    s = str(v).strip()
    if s == "":
        return ""
    # try int (no dot)
    try:
        if "." not in s:
            iv = int(s)
            return iv
    except Exception:
        pass
    # try float
    try:
        fv = float(s)
        return fv
    except Exception:
        pass
    # try parse date with pandas (very flexible)
    try:
        # use pandas to_datetime for many formats, fallback to string
        ts = pd.to_datetime(s, errors="coerce")
        if not pd.isna(ts):
            # return numeric timestamp for stable numeric comparisons
            return ts.timestamp()
    except Exception:
        pass
    # fallback string lower for lexicographic consistency
    return s.lower()

def build_key_fn(indices: List[int]):
    """
    Returns a key function that, given a row (list), returns a tuple of parsed values
    in the order of indices. For multi-column sorting, the earlier element in the tuple
    is the highest-priority key.
    """
    def key_fn(row):
        return tuple(auto_parse_value(row[i]) for i in indices)
    return key_fn

def apply_sort_from_tablewidget(table_widget, algo_name: str, selected_column_texts: List[str], headers: List[str], save_csv_path="sorted_tvmaze_shows.csv") -> SortedResult:
    """
    Reads rows from the provided QTableWidget (via table_to_rows),
    determines column indices from headers and selected_column_texts,
    sorts with chosen algorithm, writes CSV and returns (sorted_rows, time_ms).
    """
    rows, hdrs = table_to_rows(table_widget)
    if not rows:
        return [], 0

    # header list passed in should match table; build map
    header_map = {h: i for i, h in enumerate(headers)}
    # compute indices in the order desired by user:
    # user wants "first selected has highest priority". `selected_column_texts` is expected
    # to be ordered by the user preference. We'll trust the order passed in.
    indices = []
    for col_name in selected_column_texts:
        if col_name not in header_map:
            raise ValueError(f"Column '{col_name}' not found")
        indices.append(header_map[col_name])

    key = build_key_fn(indices)

    t0 = time.perf_counter()
    try:
        sorted_rows = sort_rows(rows, key, algo_name)
    except Exception:
        # fallback to Python sorted
        sorted_rows = sorted(rows, key=key)
    t1 = time.perf_counter()

    time_ms = int((t1 - t0) * 1000)

    # Save to CSV using pandas for robustness
    try:
        df = pd.DataFrame(sorted_rows, columns=headers)
        df.to_csv(save_csv_path, index=False, encoding="utf-8-sig")
    except Exception as e:
        # fallback manual CSV write
        try:
            with open(save_csv_path, "w", newline='', encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for r in sorted_rows:
                    writer.writerow(r)
        except Exception as e2:
            print("Warning: failed to save sorted CSV:", e2)

    # write back to the table widget
    rows_to_table(sorted_rows, headers, table_widget)

    return sorted_rows, time_ms
