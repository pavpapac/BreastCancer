from pathlib import Path
from pydicom import dcmread
import numpy as np
import pandas as pd
import sqlite3
import os


class DataIngestion:
    """
    Handles file path setup, reading CSV metadata, linking DICOM paths,
    and ingesting the combined data into an SQLite database.
    """

    def __init__(self):
         # 📝 Path Configuration: Use raw string for paths or better, a configuration file.
        base_dir = Path.home() / 'PycharmProjects/Apps/BreastCancer/Data/manifest-ZkhPvrLo5216730872708713142'
        self.data_path = base_dir
        self.metadata_path = base_dir / 'metadata.csv'
        self.mass_data_train_path = base_dir / 'mass_case_description_train_set.csv'

        # 📝 Improvement: Check if the base directory exists upon initialization
        if not self.data_path.is_dir():
            print(f"Warning: Base data directory not found at {self.data_path}")
            # Optionally, raise an exception here to stop execution if data is mandatory

    def patient_data_to_df(self):
        """Reads csv files including patient and metadata and converts them to a pandas dataframe"""

        # 📝 Improvement: Basic error handling for file reading
        try:
            self.mass_data_train_df = pd.read_csv(self.mass_data_train_path)
            self.metadata_df = pd.read_csv(self.metadata_path)
            print("Metadata CSV files loaded successfully.")
        except FileNotFoundError as e:
            print(f"Error: One or more CSV files not found. Check paths. Error: {e}")
        except Exception as e:
            print(f"Error reading CSV files: {e}")

    def _get_full_dicom_path(self, row):
        """
        Helper method to generate the full DICOM paths for a single row.
        Designed to be used with DataFrame.apply().
        """
        # Extract folder names from the relative paths
        image_folder_name = row['image file path'].split('/')[0]
        mask_folder_name = row['ROI mask file path'].split('/')[0]

        # 📝 Improvement: Use .loc for clean, conditional filtering
        metadata_image_folder = self.metadata_df.loc[self.metadata_df['Subject ID'] == image_folder_name]
        metadata_mask_folder = self.metadata_df.loc[self.metadata_df['Subject ID'] == mask_folder_name]

        # Safely get the file location path (assuming only one match)
        image_folder_path = metadata_image_folder['File Location'].iloc[0]
        mask_folder_path = metadata_mask_folder['File Location'].iloc[0]

        # Construct the final Path objects
        images_path = self.data_path / image_folder_path
        mask_path = self.data_path / mask_folder_path

        return str(images_path), str(mask_path)

    def patient_data_df_with_dicom_paths(self):
        """
        Returns an updated version of the main patient table with the Windows local file
        paths included, generated using the efficient .apply() method.
        """
        # 📝 Improvement: Ensure mass_data_train_df exists before copying
        if not hasattr(self, 'mass_data_train_df'):
            print("Error: mass_data_train_df not loaded. Run patient_data_to_df() first.")
            return

        self.patient_data_df = self.mass_data_train_df.copy()

        print("Linking DICOM file paths (using efficient .apply())...")

        # 📝 Key Efficiency Improvement: Use .apply() with a lambda function
        # to process rows and assign new columns efficiently.
        paths = self.patient_data_df.apply(
            self._get_full_dicom_path,
            axis=1,  # Apply function row-wise
            result_type='expand'  # Expands the returned tuple into new columns
        )

        self.patient_data_df["global image dicom path"] = paths[0]
        self.patient_data_df["global mask dicom path"] = paths[1]

        print("DICOM paths successfully added to DataFrame.")

    def patient_data_sql(self):
        """
        Writes the processed patient data DataFrame to an SQLite database file
        using a context manager for safe connection handling.
        """
        # 📝 Pre-check: Ensure the necessary DataFrame is ready
        if not hasattr(self, 'patient_data_df'):
            print("Error: 'patient_data_df' not found. Run 'patient_data_df_with_dicom_paths()' first.")
            return

        df = self.patient_data_df

        print("--- DataFrame to be written to SQL ---")
        print(f"Shape: {df.shape}")
        print(df.head(2))
        print("\n")

        # --- 1. Define database and table names ---
        database_file_name = 'clinical_database.db'
        table_name = 'patients'

        # --- 2. Write the DataFrame to the SQL database using a Context Manager ---
        try:
            # 📝 Key Improvement: Use 'with' statement. Guarantees conn.close()
            with sqlite3.connect(database_file_name) as conn:

                print(f"Attempting to write data to database: '{database_file_name}'...")

                # 📝 Core Logic: Write DataFrame to SQL table
                df.to_sql(
                    name=table_name,
                    con=conn,
                    if_exists='replace',  # 📝 Action: Replace the table if it exists
                    index=False  # 📝 Best Practice: Do not write the pandas index as a column
                )

                self.database_exists = True
                print(f"Success! DataFrame was written to table '{table_name}'.")

        except Exception as e:
            print(f"❌ An error occurred during database write: {e}")
            self.database_exists = False

        # --- 3. (Optional) Verification Step ---
        print("\n--- Verifying: Reading data back from the DB ---")
        if self.database_exists:
            try:
                # 📝 Use context manager for reading back as well
                with sqlite3.connect(database_file_name) as conn:

                    # 📝 Efficiency: Use LIMIT 5 to quickly verify data presence without loading the whole table
                    df_from_db = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)

                    print(f"Successfully read back 5 rows from table '{table_name}':")
                    print(df_from_db)

            except Exception as e:
                print(f"❌ Could not read from database for verification: {e}")
        else:
            print("Verification skipped because database write failed.")

if __name__ == '__main__':
    DI = DataIngestion()
    print("Data Ingestion: initialisation completed")
    print("Reading patient breast mass data ", DI.patient_data_to_df())
    print("Image and mask folder names:", DI.patient_data_df_with_dicom_paths())
    print("Image and mask folder names:", DI.patient_data_sql())