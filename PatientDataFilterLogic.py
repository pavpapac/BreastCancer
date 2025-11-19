import DatabaseHandler
import DicomHandler
from pathlib import Path
import pandas as pd
from typing import Dict, List, Any, Tuple

class PatientDataFilterLogic:
    """
    This class acts as the business logic layer, translating user requests
    into data retrieval and processing operations using DataFrames.
    """

    def __init__(self, clinical_database_path: str):
        self.db_path = clinical_database_path

    def _get_full_filtered_data(self, patient_id: str, breast_side: str, image_view: str) -> pd.DataFrame:
        """
        Private helper method to get the complete filtered DataFrame.
        This centralizes the filtering logic to avoid code duplication.
        """
        with DatabaseHandler.DatabaseHandler(self.db_path) as dbh:
            patient_df = dbh.get_rows_by_patient_id(patient_id)
            side_filtered_df = dbh.filter_by_breast_side(patient_df, breast_side)
            final_filtered_df = dbh.filter_by_image_view(side_filtered_df, image_view)
        return final_filtered_df

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
        Gets filtered clinical data, removes redundant and file path columns, and returns it for presentation.
        """
        # Call the private helper to get the full data
        final_filtered_df = self._get_full_filtered_data(patient_id, breast_side, image_view)

        # Shape the data for presentation by dropping known columns
        columns_to_drop = [
            'patient_id', 'breast_density', 'left or right breast', 'image view',
            'image file path', 'cropped image file path', 'ROI mask file path',
            'global image dicom path', 'global mask dicom path'
        ]
        presentation_df = final_filtered_df.drop(columns=columns_to_drop, errors='ignore')
        
        return presentation_df

    def get_patient_dicom_path(self, patient_id: str, breast_side: str, image_view: str) -> Path:
        """
        Retrieves the DICOM path by calling the internal filtering logic.
        """
        # Call the private helper to get the full data
        final_filtered_df = self._get_full_filtered_data(patient_id, breast_side, image_view)

        # Extract the path from the full DataFrame
        with DatabaseHandler.DatabaseHandler(self.db_path) as dbh:
            dicom_paths = dbh.get_dicom_paths(final_filtered_df)
            if not dicom_paths:
                raise FileNotFoundError("No DICOM path found for the specified filters.")
            return Path(dicom_paths[0])

    def get_patient_image_data(self, dcm_path: Path) -> Tuple[Any, Dict]:
        """
        Retrieves the raw pixel array and metadata from a DICOM file path.
        """
        dcmh = DicomHandler.DicomHandler(dcm_path)
        if dcmh.dataset is None:
            raise FileNotFoundError(f"Failed to load DICOM data from {dcm_path}")
        
        pixel_array = dcmh.get_pixel_array()
        image_metadata = dcmh.get_metadata()
        
        return pixel_array, image_metadata
