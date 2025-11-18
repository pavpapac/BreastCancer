import sqlite3
from typing import List, Tuple, Any

class DatabaseHandler:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None

    def __enter__(self):
        try:
            self.connection = sqlite3.connect(self.db_path)
            return self
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()

    def get_column_names(self) -> List[str]:
        """Fetches the column names from the 'patients' table."""
        if not self.connection:
            raise ConnectionError("Database connection is not open.")
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM patients LIMIT 0")
        return [description[0] for description in cursor.description]

    def get_distinct_values(self, column_name: str) -> List[str]:
        """Fetches unique, non-null values from a specified column."""
        if not self.connection:
            raise ConnectionError("Database connection is not open.")
        
        # Robust validation: Check if the column name actually exists in the table.
        actual_columns = self.get_column_names()
        if column_name not in actual_columns:
            raise ValueError(f"Invalid column name: '{column_name}' does not exist in the table.")

        cursor = self.connection.cursor()
        # Use quotes to safely handle column names that contain spaces.
        cursor.execute(f'SELECT DISTINCT "{column_name}" FROM patients WHERE "{column_name}" IS NOT NULL ORDER BY "{column_name}"')
        return [row[0] for row in cursor.fetchall()]

    def get_rows_by_patient_id(self, patient_id: str) -> List[Tuple[Any, ...]]:
        """Fetches all rows for a given patient_id from the 'patients' table."""
        if not self.connection:
            raise ConnectionError("Database connection is not open.")
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        return cursor.fetchall()

    def filter_by_breast_side(self, rows: List[Tuple[Any, ...]], side: str) -> List[Tuple[Any, ...]]:
        """Filters a list of rows based on the 'left or right breast' column."""
        # This relies on a fixed column index and is less robust.
        column_index = 2 
        side_upper = side.upper()
        return [row for row in rows if len(row) > column_index and row[column_index].upper() == side_upper]

    def filter_by_image_view(self, rows: List[Tuple[Any, ...]], image_view: str) -> List[Tuple[Any, ...]]:
        """Filters a list of rows based on the 'image view' column."""
        # This relies on a fixed column index and is less robust.
        column_index = 3
        image_view_upper = image_view.upper()
        return [row for row in rows if len(row) > column_index and row[column_index].upper() == image_view_upper]

    def get_dicom_paths(self, rows: List[Tuple[Any, ...]]) -> List[str]:
        """Extracts the 'global image dicom path' from a list of rows."""
        # This relies on a fixed column index and is less robust.
        column_index = 14
        return [row[column_index] for row in rows if len(row) > column_index]
