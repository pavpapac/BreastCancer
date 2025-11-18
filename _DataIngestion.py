from pathlib import Path
from pydicom import dcmread
import numpy as np
import pandas as pd
import sqlite3

class DataIngestion:


    def __init__(self):
        self.database_exists = False
        self.data_path = Path.home() / Path('PycharmProjects/Apps/BreastCancer/Data/manifest-ZkhPvrLo5216730872708713142')
        self.metadata_path = Path.home() / Path(
            'PycharmProjects/Apps/BreastCancer/Data/manifest-ZkhPvrLo5216730872708713142/metadata.csv')
        self.mass_data_train_path = Path.home() / Path(
            'PycharmProjects/Apps/BreastCancer/Data/manifest-ZkhPvrLo5216730872708713142/mass_case_description_train_set.csv')

    def patient_data_to_df(self):
        """Reads csv files including pataient and metadata and converts them to a pandas dataframe"""
        self.mass_data_train_df = pd.read_csv(self.mass_data_train_path)
        self.metadata_df = pd.read_csv(self.metadata_path)
        
    def patient_data_df_with_dicom_paths(self):
        """Returns an updated version of the main patient table (mass_data_train.df) but with the Windows local file 
        paths included. Each row now has a direct link to the image and ROI mask dicom file."""

        self.patient_data_df = self.mass_data_train_df.copy()
        image_path_list = []
        mask_path_list = []

        for patient_num in range(self.mass_data_train_df.shape[0]):
            image_path, mask_path = self._path_to_dicoms(patient_num)
            image_path_list.append(str(image_path))
            mask_path_list.append(str(mask_path))

        self.patient_data_df["global image dicom path"] = image_path_list
        self.patient_data_df["global mask dicom path"] = mask_path_list

    def patient_data_sql(self):
        # --- 1. Choose the patient dataFrame to save to sql---
        df = self.patient_data_df

        print("--- This is our original DataFrame ---")
        print(df)
        print("\n")

        # --- 2. Define database and table names ---
        database_file_name = 'clinical_database.db'
        table_name = 'patients'

        # --- 3. Create a connection to the SQL database ---
        # This will create the file 'my_company_data.db' if it doesn't exist
        conn = sqlite3.connect(database_file_name)

        # --- 4. Write the DataFrame to the SQL database ---
        # This is the key command
        try:
            # 'name' is the name of the table we want to create
            # 'con' is the connection object
            # 'if_exists' tells pandas what to do if the table is already there
            #   'replace': Drop the old table and create a new one
            #   'append': Add data to the end of the existing table
            #   'fail': (Default) Do nothing and raise an error
            # 'index=False' means do not write the pandas index (0, 1, 2...) as a column

            df.to_sql(name=table_name, con=conn, if_exists='replace', index=False)

            print(f"Success! DataFrame was written to table '{table_name}' in '{database_file_name}'")

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            # --- 5. Close the connection ---
            # It's important to close the connection to save changes
            conn.close()

        # --- (Optional) How to verify it worked ---
        # You can test that the data is really in the database
        # by reading it back into a *new* DataFrame.

        print("\n--- Verifying: Reading data back from the DB ---")
        try:
            conn = sqlite3.connect(database_file_name)  # Re-open connection

            # Use pandas to read a SQL query
            df_from_db = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

            print(df_from_db)

        except Exception as e:
            print(f"Could not read from database: {e}")

        finally:
            conn.close()

    def _path_to_dicoms(self, patient_num):
        """

        :rtype: Windows path
        """
        image_folder_name = self.mass_data_train_df['image file path'][patient_num].split('/')[0]
        mask_folder_name = self.mass_data_train_df['ROI mask file path'][patient_num].split('/')[0]
        metadata_image_folder = self.metadata_df[self.metadata_df['Subject ID'] == image_folder_name]
        metadata_mask_folder = self.metadata_df[self.metadata_df['Subject ID'] == mask_folder_name]
        image_folder_path = metadata_image_folder['File Location'].values[0]
        mask_folder_path = metadata_mask_folder['File Location'].values[0]
        images_path = self.data_path / image_folder_path
        mask_path = self.data_path / mask_folder_path

        return images_path, mask_path



if __name__ == '__main__':

    DI = DataIngestion()
    print("Data Ingestion: initialise")
    print("Database exists: ", DI.database_exists)
    print("Reading patient breast mass data ", DI.patient_data_to_df())
    print("Image and mask folder names:", DI.patient_data_df_with_dicom_paths())
    DI.patient_data_sql()
    print("end")



