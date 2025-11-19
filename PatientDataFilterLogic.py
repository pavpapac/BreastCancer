import DatabaseHandler
import DicomHandler
from pathlib import Path
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional

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
        """
        with DatabaseHandler.DatabaseHandler(self.db_path) as dbh:
            patient_df = dbh.get_rows_by_patient_id(patient_id)
            side_filtered_df = dbh.filter_by_breast_side(patient_df, breast_side)
            final_filtered_df = dbh.filter_by_image_view(side_filtered_df, image_view)
        return final_filtered_df

    def get_all_patient_ids(self) -> List[str]:
        """Fetches a list of all unique patient IDs."""
        try:
            with DatabaseHandler.DatabaseHandler(self.db_path) as dbh:
                return dbh.get_distinct_values('patient_id')
        except Exception as e:
            print(f"Error fetching patient IDs: {e}")
            return []

    def get_dependent_options(self, patient_id: str, breast_side: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Gets the available filter options based on prior selections.
        """
        options = {'breast_sides': [], 'image_views': []}
        if not patient_id:
            return options
        
        try:
            with DatabaseHandler.DatabaseHandler(self.db_path) as dbh:
                patient_df = dbh.get_rows_by_patient_id(patient_id)
                if patient_df.empty:
                    return options

                if breast_side:
                    side_df = dbh.filter_by_breast_side(patient_df, breast_side)
                    options['breast_sides'] = patient_df['left or right breast'].unique().tolist()
                    options['image_views'] = side_df['image view'].unique().tolist()
                else:
                    options['breast_sides'] = patient_df['left or right breast'].unique().tolist()
                    options['image_views'] = patient_df['image view'].unique().tolist()
            
            return options
        except Exception as e:
            print(f"Error fetching dependent options: {e}")
            return options

    def get_patient_filtered_data(self, patient_id: str, breast_side: str, image_view: str) -> pd.DataFrame:
        """
        Gets filtered clinical data, removes redundant columns, and returns it for presentation.
        """
        final_filtered_df = self._get_full_filtered_data(patient_id, breast_side, image_view)
        columns_to_drop = [
            'patient_id', 'left or right breast', 'image view',
            'image file path', 'cropped image file path', 'ROI mask file path',
            'global image dicom path', 'global mask dicom path'
        ]
        return final_filtered_df.drop(columns=columns_to_drop, errors='ignore')

    def get_patient_dicom_path(self, patient_id: str, breast_side: str, image_view: str) -> Path:
        """
        Retrieves the DICOM path by re-filtering the data internally.
        """
        final_filtered_df = self._get_full_filtered_data(patient_id, breast_side, image_view)
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

if __name__ == '__main__':
    pdfl = PatientDataFilterLogic("clinical_database.db")
    
    def check_distinct(column_name):
        try:
            with DatabaseHandler.DatabaseHandler(pdfl.db_path) as dbh:
                values = dbh.get_distinct_values(column_name)
                # Sort numeric values correctly
                try:
                    sorted_values = sorted(values, key=int)
                except ValueError:
                    sorted_values = sorted(values)
                print(f"Unique values for '{column_name}': {sorted_values}")
        except Exception as e:
            print(f"Error checking '{column_name}': {e}")

    print("--- Investigating Unique Values for Tooltips ---")
    check_distinct('pathology')
    check_distinct('breast_density')
    check_distinct('mass shape')
    check_distinct('mass margins')
    check_distinct('subtlety')
    print("--- Investigation Complete ---")
