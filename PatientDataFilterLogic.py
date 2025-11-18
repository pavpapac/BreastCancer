import DatabaseHandler
import DicomHandler
from pathlib import Path
from typing import Dict, List, Any

class PatientDataFilterLogic:
    """
    This class acts as the business logic layer, translating user requests
    into data retrieval and processing operations.
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

    def get_column_names(self) -> List[str]:
        """Pass-through method to get column names for the UI."""
        try:
            with DatabaseHandler.DatabaseHandler(self.db_path) as dbh:
                return dbh.get_column_names()
        except Exception as e:
            print(f"Error fetching column names: {e}")
            return []

    def get_patient_filtered_data(self, patient_id: str, breast_side: str, image_view: str) -> List[Any]:
        """Gets filtered clinical data rows based on user selections."""
        with DatabaseHandler.DatabaseHandler(self.db_path) as dbh:
            patient_all_rows = dbh.get_rows_by_patient_id(patient_id)
            patient_breast_side_filtered = dbh.filter_by_breast_side(patient_all_rows, breast_side)
            patient_final_filtered = dbh.filter_by_image_view(patient_breast_side_filtered, image_view)
        return patient_final_filtered

    def get_patient_dicom_path(self, patient_filtered_rows: List[Any]) -> Path:
        """Extracts the DICOM path from the filtered data rows."""
        if not patient_filtered_rows:
            raise ValueError("Cannot get DICOM path from empty data.")
        
        with DatabaseHandler.DatabaseHandler(self.db_path) as dbh:
            dicom_paths = dbh.get_dicom_paths(patient_filtered_rows)
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
