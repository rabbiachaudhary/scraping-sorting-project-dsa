# scraper_thread.py
import requests
import pandas as pd
import time
from PyQt5.QtCore import QThread, pyqtSignal
import threading

class ScraperThread(QThread):
    progress = pyqtSignal(int)          # % progress
    finished = pyqtSignal(str)          # emit CSV path when done
    status = pyqtSignal(str)            # emit messages (e.g., "Fetching page 1...")
    
    def __init__(self, output_file="tvmaze_shows_limited.csv", delay=0.5, max_pages=150):
        super().__init__()
        self.output_file = output_file
        self.delay = delay
        self.max_pages = max_pages

        self._pause_event = threading.Event()
        self._pause_event.set()  # initially not paused
        self._stop_event = threading.Event()

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def stop(self):
        self._stop_event.set()
        self._pause_event.set()  # in case paused

    def run(self):
        base_url = "https://api.tvmaze.com/shows?page="
        all_data = []
        total_pages = self.max_pages

        for page in range(total_pages):
            if self._stop_event.is_set():
                self.status.emit("🛑 Stopped by user.")
                break

            self._pause_event.wait()  # wait here if paused

            url = f"{base_url}{page}"
            self.status.emit(f"📡 Fetching page {page}...")
            try:
                response = requests.get(url, timeout=15)
                if response.status_code != 200:
                    self.status.emit(f"⚠️ Error on page {page}: {response.status_code}")
                    break
                shows = response.json()
            except Exception as e:
                self.status.emit(f"⚠️ Network error on page {page}: {e}")
                break

            if not shows:
                self.status.emit("✅ No more data returned — stopping early.")
                break

            for show in shows:
                all_data.append({
                    "ID": show.get("id"),
                    "Name": show.get("name"),
                    "Language": show.get("language"),
                    "Genres": ", ".join(show.get("genres", [])),
                    "Premiered": show.get("premiered"),
                    "Status": show.get("status"),
                    "Runtime": show.get("runtime"),
                    "Official Site": show.get("officialSite"),
                    "Network": show.get("network", {}).get("name") if show.get("network") else None,
                    "Country": show.get("network", {}).get("country", {}).get("name") if show.get("network") else None
                })

            progress_percent = int(((page + 1) / total_pages) * 100)
            self.progress.emit(progress_percent)
            self.status.emit(f"✅ Page {page} done ({len(shows)} shows)")
            time.sleep(self.delay)

        # Save CSV
        df = pd.DataFrame(all_data)
        df.to_csv(self.output_file, index=False, encoding="utf-8-sig")
        self.status.emit(f"💾 Saved {len(df)} shows to {self.output_file}")
        self.finished.emit(self.output_file)
