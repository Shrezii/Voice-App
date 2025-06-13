import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "clinical_db.sqlite"

class ClinicalDBDriver:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_id TEXT,
                    patient_id TEXT,
                    transcript TEXT,
                    translated TEXT,
                    soap_summary TEXT,
                    created_at TEXT
                )
            """)
            conn.commit()

    def save(self, doctor_id, patient_id, transcript, translated, soap_summary):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO summaries (doctor_id, patient_id, transcript, translated, soap_summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (doctor_id, patient_id, transcript, translated, soap_summary, datetime.now().isoformat())
            )
            conn.commit()

def save_summary_to_db(summary, patient_id="unknown", doctor_id="unknown", transcript="", translated=""):
    driver = ClinicalDBDriver()
    driver.save(doctor_id, patient_id, transcript, translated, summary)
    print("✅ Summary saved to SQLite DB.")