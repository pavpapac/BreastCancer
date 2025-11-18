import sqlite3
import pandas as pd
from typing import List

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
        
        actual_columns = self.get_column_names()
        if column_name not in actual_columns:
            raise ValueError(f"Invalid column name: '{column_name}' does not exist in the table.")

        cursor = self.connection.cursor()
        cursor.execute(f'SELECT DISTINCT "{column_name}" FROM patients WHERE "{column_name}" IS NOT NULL ORDER BY "{column_name}"')
        return [row[0] for row in cursor.fetchall()]

    def get_rows_by_patient_id(self, patient_id: str) -> pd.DataFrame:
        """Fetches all rows for a given patient_id and returns them as a DataFrame."""
        if not self.connection:
            raise ConnectionError("Database connection is not open.")
        
        query = "SELECT * FROM patients WHERE patient_id = ?"
        df = pd.read_sql_query(query, self.connection, params=(patient_id,))
        return df

    def filter_by_breast_side(self, df: pd.DataFrame, side: str) -> pd.DataFrame:
        """Filters a DataFrame based on the 'left or right breast' column."""
        if df.empty or 'left or right breast' not in df.columns:
            return pd.DataFrame()
        
        side_upper = side.upper()
        return df[df['left or right breast'].str.upper() == side_upper].copy()

    def filter_by_image_view(self, df: pd.DataFrame, image_view: str) -> pd.DataFrame:
        """Filters a DataFrame based on the 'image view' column."""
        if df.empty or 'image view' not in df.columns:
            return pd.DataFrame()
            
        image_view_upper = image_view.upper()
        return df[df['image view'].str.upper() == image_view_upper].copy()

    def get_dicom_paths(self, df: pd.DataFrame) -> List[str]:
        """Extracts the 'global image dicom path' from a DataFrame."""
        if df.empty or 'global image dicom path' not in df.columns:
            return []
        
        return df['global image dicom path'].tolist()
