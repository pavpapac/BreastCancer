import DatabaseHandler
import DicomHandler
from pathlib import Path
import pandas as pd
from typing import Dict, List

class PatientDataFilterLogic:
    """
    This class acts as the business logic layer, translating user requests
    into data retrieval and processing operations using DataFrames.
    """

    def __init__(self, clinical_database_path: str):
        self.db_path = clinical_database_path

    def get_ui_selection_options(self) -> Dict[str, List[str]]:
        """
        Fetches all distinct values needed to populate the UI selection widgets.
        """
        options = {}
        try:
            with DatabaseHandler.DatabaseHandler(self.db_path) as dbh:
                options['patient_ids'] = dbh.get_distinct_values('patient_id')
                options['breast_sides'] = dbh.get_distinct_values('left or right breast')
                options['image_views'] = dbh.get_distinct_values('image view')
            return options
        except Exception as e:
            print(f"Error fetching UI options: {e}")
            return {'patient_ids': [], 'breast_sides': [], 'image_views': []}

    def get_patient_filtered_data(self, patient_id: str, breast_side: str, image_view: str) -> pd.DataFrame:
        """
        Gets filtered clinical data as a DataFrame based on user selections.
        """
        with DatabaseHandler.DatabaseHandler(self.db_path) as dbh:
            patient_df = dbh.get_rows_by_patient_id(patient_id)
            side_filtered_df = dbh.filter_by_breast_side(patient_df, breast_side)
            final_filtered_df = dbh.filter_by_image_view(side_filtered_df, image_view)
        return final_filtered_df

    def get_patient_dicom_path(self, filtered_df: pd.DataFrame) -> Path:
        """Extracts the first DICOM path from the filtered DataFrame."""
        if filtered_df.empty:
            raise ValueError("Cannot get DICOM path from empty data.")
        
        with DatabaseHandler.DatabaseHandler(self.db_path) as dbh:
            dicom_paths = dbh.get_dicom_paths(filtered_df)
            if not dicom_paths:
                raise FileNotFoundError("No DICOM path found in the provided data.")
            return Path(dicom_paths[0])

    def get_patient_image_data(self, dcm_path: Path):
        """Retrieves the pixel array and metadata from a DICOM file path."""
        dcmh = DicomHandler.DicomHandler(dcm_path)
        if dcmh.dataset is None:
            raise FileNotFoundError(f"Failed to load DICOM data from {dcm_path}")
        
        pixel_array = dcmh.get_pixel_array()
        image_metadata = dcmh.get_metadata()
        return pixel_array, image_metadata
